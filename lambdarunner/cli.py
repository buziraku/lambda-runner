"""CLI entry point using Typer + Rich."""

import json
import os
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from lambdarunner import __version__
from lambdarunner.loader import load_env_file
from lambdarunner.runner import HandlerError, LambdaTimeoutError, invoke, parse_event

app = typer.Typer(
    name="lambdarunner",
    help="Run AWS Lambda handlers locally. No Docker, no SAM, no AWS.",
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"lambdarunner {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """Run AWS Lambda handlers locally. No Docker, no SAM, no AWS."""


@app.command("invoke")
def invoke_cmd(
    handler: Annotated[
        str,
        typer.Argument(help="Handler path in module.function format"),
    ],
    event: Annotated[
        str,
        typer.Option(
            "--event",
            "-e",
            help="Path to JSON file or inline JSON string",
        ),
    ] = "{}",
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", help="Timeout in seconds"),
    ] = 30,
    memory: Annotated[
        int,
        typer.Option("--memory", "-m", help="Simulated memory limit in MB"),
    ] = 128,
    env_file: Annotated[
        str | None,
        typer.Option("--env-file", help="Path to .env file"),
    ] = None,
    region: Annotated[
        str,
        typer.Option("--region", help="Simulated AWS region"),
    ] = "us-east-1",
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="AWS profile name for context"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty/--no-pretty", help="Pretty print JSON output"),
    ] = True,
    traceback: Annotated[
        bool,
        typer.Option("--traceback", help="Show full traceback on handler errors"),
    ] = False,
    watch: Annotated[
        bool,
        typer.Option("--watch", "-w", help="Re-invoke on handler file changes"),
    ] = False,
) -> None:
    """Invoke a Lambda handler locally."""
    # Display invocation info
    event_display = event if event != "{}" else "(empty)"
    info_text = (
        f"[bold]Handler[/bold]  : {handler}\n"
        f"[bold]Event[/bold]    : {event_display}\n"
        f"[bold]Timeout[/bold]  : {timeout}s\n"
        f"[bold]Memory[/bold]   : {memory}MB\n"
        f"[bold]Region[/bold]   : {region}"
    )
    if profile:
        info_text += f"\n[bold]Profile[/bold]  : {profile}"

    console.print(Panel(info_text, title="Lambda Runner", border_style="cyan"))

    os.environ["AWS_DEFAULT_REGION"] = region
    os.environ["AWS_REGION"] = region
    if profile:
        os.environ["AWS_PROFILE"] = profile

    # Load env file if provided
    if env_file:
        try:
            loaded = load_env_file(env_file)
            console.print(
                f"[dim]Loaded {len(loaded)} env variable(s) from {env_file}[/dim]"
            )
        except FileNotFoundError as exc:
            err_console.print(
                Panel(f"[red]{exc}[/red]", title="Error", border_style="red")
            )
            raise typer.Exit(1) from None

    # Parse event
    try:
        parsed_event = parse_event(event)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        err_console.print(
            Panel(
                f"[red]Failed to parse event: {exc}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1) from None

    def _do_invoke() -> bool:
        """Execute one invocation. Returns True on success."""
        console.print("[bold cyan]▶ Invoking...[/bold cyan]")
        try:
            result, elapsed = invoke(
                handler_path=handler,
                event=parsed_event,
                timeout=timeout,
                memory=memory,
                region=region,
            )
        except LambdaTimeoutError as exc:
            err_console.print(
                Panel(
                    f"[red]LambdaTimeoutError: {exc}[/red]",
                    title="Error",
                    border_style="red",
                )
            )
            return False
        except (ValueError, ModuleNotFoundError, AttributeError) as exc:
            err_console.print(
                Panel(
                    f"[red]{type(exc).__name__}: {exc}[/red]",
                    title="Error",
                    border_style="red",
                )
            )
            return False
        except HandlerError as exc:
            err_console.print(
                Panel(
                    f"[red]{exc}[/red]",
                    title="Handler Error",
                    border_style="red",
                )
            )
            if traceback and exc.exc_traceback:
                err_console.print(
                    Panel(
                        exc.exc_traceback.rstrip(),
                        title="Traceback",
                        border_style="yellow",
                    )
                )
            elif not traceback:
                console.print("[dim]Use --traceback for full error details.[/dim]")
            return False
        except Exception as exc:
            err_console.print(
                Panel(
                    f"[red]{type(exc).__name__}: {exc}[/red]",
                    title="Error",
                    border_style="red",
                )
            )
            return False

        elapsed_ms = int(elapsed * 1000)
        if isinstance(result, (dict, list)):
            if pretty:
                formatted = json.dumps(result, indent=2, ensure_ascii=False)
                output = Syntax(formatted, "json", theme="monokai")
            else:
                output = json.dumps(result, ensure_ascii=False)
        else:
            output = str(result)
        console.print(
            Panel(output, title=f"Result ({elapsed_ms}ms)", border_style="green")
        )
        return True

    # Invoke
    success = _do_invoke()

    if not watch:
        if not success:
            raise typer.Exit(1)
        return

    # Watch mode
    from lambdarunner.loader import (
        invalidate_handler_cache,
        resolve_handler_file,
    )

    try:
        from watchfiles import watch as watch_files
    except ImportError:
        err_console.print(
            Panel(
                "[red]watchfiles is required for --watch mode.\n"
                "Install with: pip install lambdarunner[watch][/red]",
                title="Missing Dependency",
                border_style="red",
            )
        )
        raise typer.Exit(1) from None

    handler_file = resolve_handler_file(handler)
    console.print(
        f"\n[dim]Watching {handler_file} for changes... (Ctrl+C to stop)[/dim]"
    )

    try:
        for _changes in watch_files(handler_file):
            console.print("\n[dim]Change detected, re-invoking...[/dim]")
            invalidate_handler_cache(handler)
            _do_invoke()
            console.print(
                f"\n[dim]Watching {handler_file} for changes... (Ctrl+C to stop)[/dim]"
            )
    except KeyboardInterrupt:
        console.print("\n[dim]Watch mode stopped.[/dim]")


if __name__ == "__main__":
    app()
