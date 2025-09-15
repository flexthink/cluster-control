# Cluster Control

Cluster Control is a SwiftBar script designed to monitor SLURM clusters directly from your macOS menu bar. It provides real-time updates on cluster status, job queues, and resource usage, helping users efficiently manage and observe their SLURM workloads.

## What is SwiftBar?

SwiftBar is a powerful macOS application that allows you to display custom scripts and plugins in your menu bar.  
Learn more and download SwiftBar here: [https://swiftbar.app](https://swiftbar.app)

## Features

- Monitor SLURM cluster status
- View job queues and resource usage
- Real-time updates in the menu bar

## Installation

- Download and install SwiftBar
- Clone this repository
- Copy the `rc` directory to the home directory on your cluster
- Modify `config.yaml` to specify the servers you would like to control
- Ensure that you can open new SSH connections to these servers without a password prompt while your session is active (i.e. by loading a cryptographic key and using features like ControlMaster to avoid a new MFA prompt on every connection)
- Create a SwiftBar script loading the correct Python virtual environment



## Configuration
Open `config.yaml` and set up each cluster entry point as follows:

```yaml
server-handle:
    host: server.somedomain.com
    label: My Server
```

## Sample SwiftBar script

```bash
#!/bin/bash
. /Users/jdoe/venv/myenv/bin/activate
python /Users/jdoe/Projects/cluster-control/swiftbar.py
```


## License

MIT license