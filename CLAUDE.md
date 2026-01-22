# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI tool that runs the same command across all subdirectories of the current directory. Uses `cyclopts` for CLI parsing and `rich` for formatted output.

## Common Commands

```bash
# Setup after cloning
uv run just prepare

# Run tests
uv run pytest
uv run just test              # stricter: reinstalls package, exact deps

# Run a single test
uv run pytest tests/test_cli.py::test_version

# Format and lint (quick)
uv run just quick-tools       # or: uv run just q

# Format (full)
uv run just format            # or: uv run just f

# Lint (full)
uv run just lint              # or: uv run just l

# Type checking
uv run mypy
uv run ty check

# Run the CLI
uv run run-in-subdirs --help
uv run run-in-subdirs <command>
uv run run-in-subdirs --async <command>   # parallel execution
```

## Architecture

- `src/run_in_subdirs/cli.py` - Main CLI implementation using cyclopts `App`. Contains:
  - `run_in_subdirs()` - Main entry point, finds subdirs and delegates to sync/async runners
  - `run_sync()` - Sequential execution with live TTY output
  - `run_async_handler()` / `run_async_task()` - Parallel execution with buffered output
- `src/run_in_subdirs/__main__.py` - Enables `python -m run_in_subdirs`
- Entry point: `run-in-subdirs` CLI command defined in `pyproject.toml`

## Code Style

- Python 3.10+ with strict typing (mypy strict mode)
- Ruff for linting with nearly all rules enabled
- Google-style docstrings
- Tests in `tests/` use pytest; doctests enabled in source files
