# run-in-subdirs

[![Tests][tests-badge]][tests-link]
[![uv][uv-badge]][uv-link]
[![Ruff][ruff-badge]][ruff-link]
\
[![Made Using tsvikas/python-template][template-badge]][template-link]
[![GitHub Discussion][github-discussions-badge]][github-discussions-link]
[![PRs Welcome][prs-welcome-badge]][prs-welcome-link]

## Overview

Run the same command across all subdirectories with clean, branch-style formatted output. Useful for managing multiple git repositories, running batch operations, or any task that needs to be repeated across sibling directories.

## Features

- **Branch-style output** - Clear visual hierarchy showing which directory each output belongs to
- **Parallel execution** - Run commands concurrently with `--async` for faster batch operations
- **Exit status tracking** - Shows exit code and duration for each directory
- **stderr highlighting** - Errors are visually distinguished from stdout
- **Shell completion** - Tab completion for bash, zsh, and fish

## Install

```bash
# Using pipx
pipx install git+https://github.com/tsvikas/run-in-subdirs.git

# Using uv
uv tool install git+https://github.com/tsvikas/run-in-subdirs.git
```

## Usage

```bash
# Run a command in all subdirectories (sequential)
run-in-subdirs git status

# Run in parallel for faster execution
run-in-subdirs --async git fetch

# Commands with flags need to use --
run-in-subdirs -- ls -la
```

### Example Output

```
┌─ 📂 project-a
│  On branch main
│  nothing to commit, working tree clean
└─ ✅ Done in 0.05s • Exit: 0

┌─ 📂 project-b
│  On branch feature/new-thing
│  Changes not staged for commit:
│    modified:   src/app.py
└─ ✅ Done in 0.04s • Exit: 0
```

### Options

| Option                 | Description                                              |
| ---------------------- | -------------------------------------------------------- |
| `--async`              | Run commands in parallel (output buffered per directory) |
| `--help`               | Show help message                                        |
| `--version`            | Show version                                             |
| `--install-completion` | Install shell completion                                 |

## Contributing

Interested in contributing?
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guideline.

[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]: https://github.com/tsvikas/run-in-subdirs/discussions
[prs-welcome-badge]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
[prs-welcome-link]: https://opensource.guide/how-to-contribute/
[ruff-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff-link]: https://github.com/astral-sh/ruff
[template-badge]: https://img.shields.io/badge/%F0%9F%9A%80_Made_Using-tsvikas%2Fpython--template-gold
[template-link]: https://github.com/tsvikas/python-template
[tests-badge]: https://github.com/tsvikas/run-in-subdirs/actions/workflows/ci.yml/badge.svg
[tests-link]: https://github.com/tsvikas/run-in-subdirs/actions/workflows/ci.yml
[uv-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
[uv-link]: https://github.com/astral-sh/uv
