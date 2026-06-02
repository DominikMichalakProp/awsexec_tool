# awsexec

> Interactive ECS `execute-command` launcher — drop into any container in seconds.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![AWS](https://img.shields.io/badge/AWS-ECS-orange)

```
  awsexec — ECS interactive exec

  AWS Profiles:
  1: default
  2: prod
  3: staging
  Select profile [1-3]: 2
  ✓ prod

  Region [eu-west-1]:
  ✓ eu-west-1

  Clusters:
  1: my-cluster-prod
  Select cluster [1-1]: 1
  ✓ my-cluster-prod

  Services:
  1: api-service
  2: worker-service
  Select service [1-2]: 1
  ✓ api-service

  Tasks:
  1: a1b2c3d4e5f6...
  Select task [1-1]: 1
  ✓ a1b2c3d4e5f6...

  Containers:
  1: api
  2: sidecar
  Select container [1-2]: 1
  ✓ api

  Command [/bin/sh]:

  Command:
  aws ecs execute-command --cluster my-cluster-prod --task a1b2c3d4... --container api --command /bin/sh --interactive --profile prod --region eu-west-1

  Execute? [y/N]: y

  Connecting...
```

## Requirements

| Dependency | Notes |
|---|---|
| Python 3.8+ | |
| [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) | v1 not supported |
| [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) | Required for `execute-command` |
| `boto3` | `pip install boto3` |
| ECS Exec enabled | `enableExecuteCommand: true` on task definition |

## Install

```bash
git clone <repo-url>
cd awsexec_tool
pip install boto3
```

Optional — add alias:

```bash
echo 'alias awsexec="python3 /path/to/awsexec.py"' >> ~/.bashrc && source ~/.bashrc
```

## Usage

```bash
# Fully interactive
python3 awsexec.py

# Skip profile + region prompts
python3 awsexec.py --profile prod --region eu-west-1

# Custom shell command
python3 awsexec.py --profile prod --region eu-west-1 --command /bin/bash

# One-liner (all flags)
awsexec --profile prod --region eu-west-1 --command "/bin/sh"
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `--profile` | interactive | AWS profile from `~/.aws/credentials` or `~/.aws/config` |
| `--region` | from AWS config | AWS region |
| `--command` | `/bin/sh` | Shell command to exec into container |

## IAM Permissions

Minimum policy for the executing role:

```json
{
  "Effect": "Allow",
  "Action": [
    "ecs:ListClusters",
    "ecs:ListServices",
    "ecs:ListTasks",
    "ecs:DescribeTasks",
    "ecs:ExecuteCommand",
    "ssmmessages:CreateControlChannel",
    "ssmmessages:CreateDataChannel",
    "ssmmessages:OpenControlChannel",
    "ssmmessages:OpenDataChannel"
  ],
  "Resource": "*"
}
```

## Troubleshooting

**`SessionManagerPlugin is not found`**
→ Install the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

**`execute-command is not enabled for this task`**
→ Redeploy task/service with `enableExecuteCommand: true` in the task definition

**`No tasks found`**
→ Service has no running tasks, or you picked the wrong cluster/service

**`AWS error: An error occurred (InvalidClientTokenId)`**
→ Credentials expired — run `aws sso login --profile <name>` or refresh tokens

**Profiles list is empty**
→ Check `~/.aws/credentials` and `~/.aws/config` exist and are readable.
   Set `AWS_SHARED_CREDENTIALS_FILE` if using a custom path.

## Notes

- Profiles read from `~/.aws/credentials` + `~/.aws/config` (respects `AWS_SHARED_CREDENTIALS_FILE`)
- All ECS list calls use pagination — no silent truncation on large accounts
- Colors auto-disabled when piped (non-tty output)
