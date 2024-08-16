import os
import subprocess
import json

try:
    import readline
except ImportError:
    try:
        import pyreadline as readline  # Windows
    except ImportError:
        print("Nie można zaimportować readline. Edycja linii może nie działać.")
        readline = None

def ask_user_input(prompt: str, default: str = '') -> str:
    if readline is not None:
        readline.set_startup_hook(lambda: readline.insert_text(default))
    response = input(prompt)
    readline.set_startup_hook()
    return response or default

def get_clusters(profile: str, region: str) -> dict:
    return json.loads(subprocess.getoutput(f"aws ecs list-clusters --profile {profile} --region {region}"))

def get_tasks_for_service(profile: str, cluster: str, service: str, region: str) -> dict:
    return json.loads(subprocess.getoutput(f"aws ecs list-tasks --cluster {cluster} --service-name {service} --profile {profile} --region {region}"))

def get_services(profile: str, cluster: str, region: str) -> dict:
    return json.loads(subprocess.getoutput(f"aws ecs list-services --cluster {cluster} --profile {profile} --region {region}"))

def get_containers(profile: str, cluster: str, task: str, region: str) -> dict:
    task_description = json.loads(subprocess.getoutput(f"aws ecs describe-tasks --cluster {cluster} --tasks {task} --profile {profile} --region {region}"))
    return task_description['tasks'][0]['containers']

def construct_command(cluster_name: str, task_id: str, container_name: str, command_to_execute: str, profile_name: str, region: str) -> str:
    return f'aws ecs execute-command --cluster {cluster_name} --task {task_id} --container {container_name} --command "{command_to_execute}" --interactive --profile {profile_name} --region {region}'

def confirm_execution() -> bool:
    confirmation = input("Do you want to execute the command? (y/n): ")
    return confirmation.lower() == "y"

def main():
    print(subprocess.getoutput("cat ~/.aws/credentials | grep -E '\\[[^]]+\\]' | sed 's/\\[//g' | sed 's/\\]//g'"))
    profile_name = ask_user_input(".aws/credentials profile name: ")
    region = ask_user_input("Region: ")

    clusters = get_clusters(profile_name, region)['clusterArns']
    for i, cluster in enumerate(clusters):
        print(f"{i+1}: {cluster.split('/')[-1]}")
    cluster_index = int(ask_user_input("Cluster name: ")) - 1

    services = get_services(profile_name, clusters[cluster_index], region)['serviceArns']
    for i, service in enumerate(services):
        print(f"{i+1}: {service.split('/')[-1]}")
    service_index = int(ask_user_input("Service name: ")) - 1

    tasks = get_tasks_for_service(profile_name, clusters[cluster_index], services[service_index].split('/')[-1], region)['taskArns']
    for i, task in enumerate(tasks):
        print(f"{i+1}: {task.split('/')[-1]}")
    task_index = int(ask_user_input("Task id: ")) - 1

    containers = get_containers(profile_name, clusters[cluster_index], tasks[task_index], region)
    for i, container in enumerate(containers):
        print(f"{i+1}: {container['name']}")
    container_index = int(ask_user_input("Container name: ")) - 1

    command_to_execute = ask_user_input("Command for connection (default /bin/sh):", "/bin/sh")
    command = construct_command(clusters[cluster_index].split('/')[-1], tasks[task_index].split('/')[-1], containers[container_index]['name'], command_to_execute, profile_name, region)
    print(f"\nYour command: \n{command}\n")

    if confirm_execution():
        print("Executing the command...")
        os.system(command)
        print("The command has been executed")
    else:
        print("Command execution aborted")

if __name__ == "__main__":
    main()

