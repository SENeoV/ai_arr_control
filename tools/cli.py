"""Command-line interface for AI Arr Control.

Provides convenient developer and operational commands:
- `run` starts the ASGI server using uvicorn
- `check` runs an in-process smoke-check (tools.check_runtime)
- `initdb` initializes the database
- `tests` runs the test suite
- `version` prints the project version
- `stop` stops a running detached server
- `status` checks if the server is running

This script is importable and also registered as a console script entry point
in pyproject.toml.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from typing import Optional
import os
import signal
from pathlib import Path

import click

from tools.check_runtime import main as check_main


@click.group()
def main() -> None:
    """AI Arr Control CLI."""


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind the server to")
@click.option("--port", default=8000, show_default=True, help="Port to bind the server to")
@click.option("--reload/--no-reload", default=False, show_default=True, help="Enable uvicorn reload mode")
@click.option("--log-level", default="info", show_default=True, help="Uvicorn log level")
@click.option("--detach/--no-detach", default=False, show_default=True, help="Run server detached (background)")
def run(host: str, port: int, reload: bool, log_level: str, detach: bool) -> None:
    """Run the application using uvicorn (requires uvicorn installed)."""
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port), "--log-level", log_level]
    if reload:
        cmd.append("--reload")

    click.echo(f"Starting server: {' '.join(cmd)}")
    pidfile = Path(".ai_arr_control.pid")
    logfile = Path("ai_arr_control.log")

    if not detach:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            click.echo(f"Server exited with error: {e}")
            raise SystemExit(e.returncode)
        return

    # Detached mode: spawn background process and write PID file
    with open(logfile, "ab") as out:
        proc = subprocess.Popen(cmd, stdout=out, stderr=out)
        pid = proc.pid
        pidfile.write_text(str(pid))
        click.echo(f"Server started in background (pid={pid}), logs -> {logfile}")


@main.command()
def check() -> None:
    """Run in-process runtime smoke-check (no external server required)."""
    check_main()


@main.command()
def initdb() -> None:
    """Initialize the database (creates tables)."""
    try:
        # Import here to avoid startup side-effects when importing the CLI
        from db.session import init_db

        asyncio.run(init_db())
        click.echo("Database initialized successfully")
    except Exception as e:
        click.echo(f"Failed to initialize database: {e}")
        raise SystemExit(1)


@main.command()
def stop() -> None:
    """Stop a previously started detached server (if PID file exists)."""
    pidfile = Path(".ai_arr_control.pid")
    if not pidfile.exists():
        click.echo("No PID file found; server may not be running")
        raise SystemExit(1)

    pid = int(pidfile.read_text().strip())
    click.echo(f"Stopping process {pid}...")
    try:
        # Try graceful termination
        os.kill(pid, signal.SIGTERM)
    except Exception:
        # Fallback to taskkill on Windows
        if sys.platform.startswith("win"):
            subprocess.run(["taskkill", "/F", "/PID", str(pid)])
    finally:
        try:
            pidfile.unlink()
        except Exception:
            pass


@main.command()
def status() -> None:
    """Show status of detached server (based on PID file)."""
    pidfile = Path(".ai_arr_control.pid")
    if not pidfile.exists():
        click.echo("No PID file found; server is not running (or not started via CLI)")
        raise SystemExit(0)

    pid = int(pidfile.read_text().strip())
    try:
        # Check if process exists
        os.kill(pid, 0)
        click.echo(f"Process {pid} is running")
    except OSError:
        click.echo(f"Process {pid} is not running")


@main.command()
def tests() -> None:
    """Run the test suite using pytest."""
    cmd = [sys.executable, "-m", "pytest"]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Tests failed: {e}")
        raise SystemExit(e.returncode)


@main.command()
def version() -> None:
    """Print project version."""
    click.echo("ai-arr-control 0.4.0")


if __name__ == "__main__":
    main()
