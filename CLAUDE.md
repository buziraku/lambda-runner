# lambdarunner

## Project Overview
CLI tool for running AWS Lambda handlers locally. No Docker, no SAM, no AWS connection required.
Python 3.12+ | Poetry | Typer + Rich | MIT License

## Architecture

| File | Responsibility |
|------|---------------|
| `lambdarunner/cli.py` | Typer CLI entry point, Rich output formatting, flag handling |
| `lambdarunner/runner.py` | Core engine: event parsing, subprocess invocation with timeout |
| `lambdarunner/context.py` | Simulated `LambdaContext` object |
| `lambdarunner/loader.py` | Dynamic module loading (`load_handler`) and `.env` file parsing |

## Key Design Decisions

- **`load_handler()` runs in the parent process** for fail-fast with native exceptions (ValueError, ModuleNotFoundError, AttributeError). Only `handler(event, context)` runs in the subprocess.
- **`multiprocessing.Process` + `Queue`** for real timeout cancellation via `process.terminate()`. Never use ThreadPoolExecutor for handler execution.
- **`HandlerError`** wraps subprocess exceptions with serialized type name, message, and traceback string. Never try to pickle arbitrary exception objects directly.
- **`LambdaContext` is created inside the subprocess** so `_start_time` reflects actual handler execution start, not context construction time.
- **Lambda environment variables** (`AWS_LAMBDA_FUNCTION_NAME`, `AWS_REGION`, etc.) are set inside the subprocess only, to avoid polluting the parent process.

## Development Commands

```bash
poetry run pytest -v          # run tests
poetry run ruff check .       # lint
poetry run ruff format .      # format
poetry run ruff format --check .  # check format without modifying
```

## Code Style

- Line length: 88
- Quote style: double quotes
- Linter rules: E, F, I, UP, B, SIM (ruff)
- Target: Python 3.12+

## Rules

- NEVER rewrite entire files. Use surgical edits on specific functions/sections.
- All CLI flags must be defined as Typer `Annotated` parameters. Never check `sys.argv` directly.
- All changes to runner.py or cli.py must have corresponding tests.
- The subprocess target function (`_run_handler_in_process`) must be defined at module level (required by multiprocessing).
- Exception propagation from subprocess uses string tuples `("error", type_name, message, traceback_str, elapsed)`, never raw exception objects.

## Dependency Security

- **Always use exact version pins (`==`)** in `pyproject.toml`. Never use `>=`, `^`, or `~`.
- **Renovate** handles dependency updates via PRs with a 3-day minimum release age (`minimumReleaseAge`). Never update dependencies manually — let Renovate create the PR and review it before merging.
- **`poetry.lock` must always be committed.** It contains SHA256 hashes that prevent tampered packages from being installed.
- When adding a new dependency, pin it to the exact version installed: `poetry show <package>` to get the version, then add `package = "==X.Y.Z"` to `pyproject.toml`.

## Known Pitfalls

- `importlib.import_module()` caches modules in `sys.modules`. With multiprocessing + fork, the subprocess inherits the parent's module cache.
- `multiprocessing.Queue.put()` pickles data internally. If handler returns unpicklable objects, the PicklingError is caught and reported as a `HandlerError`.
- On timeout: always `terminate()` first (SIGTERM), then `kill()` (SIGKILL) as fallback, to handle handlers that trap SIGTERM.
- `process.join(timeout=N)` may return with process still alive — always check `process.is_alive()` after join.
