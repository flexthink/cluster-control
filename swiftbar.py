import json
import subprocess
import shlex
from pathlib import Path

import click
import yaml
import sys


def read_config(file_name):
    file_name = Path(file_name)
    if not file_name.is_absolute():
        file_name = Path(__file__).parent / file_name
    with open(file_name, "r") as f:
        return yaml.safe_load(f)


def get_dashboards(config):
    dashboards = {
        key: get_dashboard(item["host"]) for key, item in config["servers"].items()
    }
    return dashboards


def get_dashboard(host):
    try:
        result = subprocess.run(
            ["ssh", host, "python", "rc/dashboard.py"],
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
    for key, item in config["servers"].items():
        click.echo(f"{click.style('Connecting: ', fg='yellow')} {key}")
        try:
            subprocess.run(["ssh", item["host"], "/bin/true"], text=True)
        except subprocess.CalledProcessError as e:
            click.echo(f"{click.style('Error:', color='red')} {e}")


def output_dashboards(config, dashboards):
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
            if job["status"] == "RUNNING":
                icon = ":rocket:"
            elif job["status"] == "PENDING":
                icon = ":hourglass_flowing_sand:"
            else:
                icon = ":warning:"
            print(
                f"{icon} {job['job_name']} ({job['time_left']}) "
                f"| emojize=True symbolize=False color='yellow' bash='ssh' param0='{item['host']}' param1=\"'~/rc/tail-log.sh'\" param2='{job['job_name']}' terminal=true"
            )
        print("---")
        print(
            ":computer: Shell | emojize=True symbolize=False "
            f"bash=ssh param0='{item['host']}' terminal=True"
        )
    print("---")
    print(
        ":arrows_counterclockwise: Refresh | refresh=true emojize=True symbolize=False"
    )
    print(
        ":link: Connect | emojize=True symbolize=False "
        f"bash='{sys.executable}' param0='{__file__}' param1='--connect' terminal=True"
    )
    print()


@click.command()
@click.option("--connect", default=False, is_flag=True)
@click.option(
    "--config-file", default="config.yaml", help="Path to the configuration file."
)
def main(config_file="config.yaml", connect=False):
    config = read_config(config_file)
    if connect:
        run_connect(config)
        return
    dashboards = get_dashboards(config)
    output_dashboards(config, dashboards)


if __name__ == "__main__":
    main()
