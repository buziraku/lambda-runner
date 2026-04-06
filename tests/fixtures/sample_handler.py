"""Sample Lambda handlers for testing."""

import time


def lambda_handler(event, context):
    """Simple handler that returns event data."""
    return {
        "statusCode": 200,
        "body": f"Hello {event.get('name', 'World')}",
        "requestId": context.aws_request_id,
    }


def error_handler(event, context):
    """Handler that always raises an exception."""
    raise RuntimeError("Something went wrong in the handler")


def slow_handler(event, context):
    """Handler that sleeps longer than any reasonable timeout."""
    time.sleep(60)
    return {"statusCode": 200}


def env_handler(event, context):
    """Handler that returns Lambda environment variables."""
    import os

    return {
        "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", ""),
        "region": os.environ.get("AWS_REGION", ""),
        "memory": os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", ""),
        "handler": os.environ.get("_HANDLER", ""),
    }


def crash_handler(event, context):
    """Handler that crashes the process."""
    import os

    os._exit(1)
