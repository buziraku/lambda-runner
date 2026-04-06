"""Dynamic module and handler loader."""

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


def load_handler(handler_path: str) -> Callable[..., Any]:
    """Load a Lambda handler function from a dotted path.

    Args:
        handler_path: Dotted path like 'module.function' or 'pkg.module.function'.

    Returns:
        The handler callable.

    Raises:
        ValueError: If the handler path format is invalid.
        ModuleNotFoundError: If the module cannot be imported.
        AttributeError: If the function doesn't exist in the module.
    """
    parts = handler_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid handler format: {handler_path!r}. "
            f"Expected 'module.function' (e.g. 'handler.lambda_handler')."
        )

    module_path, function_name = parts

    # Add cwd to sys.path so relative imports work
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    module = importlib.import_module(module_path)
    handler = getattr(module, function_name)

    if not callable(handler):
        raise AttributeError(
            f"{function_name!r} in module {module_path!r} is not callable."
        )

    return handler


def resolve_handler_file(handler_path: str) -> Path:
    """Resolve a handler path to its source file path.

    Args:
        handler_path: Dotted path like 'module.function'.

    Returns:
        Path to the handler's source file.
    """
    parts = handler_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid handler format: {handler_path!r}. "
            f"Expected 'module.function' (e.g. 'handler.lambda_handler')."
        )

    module_path = parts[0]

    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    module = importlib.import_module(module_path)
    return Path(module.__file__)


def invalidate_handler_cache(handler_path: str) -> None:
    """Remove a handler's module from the import cache."""
    module_path = handler_path.rsplit(".", 1)[0]
    sys.modules.pop(module_path, None)


def load_env_file(env_file: str) -> dict[str, str]:
    """Load environment variables from a .env file.

    Supports KEY=VALUE format, ignores comments (#) and blank lines.
    Strips surrounding quotes from values.

    Returns:
        Dict of loaded variable names to values.
    """
    import os

    loaded: dict[str, str] = {}
    path = Path(env_file)

    if not path.exists():
        raise FileNotFoundError(f"Env file not found: {env_file}")

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        os.environ[key] = value
        loaded[key] = value

    return loaded
