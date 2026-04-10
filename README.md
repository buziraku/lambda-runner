# lambdarunner

[![PyPI version](https://img.shields.io/pypi/v/lambdarunner.svg)](https://pypi.org/project/lambdarunner/)
[![Python](https://img.shields.io/pypi/pyversions/lambdarunner.svg)](https://pypi.org/project/lambdarunner/)
[![CI](https://github.com/buziraku/lambdarunner/actions/workflows/ci.yml/badge.svg)](https://github.com/buziraku/lambdarunner/actions/workflows/ci.yml)

Run AWS Lambda handlers locally. No Docker, no SAM, no AWS connection required.

## Installation

```bash
pip install lambdarunner
```

Or with [pipx](https://pipx.pypa.io/) for global CLI use:

```bash
pipx install lambdarunner
```

## Quickstart

Given a handler file `handler.py`:

```python
def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": f"Hello {event.get('name', 'World')}"
    }
```

Run it:

```bash
# With an event file
lambdarunner invoke handler.lambda_handler -e event.json

# With inline JSON
lambdarunner invoke handler.lambda_handler --event '{"name": "Lambda"}'

# With a custom timeout
lambdarunner invoke handler.lambda_handler -e event.json -t 10

# With environment variables
lambdarunner invoke handler.lambda_handler --env-file .env --region eu-west-1

# With event from stdin
echo '{"name": "Pipe"}' | lambdarunner invoke handler.lambda_handler -e -

# Watch mode (re-invoke on file changes)
lambdarunner invoke handler.lambda_handler -e event.json --watch

# With AWS mocking (boto3 calls intercepted by moto)
lambdarunner invoke handler.lambda_handler -e event.json --mock-aws
```

Watch mode requires: `pip install lambdarunner[watch]`

Mock AWS mode requires: `pip install lambdarunner[mock]`

## Event Templates

Generate ready-to-use event JSON for the most common Lambda trigger types:

```bash
# List all available templates
lambdarunner template

# Print a template to the terminal
lambdarunner template s3
lambdarunner template sqs
lambdarunner template sns
lambdarunner template eventbridge
lambdarunner template apigw       # API Gateway REST API (v1)
lambdarunner template apigw-v2    # API Gateway HTTP API (v2)
```

Save to file and use with `invoke`:

```bash
# Bash / Zsh (Linux, macOS)
lambdarunner template s3 > event.json
lambdarunner invoke handler.lambda_handler --event event.json

# PowerShell 7 (pwsh)
lambdarunner template s3 > event.json

# PowerShell 5 (Windows PowerShell)
# Use Out-File to ensure UTF-8 encoding (plain `>` produces UTF-16 in PS5)
lambdarunner template s3 | Out-File -Encoding utf8 event.json
```

## CLI Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--event` | `-e` | `{}` | Path to a JSON file, inline JSON string, or `-` for stdin |
| `--timeout` | `-t` | `30` | Timeout in seconds |
| `--memory` | `-m` | `128` | Simulated memory limit in MB |
| `--env-file` | | `None` | Path to a `.env` file to load |
| `--region` | | `us-east-1` | Simulated `AWS_DEFAULT_REGION` |
| `--profile` | | `None` | AWS profile name for context |
| `--pretty / --no-pretty` | | `True` | Pretty print JSON output |
| `--traceback` | | `False` | Show full traceback on handler errors |
| `--watch` | `-w` | `False` | Re-invoke on handler file changes |
| `--mock-aws` | | `False` | Start a local moto server and redirect boto3 calls to it |
| `--version` | `-V` | | Show version and exit |

## Mock AWS

Use `--mock-aws` to intercept all `boto3` calls with [moto](https://github.com/getmoto/moto) — no AWS account, no credentials, no Docker required.

```python
# handler.py
import boto3

def lambda_handler(event, context):
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="my-bucket")
    s3.put_object(Bucket="my-bucket", Key="hello.txt", Body=b"world")
    obj = s3.get_object(Bucket="my-bucket", Key="hello.txt")
    return {"body": obj["Body"].read().decode()}
```

```bash
lambdarunner invoke handler.lambda_handler --mock-aws
```

boto3 is redirected to a local moto server automatically — no `@mock_aws` decorators needed in your handler code.

**Note:** AWS state (buckets, tables, queues, etc.) is reset on every invocation. In `--watch` mode, each file-change re-invoke starts with a fresh mock environment.

## Shell Completion

Enable tab completion for your shell:

```bash
lambdarunner --install-completion
```

Supports Bash, Zsh, Fish, and PowerShell.

## Why lambdarunner?

- Built from scratch with modern Python (3.12+)
- Polished CLI experience with Typer + Rich
- Faithful Lambda Context simulation, including `get_remaining_time_in_millis()`
- Real timeout handling with process isolation via `multiprocessing`

## License

MIT
