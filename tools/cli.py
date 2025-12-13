"""Command-line interface for AI Arr Control.

Provides convenient developer and operational commands:
- `run` starts the ASGI server using uvicorn
- `check` runs an in-process smoke-check (tools.check_runtime)
- `initdb` initializes the database
- `tests` runs the test suite
- `version` prints the project version

This script is importable and also registered as a console script.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from typing import Optional

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
def run(host: str, port: int, reload: bool, log_level: str) -> None:
    """Run the application using uvicorn (requires uvicorn installed)."""
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port), "--log-level", log_level]
    if reload:
        cmd.append("--reload")

    click.echo(f"Starting server: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Server exited with error: {e}")
        raise SystemExit(e.returncode)


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
    # Keep static for now; update to read from pyproject or package metadata if needed
    click.echo("ai-arr-control 0.3.0")


if __name__ == "__main__":
    main()
