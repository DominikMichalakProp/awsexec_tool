# AWS Exec Command Generator

This Python script is designed to generate AWS Exec command based on the input provided by the user. The user is prompted to provide a series of details that are then used to generate the appropriate command.

## Requirements

To run this script, you will need:

- Python 3.6 or later
- Python modules: os, subprocess, json, readline (optional)

## Installation

1. Clone this repository to your device

2. Install the required Python modules

```bash
pip install os subprocess json readline
```

3. Run the script using your Python interpreter:

```bash
python aws_exec_command_generator.py
```

4. Then, follow the instructions displayed in the console.

## Functions

### The script includes the following functions:

    ask_user_input(prompt: str, default: str = '') -> str: Prompts the user to provide input
    get_clusters(profile: str, region: str) -> dict: Retrieves a list of clusters
    get_tasks_for_service(profile: str, cluster: str, service: str, region: str) -> dict: Retrieves a list of tasks for a given service
    get_services(profile: str, cluster: str, region: str) -> dict: Retrieves a list of services for a given cluster
    get_containers(profile: str, cluster: str, task: str, region: str) -> dict: Retrieves a list of containers for a given task
    construct_command(cluster_name: str, task_id: str, container_name: str, command_to_execute: str, profile_name: str, region: str) -> str: Generates the AWS Exec command
    confirm_execution() -> bool: Asks the user to confirm the command execution
    main(): The main function of the program

## Additional Info

  To add this command to your bash profile, you can append an alias to your ~/.bashrc file:

```bash
echo 'alias awsexec="python /path/to/your/script/aws_exec_command_generator.py"' >> ~/.bashrc
```

After adding the alias, run the following command to make the changes effective:

```bash
source ~/.bashrc
```

Now, you can use the **awsexec** command directly from your terminal!

## Notes

Ensure you have AWS CLI installed and AWS CLI profiles configured on your device.
