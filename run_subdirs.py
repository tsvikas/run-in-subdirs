# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "typer>=0.21.1",
# ]
# ///
"""Run the same command in subdirectories."""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(add_completion=False, help="Run commands in subdirectories.")


def get_header(subdir: Path) -> list[str]:
    """Create the header for each command."""
    return [f"┌─ 📂 {subdir}"]


def get_footer(status_code: int, duration: float) -> list[str]:
    """Create the footer for each command."""
    icon = "✅" if status_code == 0 else "❌"
    color = typer.colors.GREEN if status_code == 0 else typer.colors.RED
    base_text = f"└─ {icon} Done in {duration:.2f}s • "
    exit_status = typer.style(f"Exit: {status_code}", fg=color, bold=True)
    return [f"{base_text}{exit_status}", ""]


def format_line(line: str, *, is_err: bool = False) -> str:
    """Prepends the branch line."""
    prefix = "│  "
    if is_err:
        prefix = typer.style(prefix, bg=typer.colors.RED)
    return f"{prefix}{line.rstrip()}"


def run_sync(subdirs: list[Path], command_str: str) -> None:
    """Run commands sequentially with raw live output."""
    for subdir in subdirs:
        for head in get_header(subdir):
            typer.echo(head)

        start_time = time.perf_counter()

        # No formatting here: allows for true live output, TTY colors, and progress bars
        result = subprocess.run(command_str, cwd=subdir, shell=True, check=False)  # noqa: S602

        duration = time.perf_counter() - start_time
        for foot in get_footer(result.returncode, duration):
            typer.echo(foot)


async def run_async_task(subdir: Path, command_str: str) -> None:
    """Run command asynchronously and applies branch formatting to buffered output."""
    start_time = time.perf_counter()

    process = await asyncio.create_subprocess_shell(
        command_str,
        cwd=subdir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    duration = time.perf_counter() - start_time

    output_lines = get_header(subdir)

    # Process stdout
    if stdout:
        for line in stdout.decode().splitlines():
            output_lines.append(format_line(line, is_err=False))

    # Process stderr with a different vertical marker
    if stderr:
        for line in stderr.decode().splitlines():
            output_lines.append(format_line(line, is_err=True))

    output_lines.extend(get_footer(process.returncode, duration))

    typer.echo("\n".join(output_lines))


async def run_async_handler(subdirs: list[Path], command_str: str) -> None:
    """Run commands async."""
    tasks = [run_async_task(d, command_str) for d in subdirs]
    await asyncio.gather(*tasks)


@app.command()
def main(
    command: Annotated[list[str], typer.Argument(help="The command to run")],
    *,
    run_async: Annotated[bool, typer.Option("--async", help="Run in parallel")] = False,
) -> None:
    """Run the same command in subdirectories with clean branch-style formatting."""
    subdirs = sorted([d for d in Path().iterdir() if d.is_dir()])
    command_str = " ".join(command)

    if not subdirs:
        typer.secho("No subdirectories found.", fg=typer.colors.YELLOW)
        raise typer.Exit

    if run_async:
        asyncio.run(run_async_handler(subdirs, command_str))
    else:
        run_sync(subdirs, command_str)


if __name__ == "__main__":
    app()
