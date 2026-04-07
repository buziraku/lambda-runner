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


def _parse_env_content(content: str):
    """Parse .env content yielding (key, raw_value, quote_char) tuples."""
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        quote_char = ""
        if value and value[0] in ('"', "'"):
            quote_char = value[0]
            if len(value) >= 2 and value[-1] == quote_char:
                value = value[1:-1]
            else:
                parts = [value[1:]]
                while i < len(lines):
                    raw = lines[i]
                    i += 1
                    if raw.rstrip().endswith(quote_char):
                        parts.append(raw.rstrip()[:-1])
                        break
                    parts.append(raw)
                value = "\n".join(parts)
        else:
            idx = value.find(" #")
            if idx >= 0:
                value = value[:idx].rstrip()

        yield key, value, quote_char


def load_env_file(env_file: str) -> dict[str, str]:
    """Load environment variables from a .env file.

    Supports KEY=VALUE format, export prefix, inline comments,
    multiline quoted values, and variable expansion ($VAR / ${VAR}).
    Single-quoted values are treated as literals (no expansion).

    Returns:
        Dict of loaded variable names to values.
    """
    import os
    import re

    loaded: dict[str, str] = {}
    path = Path(env_file)

    if not path.exists():
        raise FileNotFoundError(f"Env file not found: {env_file}")

    for key, value, quote_char in _parse_env_content(path.read_text()):
        if quote_char != "'":
            value = re.sub(
                r"\$\{(\w+)\}|\$(\w+)",
                lambda m: loaded.get(
                    m.group(1) or m.group(2),
                    os.environ.get(m.group(1) or m.group(2), ""),
                ),
                value,
            )

        os.environ[key] = value
        loaded[key] = value

    return loaded
