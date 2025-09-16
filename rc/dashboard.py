from datetime import datetime
from pathlib import Path
import dateparser
import json
import click
import subprocess
import os
import sys


class ClusterInfoException(Exception):
    """Custom exception for cluster information retrieval errors.

    Arguments
    ---------
    message : str
        Error message
    output : str, optional
        Additional output from the failed command
    """

    def __init__(self, message, output=None):
        if output:
            message = f"{message}\nOutput:\n{output}"
        super().__init__(message)


def get_queue():
    """Retrieves the current user's SLURM job queue.

    Arguments
    ---------
    None

    Returns
    -------
    jobs : list of dict
        List of jobs with job name, status, and time left

    Raises
    ------
    ClusterInfoException
        If the squeue command fails
    """
    try:
        user = os.getenv("USER")
        result = subprocess.run(
            ["squeue", "-u", user, "-o", "%j\t%T\t%L\t%V"],
            capture_output=True,
            text=True,
            check=True,
        )
        return parse_queue(result.stdout)
    except subprocess.CalledProcessError as e:
        raise ClusterInfoException(f"Error retrieving queue: {e}", output=e.stderr)


def parse_queue(output):
    """Parses the output of the squeue command.

    Arguments
    ---------
    output : str
        Raw output from squeue

    Returns
    -------
    jobs : list of dict
        List of parsed jobs with job name, status, and time left
    """
    lines = output.strip().split("\n")
    jobs = []
    for line in lines[1:]:  # Skip header
        if line.strip():  # Avoid empty lines
            parts = line.split("\t")
            if len(parts) == 4:
                job_name, status, time_left, time_started = parts
                time_started = datetime.fromisoformat(time_started)
                time_pending = (
                    datetime.now() - time_started
                    if status == "PENDING"
                    else None
                )
                jobs.append(
                    {
                        "job_name": job_name,
                        "status": status,
                        "time_left": time_left,
                        "time_started": time_started.isoformat(),
                        "time_pending": (
                            str(time_pending) if time_pending
                            else None
                        ),
                    }
                )
    return jobs


def get_recent(experiments_path, creation_cutoff, activity_cutoff, queue):
    experiment_paths = [
        path
        for path in experiments_path.glob("*")
        if path.is_dir()
        and datetime.fromtimestamp(path.stat().st_ctime) >= creation_cutoff
    ]
    experiments = [
        {
            "experiment_name": experiment_path.name,
            "time_activity": get_last_activity_time(experiment_path)
        }
        for experiment_path in experiment_paths
    ]
    queue_job_names = {
        job["job_name"] for job in queue
    }
    result = [
        format_dates(experiment)
        for experiment in experiments
        if experiment["time_activity"] > activity_cutoff
        and experiment["experiment_name"] not in queue_job_names
    ]
    return result


def get_last_activity_time(experiment_path):
    timestamps = [
        datetime.fromtimestamp(file_name.stat().st_mtime)
        for file_name in experiment_path.glob("output/*.txt")
    ]
    return (
        max(timestamps)
        if timestamps
        else datetime.fromtimestamp(experiment_path.stat().st_mtime)
    )


def format_dates(values):
    return {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in values.items()
    }



@click.command()
@click.option(
    "--experiments-path",
    help="The path to the experiments folder",
    default="~/experiments"
)
@click.option(
    "--recent-creation-cutoff",
    help="A date or a natural language string (e.g. '1 week') indicating"
    "the earliest date on which an experiment must be created "
    "to count as recent",
    default="1 week"
)
@click.option(
    "--recent-activity-cutoff",
    help="A date or a natural language string (e.g. '2 months') indicating"
    "the earliest date on which an experiment must have had activity"
    "to count as recent",
    default="1 day"
)
def main(
    experiments_path,
    recent_creation_cutoff,
    recent_activity_cutoff,
):
    """Main entry point for the dashboard script.

    Arguments
    ---------
    experiments_path : str
        The path to the experiments folder

    Returns
    -------
    None
    """
    queue = get_queue()
    experiments_path = Path(experiments_path).expanduser()
    recent_creation_cutoff_date = dateparser.parse(recent_creation_cutoff)
    recent_activity_cutoff_date = dateparser.parse(recent_activity_cutoff)
    if recent_creation_cutoff_date is None:
        raise click.ClickException(f"Unable to parse --recent-creation-cutoff {recent_creation_cutoff}")
    if recent_activity_cutoff_date is None:
        raise click.ClickException(f"Unable to parse --recent-creation-cutoff {recent_activity_cutoff}")
    recent = get_recent(
        experiments_path=experiments_path,
        creation_cutoff=recent_creation_cutoff_date,
        activity_cutoff=recent_activity_cutoff_date,
        queue=queue
    )
    dashboard = {"queue": queue, "recent": recent}
    json.dump(dashboard, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
