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
        """Initializes ClusterInfoException with error message and optional output.

        Arguments
        ---------
        message : str
            Error message
        output : str, optional
            Additional output from the failed command
        """
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
            ["squeue", "-u", user, "-o", "%j\t%T\t%L"],
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
            if len(parts) == 3:
                job_name, status, time_left = parts
                jobs.append(
                    {"job_name": job_name, "status": status, "time_left": time_left}
                )
    return jobs


@click.command()
def main():
    """Main entry point for the dashboard script.

    Arguments
    ---------
    None

    Returns
    -------
    None

    Side Effects
    ------------
    Prints the job queue as JSON to stdout
    """
    queue = get_queue()
    dashboard = {"queue": queue}
    json.dump(dashboard, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
