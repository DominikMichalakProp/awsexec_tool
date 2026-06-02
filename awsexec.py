import argparse
import configparser
import os
import subprocess
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError

try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline  # Windows
    except ImportError:
        readline = None

# ── ANSI colors (auto-disabled when not a tty) ───────────────────────────────

_COLOR = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text

def bold(t):   return _c("1", t)
def dim(t):    return _c("2", t)
def cyan(t):   return _c("1;36", t)
def green(t):  return _c("1;32", t)
def red(t):    return _c("1;31", t)
def yellow(t): return _c("1;33", t)

# ── Helpers ───────────────────────────────────────────────────────────────────

def ask(prompt: str, default: str = "") -> str:
    if readline is not None:
        readline.set_startup_hook(lambda: readline.insert_text(default))
    try:
        response = input(prompt)
    finally:
        if readline is not None:
            readline.set_startup_hook()
    return response.strip() or default


def pick(label: str, items: list, key=lambda x: x) -> object:
    """Print numbered list, prompt user to pick one. Retries on bad input."""
    if not items:
        print(red(f"  No {label}s found."))
        sys.exit(1)
    for i, item in enumerate(items, 1):
        print(f"  {dim(str(i))}: {key(item)}")
    while True:
        try:
            idx = int(ask(f"  Select {label} [1-{len(items)}]: ")) - 1
            if 0 <= idx < len(items):
                print(f"  {green('✓')} {key(items[idx])}\n")
                return items[idx]
            print(yellow(f"  Enter a number between 1 and {len(items)}."))
        except ValueError:
            print(yellow("  Enter a number."))


def list_profiles() -> list:
    """Read profile names from ~/.aws/credentials and ~/.aws/config."""
    creds_path = os.environ.get(
        "AWS_SHARED_CREDENTIALS_FILE", os.path.expanduser("~/.aws/credentials")
    )
    config_path = os.path.expanduser("~/.aws/config")

    creds = configparser.ConfigParser()
    cfg = configparser.ConfigParser()
    creds.read(creds_path)
    cfg.read(config_path)

    profiles = set(creds.sections())
    for section in cfg.sections():
        name = section[len("profile "):] if section.startswith("profile ") else section
        profiles.add(name)

    return sorted(profiles)


def paginate_ecs(client, method: str, result_key: str, **kwargs) -> list:
    paginator = client.get_paginator(method)
    results = []
    for page in paginator.paginate(**kwargs):
        results.extend(page[result_key])
    return results


def arn_name(arn: str) -> str:
    return arn.split("/")[-1]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Interactive ECS exec — drop into any container in seconds."
    )
    parser.add_argument("--profile", help="AWS profile name")
    parser.add_argument("--region",  help="AWS region (e.g. eu-west-1)")
    parser.add_argument("--command", default="/bin/sh",
                        help="Shell command to run (default: /bin/sh)")
    args = parser.parse_args()

    print(cyan(bold("\n  awsexec — ECS interactive exec\n")))

    # ── Profile ───────────────────────────────────────────────────────────────
    if args.profile:
        profile = args.profile
        print(f"  Profile: {green(profile)}\n")
    else:
        profiles = list_profiles()
        print(bold("  AWS Profiles:"))
        profile = pick("profile", profiles)

    # ── Region ────────────────────────────────────────────────────────────────
    if args.region:
        region = args.region
        print(f"  Region: {green(region)}\n")
    else:
        default_region = boto3.Session(profile_name=profile).region_name or "eu-west-1"
        region = ask(f"  Region [{default_region}]: ", default_region)
        print()

    # ── ECS client ────────────────────────────────────────────────────────────
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        ecs = session.client("ecs")

        # Cluster
        print(bold("  Clusters:"))
        cluster_arns = paginate_ecs(ecs, "list_clusters", "clusterArns")
        cluster_arn = pick("cluster", cluster_arns, key=arn_name)
        cluster_name = arn_name(cluster_arn)

        # Service
        print(bold("  Services:"))
        service_arns = paginate_ecs(ecs, "list_services", "serviceArns",
                                    cluster=cluster_arn)
        service_arn = pick("service", service_arns, key=arn_name)
        service_name = arn_name(service_arn)

        # Task
        print(bold("  Tasks:"))
        task_arns = paginate_ecs(ecs, "list_tasks", "taskArns",
                                 cluster=cluster_arn, serviceName=service_name)
        task_arn = pick("task", task_arns, key=arn_name)
        task_id = arn_name(task_arn)

        # Container
        resp = ecs.describe_tasks(cluster=cluster_arn, tasks=[task_arn])
        if not resp["tasks"]:
            print(red(f"  Task {task_id} not found — may have stopped."))
            sys.exit(1)
        containers = resp["tasks"][0]["containers"]

        print(bold("  Containers:"))
        container = pick("container", containers, key=lambda c: c["name"])
        container_name = container["name"]

    except ClientError as e:
        print(red(f"\n  AWS error: {e.response['Error']['Message']}"))
        sys.exit(1)
    except BotoCoreError as e:
        print(red(f"\n  AWS error: {e}"))
        sys.exit(1)

    # ── Command ───────────────────────────────────────────────────────────────
    command = args.command if args.command != "/bin/sh" else \
              ask(f"  Command [{args.command}]: ", args.command)

    cmd = [
        "aws", "ecs", "execute-command",
        "--cluster", cluster_name,
        "--task", task_id,
        "--container", container_name,
        "--command", command,
        "--interactive",
        "--profile", profile,
        "--region", region,
    ]

    print(f"\n  {bold('Command:')}")
    print(f"  {dim(' '.join(cmd))}\n")

    if ask("  Execute? [y/N]: ").lower() != "y":
        print(dim("  Aborted."))
        sys.exit(0)

    print(cyan("\n  Connecting...\n"))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(red(f"\n  Command exited with code {result.returncode}."))
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
