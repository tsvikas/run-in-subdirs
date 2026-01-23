"""CLI for run_in_subdirs.

Run the same command in subdirectories.
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich import print  # noqa: A004

app = App(name="run-in-subdirs")
app.register_install_completion_command()


def get_header(subdir: Path) -> list[str]:
    """Create the header for each command."""
    return [f"┌─ 📂 {subdir}"]


def get_footer(status_code: int, duration: float) -> list[str]:
    """Create the footer for each command."""
    icon = "✅" if status_code == 0 else "❌"
    color = "green" if status_code == 0 else "red"
    return [
        f"└─ {icon} Done in {duration:.2f}s •[bold {color}]Exit: {status_code}[/]",
        "",
    ]


def format_line(line: str, *, is_err: bool = False) -> str:
    """Prepends the branch line."""
    prefix = "│  "
    if is_err:
        prefix = f"[on red]{prefix}[/]"
    return f"{prefix}{line.rstrip()}"


def run_sync(subdirs: list[Path], command_str: str) -> None:
    """Run commands sequentially with raw live output."""
    for subdir in subdirs:
        for head in get_header(subdir):
            print(head)

        start_time = time.perf_counter()

        # No formatting here: allows for true live output, TTY colors, and progress bars
        result = subprocess.run(command_str, cwd=subdir, shell=True, check=False)  # noqa: S602

        duration = time.perf_counter() - start_time
        for foot in get_footer(result.returncode, duration):
            print(foot)


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
    assert isinstance(process.returncode, int)  # noqa: S101
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

    print("\n".join(output_lines))


async def run_async_handler(subdirs: list[Path], command_str: str) -> None:
    """Run commands async."""
    tasks = [run_async_task(d, command_str) for d in subdirs]
    await asyncio.gather(*tasks)


@app.default()
def run_in_subdirs(
    command: list[str],
    /,
    *,
    run_async: Annotated[bool, Parameter("--async")] = False,
) -> int:
    """Run the same command in subdirectories with clean branch-style formatting.

    Parameters
    ----------
    command
        The command to run
    run_async
        Run in parallel
    """
    command_str = " ".join(command)
    if not command_str.strip():
        msg = "Must provide a command to run"
        raise ValueError(msg)

    subdirs = sorted([d for d in Path().iterdir() if d.is_dir()])

    if run_async:
        asyncio.run(run_async_handler(subdirs, command_str))
    else:
        run_sync(subdirs, command_str)

    return 0
