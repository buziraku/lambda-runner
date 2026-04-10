"""Core runner: execute Lambda handlers with timeout."""

import json
import multiprocessing
import os
import sys
import time
import traceback as tb_module
from collections.abc import Callable
from pathlib import Path
from typing import Any

from lambdarunner.context import LambdaContext
from lambdarunner.loader import load_handler


class LambdaTimeoutError(Exception):
    """Raised when a Lambda handler exceeds its configured timeout."""

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout
        super().__init__(f"Function timed out after {timeout} seconds")


class HandlerError(Exception):
    """Wraps an exception that occurred in the handler subprocess."""

    def __init__(
        self,
        exc_type_name: str,
        exc_message: str,
        exc_traceback: str,
    ) -> None:
        self.exc_type_name = exc_type_name
        self.exc_message = exc_message
        self.exc_traceback = exc_traceback
        super().__init__(f"{exc_type_name}: {exc_message}")


def parse_event(event_input: str) -> Any:
    """Parse event from a JSON file path, inline JSON string, or stdin.

    Args:
        event_input: Path to a .json file, a raw JSON string, or "-" for stdin.

    Returns:
        Parsed event data.
    """
    if not event_input or event_input == "{}":
        return {}

    if event_input == "-":
        return json.loads(sys.stdin.read())

    path = Path(event_input)
    if path.exists() and path.is_file():
        return json.loads(path.read_text(encoding="utf-8-sig"))

    return json.loads(event_input)


def _find_free_port() -> int:
    """Return an ephemeral free TCP port on localhost."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_handler_in_process(
    handler: Callable[..., Any],
    event: Any,
    handler_path: str,
    function_name: str,
    timeout: int,
    memory: int,
    region: str,
    result_queue: multiprocessing.Queue,
    mock_aws_endpoint: str | None = None,
) -> None:
    """Execute a Lambda handler in an isolated subprocess."""
    os.environ.update(
        {
            "AWS_LAMBDA_FUNCTION_NAME": function_name,
            "AWS_LAMBDA_FUNCTION_VERSION": "$LATEST",
            "AWS_REGION": region,
            "AWS_DEFAULT_REGION": region,
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": str(memory),
            "_HANDLER": handler_path,
        }
    )

    if mock_aws_endpoint:
        os.environ["AWS_ENDPOINT_URL"] = mock_aws_endpoint
        os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
        os.environ.setdefault("AWS_SESSION_TOKEN", "testing")

    context = LambdaContext(
        function_name=function_name,
        timeout=timeout,
        memory_limit_in_mb=memory,
        region=region,
    )

    start = time.monotonic()
    try:
        result = handler(event, context)
        elapsed = time.monotonic() - start
        result_queue.put(("ok", result, elapsed))
    except Exception as exc:
        elapsed = time.monotonic() - start
        try:
            result_queue.put(
                ("error", type(exc).__name__, str(exc), tb_module.format_exc(), elapsed)
            )
        except Exception:
            result_queue.put(("error", type(exc).__name__, str(exc), "", elapsed))


def invoke(
    handler_path: str,
    event: Any,
    timeout: int = 30,
    memory: int = 128,
    region: str = "us-east-1",
    mock_aws: bool = False,
) -> tuple[Any, float]:
    """Invoke a Lambda handler locally.

    Args:
        handler_path: Dotted path to the handler (e.g. 'module.function').
        event: The event data to pass to the handler.
        timeout: Timeout in seconds.
        memory: Simulated memory limit in MB.
        region: Simulated AWS region.
        mock_aws: If True, start a local moto server and redirect AWS SDK calls to it.

    Returns:
        Tuple of (handler result, execution time in seconds).

    Raises:
        LambdaTimeoutError: If the handler exceeds the timeout.
        HandlerError: If the handler raises an exception.
        ValueError: If the handler path format is invalid.
        ModuleNotFoundError: If the handler module cannot be found.
        AttributeError: If the handler function doesn't exist.
    """
    handler = load_handler(handler_path)

    function_name = handler_path.rsplit(".", 1)[0].replace(".", "_")

    mock_server = None
    mock_endpoint: str | None = None

    if mock_aws:
        try:
            from moto.server import ThreadedMotoServer
        except ImportError:
            raise ImportError(
                "moto is required for --mock-aws mode. "
                "Install with: pip install lambdarunner[mock]"
            ) from None
        port = _find_free_port()
        mock_server = ThreadedMotoServer(port=port)
        mock_server.start()
        mock_endpoint = f"http://127.0.0.1:{port}"

    result_queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_run_handler_in_process,
        args=(
            handler,
            event,
            handler_path,
            function_name,
            timeout,
            memory,
            region,
            result_queue,
            mock_endpoint,
        ),
    )

    try:
        process.start()
        process.join(timeout=timeout)

        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()
            raise LambdaTimeoutError(timeout)

        if result_queue.empty():
            raise HandlerError(
                "ProcessError",
                f"Handler process exited with code {process.exitcode}"
                " without producing a result",
                "",
            )

        status, *payload = result_queue.get_nowait()

        if status == "ok":
            result, elapsed = payload
            return result, elapsed

        exc_type_name, exc_message, exc_traceback, elapsed = payload
        raise HandlerError(exc_type_name, exc_message, exc_traceback)
    finally:
        if mock_server is not None:
            mock_server.stop()
