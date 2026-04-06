"""Tests for the runner module."""

import json
import os
import sys
from pathlib import Path

import pytest

from lambdarunner.runner import HandlerError, LambdaTimeoutError, invoke, parse_event

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _add_fixtures_to_path():
    """Ensure the fixtures directory is on sys.path for handler imports."""
    fixtures = str(FIXTURES_DIR)
    sys.path.insert(0, fixtures)
    yield
    sys.path.remove(fixtures)


class TestParseEvent:
    def test_empty_string(self):
        assert parse_event("{}") == {}

    def test_inline_json(self):
        result = parse_event('{"key": "value"}')
        assert result == {"key": "value"}

    def test_from_file(self):
        event_file = str(FIXTURES_DIR / "sample_event.json")
        result = parse_event(event_file)
        assert result["name"] == "Lambda"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_event("not valid json")

    def test_inline_json_list(self):
        result = parse_event("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_inline_json_string(self):
        result = parse_event('"hello"')
        assert result == "hello"

    def test_from_stdin(self, monkeypatch):
        from io import StringIO

        monkeypatch.setattr("sys.stdin", StringIO('{"source": "stdin"}'))
        result = parse_event("-")
        assert result == {"source": "stdin"}


class TestInvoke:
    def test_successful_handler(self):
        result, elapsed = invoke(
            handler_path="sample_handler.lambda_handler",
            event={"name": "Test"},
            timeout=10,
        )
        assert result["statusCode"] == 200
        assert result["body"] == "Hello Test"
        assert "requestId" in result
        assert elapsed > 0

    def test_handler_with_empty_event(self):
        result, _ = invoke(
            handler_path="sample_handler.lambda_handler",
            event={},
            timeout=10,
        )
        assert result["body"] == "Hello World"

    def test_handler_exception_propagates(self):
        with pytest.raises(
            HandlerError, match="RuntimeError: Something went wrong"
        ) as exc_info:
            invoke(
                handler_path="sample_handler.error_handler",
                event={},
                timeout=10,
            )
        assert exc_info.value.exc_type_name == "RuntimeError"
        assert "Something went wrong" in exc_info.value.exc_message
        assert exc_info.value.exc_traceback

    def test_timeout_raises_lambda_timeout_error(self):
        with pytest.raises(LambdaTimeoutError) as exc_info:
            invoke(
                handler_path="sample_handler.slow_handler",
                event={},
                timeout=1,
            )
        assert exc_info.value.timeout == 1

    def test_invalid_handler_path(self):
        with pytest.raises(ValueError, match="Invalid handler format"):
            invoke(handler_path="no_dot_here", event={}, timeout=5)

    def test_nonexistent_module(self):
        with pytest.raises(ModuleNotFoundError):
            invoke(
                handler_path="nonexistent_module.handler",
                event={},
                timeout=5,
            )

    def test_nonexistent_function(self):
        with pytest.raises(AttributeError):
            invoke(
                handler_path="sample_handler.nonexistent_func",
                event={},
                timeout=5,
            )

    def test_invoke_with_memory(self):
        result, elapsed = invoke(
            handler_path="sample_handler.lambda_handler",
            event={"name": "Test"},
            timeout=10,
            memory=256,
        )
        assert result["statusCode"] == 200

    def test_handler_error_has_traceback(self):
        with pytest.raises(HandlerError) as exc_info:
            invoke(
                handler_path="sample_handler.error_handler",
                event={},
                timeout=10,
            )
        assert "sample_handler" in exc_info.value.exc_traceback
        assert "RuntimeError" in exc_info.value.exc_traceback

    def test_lambda_env_vars_set(self):
        result, _ = invoke(
            handler_path="sample_handler.env_handler",
            event={},
            timeout=10,
            memory=512,
            region="eu-west-1",
        )
        assert result["function_name"] == "sample_handler"
        assert result["region"] == "eu-west-1"
        assert result["memory"] == "512"
        assert result["handler"] == "sample_handler.env_handler"

    def test_process_crash_raises_handler_error(self):
        with pytest.raises(HandlerError, match="ProcessError"):
            invoke(
                handler_path="sample_handler.crash_handler",
                event={},
                timeout=10,
            )


class TestResolveHandlerFile:
    def test_resolves_to_file(self):
        from lambdarunner.loader import resolve_handler_file

        path = resolve_handler_file("sample_handler.lambda_handler")
        assert path.name == "sample_handler.py"
        assert path.exists()

    def test_invalid_format_raises(self):
        from lambdarunner.loader import resolve_handler_file

        with pytest.raises(ValueError, match="Invalid handler format"):
            resolve_handler_file("no_dot_here")


class TestInvalidateHandlerCache:
    def test_removes_from_sys_modules(self):
        import importlib

        from lambdarunner.loader import invalidate_handler_cache

        importlib.import_module("sample_handler")
        assert "sample_handler" in sys.modules
        invalidate_handler_cache("sample_handler.lambda_handler")
        assert "sample_handler" not in sys.modules

    def test_no_error_if_not_cached(self):
        from lambdarunner.loader import invalidate_handler_cache

        invalidate_handler_cache("nonexistent_module.handler")


class TestLoadEnvFile:
    def test_load_env_file(self, tmp_path):
        from lambdarunner.loader import load_env_file

        env = tmp_path / ".env"
        env.write_text('FOO=bar\nBAZ="quoted"\n# comment\n')
        loaded = load_env_file(str(env))
        assert loaded["FOO"] == "bar"
        assert loaded["BAZ"] == "quoted"
        assert os.environ["FOO"] == "bar"

    def test_missing_env_file(self):
        from lambdarunner.loader import load_env_file

        with pytest.raises(FileNotFoundError):
            load_env_file("/nonexistent/.env")
