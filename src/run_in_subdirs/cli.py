"""CLI for run_in_subdirs.

Run the same command in subdirectories.
"""

import asyncio
import shlex
import subprocess
import sys
import time
import traceback
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, NoReturn

from colorama import Back, Fore, Style, just_fix_windows_console
from cyclopts import App, Parameter, validators

just_fix_windows_console()

app = App(name="run-in-subdirs")
app.register_install_completion_command()


def get_header(subdir: Path) -> list[str]:
    """Create the header for each command."""
    return [f"┌─ 📂 {subdir}"]


def get_footer(status_code: int, duration: float) -> list[str]:
    """Create the footer for each command."""
    icon = "✅" if status_code == 0 else "❌"
    color = Fore.GREEN if status_code == 0 else Fore.RED
    exit_text = f"{Style.BRIGHT}{color}Exit: {status_code}{Style.RESET_ALL}"
    return [
        f"└─ {icon} Done in {duration:.2f}s • {exit_text}",
        "",
    ]


def format_line(line: str, *, is_err: bool = False) -> str:
    """Prepends the branch line."""
    prefix = "│  "
    if is_err:
        prefix = f"{Back.RED}{prefix}{Style.RESET_ALL}"
    return f"{prefix}{line.rstrip()}"


def find_subdirs(root: Path, depth: int) -> list[Path]:
    """Find the directories exactly `depth` levels below `root`, sorted."""
    level = [root]
    for _ in range(depth):
        level = [child for d in level for child in d.iterdir() if child.is_dir()]
    return sorted(level)


def run_sync(subdirs: list[Path], command_str: str) -> list[tuple[Path, int, float]]:
    """Run commands sequentially with raw live output."""
    results: list[tuple[Path, int, float]] = []
    for subdir in subdirs:
        for head in get_header(subdir):
            print(head)

        start_time = time.perf_counter()

        # No formatting here: allows for true live output, TTY colors, and progress bars
        result = subprocess.run(command_str, cwd=subdir, shell=True, check=False)  # noqa: S602

        duration = time.perf_counter() - start_time
        for foot in get_footer(result.returncode, duration):
            print(foot)
        results.append((subdir, result.returncode, duration))
    return results


async def read_stream(
    stream: asyncio.StreamReader,
    captured: list[tuple[float, bool, str]],
    *,
    is_err: bool,
) -> None:
    """Read lines from a stream, tagging each with an arrival timestamp."""
    while True:
        raw = await stream.readline()
        if not raw:
            break
        captured.append((time.perf_counter(), is_err, raw.decode().rstrip("\n")))


async def run_async_task(subdir: Path, command_str: str) -> tuple[Path, int, float]:
    """Run command asynchronously and applies branch formatting to buffered output."""
    start_time = time.perf_counter()

    process = await asyncio.create_subprocess_shell(
        command_str,
        cwd=subdir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert process.stdout is not None  # noqa: S101
    assert process.stderr is not None  # noqa: S101

    # Interleave stdout/stderr in arrival order; order is approximate (kernel
    # buffering and asyncio scheduling), but preserves the is_err distinction.
    captured: list[tuple[float, bool, str]] = []
    await asyncio.gather(
        read_stream(process.stdout, captured, is_err=False),
        read_stream(process.stderr, captured, is_err=True),
    )
    await process.wait()
    assert isinstance(process.returncode, int)  # noqa: S101
    duration = time.perf_counter() - start_time

    output_lines = get_header(subdir)
    for _, is_err, line in sorted(captured, key=lambda item: item[0]):
        output_lines.append(format_line(line, is_err=is_err))
    output_lines.extend(get_footer(process.returncode, duration))

    print("\n".join(output_lines))
    return subdir, process.returncode, duration


async def run_async_handler(
    subdirs: list[Path], command_str: str
) -> list[tuple[Path, int, float]]:
    """Run commands async."""
    tasks = [run_async_task(d, command_str) for d in subdirs]
    return await asyncio.gather(*tasks)


def print_summary(results: list[tuple[Path, int, float]]) -> None:
    """Print a compact one-line-per-dir summary of all runs."""
    if not results:
        return
    succeeded = sum(1 for _, code, _ in results if code == 0)
    total = len(results)
    header_color = Fore.GREEN if succeeded == total else Fore.RED
    print(
        f"{Style.BRIGHT}{header_color}Summary: "
        f"{succeeded}/{total} succeeded{Style.RESET_ALL}"
    )
    for subdir, code, _duration in results:
        icon = "✅" if code == 0 else "❌"
        print(f"{icon} {subdir}")


# --- Commands -------------------------------------------------------------------------
# This is the part to replace. `@app.default()` runs when no subcommand is
# given, so switch these to `@app.command()` once there is more than one, and
# keep the exit codes each returns listed in its docstring.
@app.default()
def run_in_subdirs(
    command: list[str],
    /,
    *,
    run_async: Annotated[bool, Parameter("--async")] = False,
    depth: Annotated[int, Parameter(validator=validators.Number(gte=1))] = 1,
) -> int:
    """Run the same command in subdirectories with clean branch-style formatting.

    Args:
        command: The command to run
        run_async: Run in parallel
        depth: Run only in directories exactly this many levels deep

    Returns:
        The process exit code.

    Exit Codes:
        0: Success, even if the command failed in some subdirectories.
        2: Invalid usage.
        64-78: Reserved, an internal failure.
        129-159: Reserved, terminated by signal N, as 128 + N.
    """
    command_str = shlex.join(command)
    if not command_str.strip():
        msg = "Must provide a command to run"
        raise ValueError(msg)

    subdirs = find_subdirs(Path(), depth)

    if run_async:
        results = asyncio.run(run_async_handler(subdirs, command_str))
    else:
        results = run_sync(subdirs, command_str)

    print_summary(results)

    return 0


# --- Entry point ----------------------------------------------------------------------
# Maps the commands above onto exit codes, and is what `[project.scripts]` and
# `__main__` both call.

# Cyclopts itself exits 2 on invalid usage. These are sysexits(3) codes.
# `os.EX_*` holds the same values but only exists on Unix, so they are inlined
# to keep the CLI importable on Windows.
EX_NOINPUT = 66
EX_UNAVAILABLE = 69
EX_SOFTWARE = 70
EX_NOPERM = 77


def _fail(exc: Exception, code: int) -> NoReturn:
    """Report `exc` on stderr and exit with `code`."""
    print(f"error: {exc}", file=sys.stderr)
    sys.exit(code)


def main(tokens: Sequence[str] | None = None) -> None:
    """Run the CLI, reporting failures and mapping them onto exit codes.

    Args:
        tokens: The command line to parse. Defaults to `sys.argv[1:]`.
    """
    try:
        # `tokens` is a parameter so that tests can pass a command line here.
        # Under pytest, a bare `app()` warns, since it would parse pytest's own
        # argv, and a test that does so passes while testing nothing.
        app(tokens)
    # Nothing reports the errors below, so without `_fail` the CLI would exit on
    # a bare code and no output. Match on the exception rather than on
    # `type(exc)`, so that subclasses such as ConnectionRefusedError still land
    # on the right code. Specific OSError subclasses must precede any bare
    # `except OSError`, which would otherwise swallow them.
    except FileNotFoundError as exc:
        _fail(exc, EX_NOINPUT)
    except PermissionError as exc:
        _fail(exc, EX_NOPERM)
    except ConnectionError as exc:
        _fail(exc, EX_UNAVAILABLE)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(EX_SOFTWARE)
