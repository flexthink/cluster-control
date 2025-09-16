from datetime import datetime
import json
import re
import subprocess
import humanize
import dateparser
from pathlib import Path

import click
import yaml
import sys


def read_config(file_name):
    """Reads the YAML configuration file.

    Arguments
    ---------
    file_name : str
        Path to the configuration YAML file

    Returns
    -------
    config : dict
        Parsed configuration as a dictionary
    """
    file_name = Path(file_name)
    if not file_name.is_absolute():
        file_name = Path(__file__).parent / file_name
    with open(file_name, "r") as f:
        return yaml.safe_load(f)


def get_dashboards(config):
    """Retrieves dashboards for all servers in the config.

    Arguments
    ---------
    config : dict
        Configuration dictionary with server info

    Returns
    -------
    dashboards : dict
        Dictionary of dashboards keyed by server name
    """
    dashboards = {
        key: get_dashboard(item) for key, item in config["servers"].items()
    }
    return dashboards


def get_dashboard(config):
    """Retrieves the dashboard data from a remote host.

    Arguments
    ---------
    config : dict
        A dictionary with server info

    Returns
    -------
    dashboard : dict
        Dashboard data parsed from JSON output
    """
    try:
        venv = config.get("venv")
        if venv:
            python = str(Path(venv) / "bin" / "python")
        else:
            python = "python"
        result = subprocess.run(
            ["ssh", config["host"], python, "rc/dashboard.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"queue": [], "error": f"Command failed: {e}", "output": e.stderr}
    except json.JSONDecodeError as e:
        return {"queue": [], "error": f"Failed to parse JSON: {e}"}


def run_connect(config):
    """Attempts to connect to all servers in the config.

    Arguments
    ---------
    config : dict
        Configuration dictionary with server info

    Returns
    -------
    None
        Prints connection status to stdout
    """
    for key, item in config["servers"].items():
        click.echo(f"{click.style('Connecting: ', fg='yellow')} {key}")
        try:
            subprocess.run(["ssh", item["host"], "/bin/true"], text=True)
        except subprocess.CalledProcessError as e:
            click.echo(f"{click.style('Error:', color='red')} {e}")


def output_dashboards(config, dashboards):
    """Outputs the dashboards in SwiftBar format.

    Arguments
    ---------
    config : dict
        Configuration dictionary with server info
    dashboards : dict
        Dashboard data for each server

    Returns
    -------
    None
        Prints formatted dashboard to stdout
    """
    print(":computer: Cluster | emojize=True symbolize=False")
    for key, item in config["servers"].items():
        dashboard = dashboards.get(key, {"queue": [], "error": "No data"})
        queue = dashboard["queue"]
        print("---")
        print(f"**{item['label']}** | color='blue' md=true")
        print("---")
        if not queue and not dashboard.get("error"):
            print("Empty")
        if dashboard.get("error"):
            print(f"Error: {dashboard['error']} | color=red")
        for job in queue:
            label = format_job_label(job)
            print(
                f"{label} "
                f"| emojize=True symbolize=False color='yellow' bash='ssh' "
                f"param0='{item['host']}' param1=\"'~/rc/tail-log.sh'\" "
                f"param2='{job['job_name']}' terminal=true"
            )
        print("---")
        recent = dashboard.get("recent", [])
        for experiment in recent:
            label = format_experiment_label(experiment)
            print(
                f"{label} "
                f"| emojize=True symbolize=False color='yellow' bash='ssh' "
                f"param0='{item['host']}' param1=\"'~/rc/tail-log.sh'\" "
                f"param2='{experiment['experiment_name']}' terminal=true"
            )
            
        print(
            ":computer: Shell | emojize=True symbolize=False "
            f"bash=ssh param0='{item['host']}' terminal=True"
        )
    print("---")
    print(
        ":arrows_counterclockwise: Refresh | refresh=true emojize=True "
        "symbolize=False"
    )
    print(
        ":link: Connect | emojize=True symbolize=False "
        f"bash='{sys.executable}' param0='{__file__}' param1='--connect' "
        "terminal=True"
    )
    print()


def format_job_label(job):
    if job["status"] == "RUNNING":
        icon = ":rocket:"
        time_ind = job['time_left']
    elif job["status"] == "PENDING":
        icon = ":hourglass_flowing_sand:"
        time_pending = re.sub(
            r"\.\d+$",
            "",
            job['time_pending']
        )
        time_ind = f":clock2: {time_pending}"
    else:
        icon = ":warning:"
        time_ind = ":bangbang:"
    return f"{icon} {job['job_name']} ({time_ind})"


def format_experiment_label(experiment):
    activity_delta = (
        datetime.now() - datetime.fromisoformat(experiment["time_activity"])
    )
    time_ind = humanize.naturaldelta(activity_delta)
    return f" :red_circle: {experiment['experiment_name']} ({time_ind})"


@click.command()
@click.option("--connect", default=False, is_flag=True)
@click.option(
    "--config-file", default="config.yaml", help="Path to the configuration file."
)
def main(config_file="config.yaml", connect=False):
    """Main entry point for the SwiftBar script.

    Arguments
    ---------
    config_file : str, optional
        Path to the configuration YAML file (default: 'config.yaml')
    connect : bool, optional
        Whether to run connection checks (default: False)

    Returns
    -------
    None
        Runs the dashboard or connection logic
    """
    config = read_config(config_file)
    if connect:
        run_connect(config)
        return
    dashboards = get_dashboards(config)
    output_dashboards(config, dashboards)


if __name__ == "__main__":
    main()
