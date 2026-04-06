# lambdarunner

[![PyPI version](https://img.shields.io/pypi/v/lambdarunner.svg)](https://pypi.org/project/lambdarunner/)
[![Python](https://img.shields.io/pypi/pyversions/lambdarunner.svg)](https://pypi.org/project/lambdarunner/)

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
```

Watch mode requires: `pip install lambdarunner[watch]`

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
| `--version` | `-V` | | Show version and exit |

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
