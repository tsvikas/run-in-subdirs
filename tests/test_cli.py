from pathlib import Path

import pytest
from colorama import Back, Style

from run_in_subdirs import __version__, cli
from run_in_subdirs.cli import (
    EX_NOINPUT,
    EX_NOPERM,
    EX_SOFTWARE,
    EX_UNAVAILABLE,
    app,
    format_line,
    main,
)
from run_in_subdirs.cli import run_in_subdirs as run_in_subdirs_fn


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        app("--version")
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_no_command_raises_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        app([])
    assert exc_info.value.code == 2


class TestFormatLine:
    def test_stderr_line_has_red_background(self) -> None:
        """Stderr lines should be formatted with a red background prefix."""
        result = format_line("error message", is_err=True)
        assert "│  " in result
        assert Back.RED in result
        assert "error message" in result
        assert Style.RESET_ALL in result


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create an isolated workspace with subdirectories for testing."""
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "file1.txt").write_text("alpha content")

    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "file2.txt").write_text("beta content")

    (tmp_path / "gamma").mkdir()
    (tmp_path / "gamma" / "nested").mkdir()
    (tmp_path / "gamma" / "nested" / "deep.txt").write_text("deep content")

    return tmp_path


class TestRunSync:
    def test_ls_lists_files_in_subdirs(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["ls"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert "alpha" in output
        assert "beta" in output
        assert "gamma" in output
        assert "file1.txt" in output
        assert "file2.txt" in output
        assert "nested" in output

    def test_echo_runs_in_each_subdir(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["echo", "hello"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert output.count("hello") == 3

    def test_pwd_shows_correct_directories(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["pwd"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert str(workspace / "alpha") in output
        assert str(workspace / "beta") in output
        assert str(workspace / "gamma") in output

    def test_exit_code_shown_in_output(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["ls"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert "Exit: 0" in output

    def test_failed_command_shows_nonzero_exit(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["ls", "nonexistent_file"])
        assert exc_info.value.code == 0  # app itself succeeds

        output = capfd.readouterr().out
        assert "Exit: " in output


class TestDepth:
    def test_depth_2_runs_only_in_nested_dirs(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--depth", "2", "pwd"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert str(workspace / "gamma" / "nested") in output
        assert "Summary: 1/1 succeeded" in output

    def test_depth_beyond_tree_runs_nothing(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--depth", "3", "pwd"])
        assert exc_info.value.code == 0
        assert capfd.readouterr().out == ""

    def test_depth_zero_is_invalid(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            app(["--depth", "0", "pwd"])
        assert exc_info.value.code == 2


class TestHidden:
    @pytest.fixture
    def hidden_workspace(self, workspace: Path) -> Path:
        """Extend `workspace` with hidden directories at depth 1 and 2."""
        (workspace / ".hidden").mkdir()
        (workspace / "alpha" / ".git").mkdir()
        return workspace

    def test_default_skips_hidden_dirs(
        self,
        hidden_workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(hidden_workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["pwd"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert ".hidden" not in output
        assert "Summary: 3/3 succeeded" in output

    def test_depth_2_skips_nested_hidden_dirs(
        self,
        hidden_workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(hidden_workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--depth", "2", "pwd"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert ".git" not in output
        assert "Summary: 1/1 succeeded" in output

    def test_hidden_includes_nested_hidden_dirs(
        self,
        hidden_workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(hidden_workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--hidden", "--depth", "2", "pwd"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert str(hidden_workspace / "alpha" / ".git") in output
        assert str(hidden_workspace / "gamma" / "nested") in output
        assert "Summary: 2/2 succeeded" in output


class TestRunAsync:
    def test_async_ls_lists_files_in_subdirs(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--async", "ls"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert "alpha" in output
        assert "beta" in output
        assert "gamma" in output
        assert "file1.txt" in output
        assert "file2.txt" in output

    def test_async_echo_runs_in_each_subdir(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--async", "echo", "hello"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert output.count("hello") == 3

    def test_async_pwd_shows_correct_directories(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--async", "pwd"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert str(workspace / "alpha") in output
        assert str(workspace / "beta") in output
        assert str(workspace / "gamma") in output

    def test_async_stderr_only_is_captured(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Async mode should capture stderr even when there is no stdout."""
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["--async", "ls", "nonexistent_unique_file"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        # stderr from ls should be captured and displayed in the output
        assert "nonexistent_unique_file" in output

    def test_async_stdout_and_stderr_both_captured(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Async mode should capture and display both stdout and stderr."""
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(
                [
                    "--async",
                    "--",
                    "bash",
                    "-c",
                    "echo stdout_msg && echo stderr_msg >&2",
                ]
            )
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert "stdout_msg" in output
        assert "stderr_msg" in output


class TestSummary:
    def test_summary_header_and_all_dirs_listed(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit):
            app(["echo", "hello"])

        output = capfd.readouterr().out
        assert "Summary: 3/3 succeeded" in output
        summary = output.split("Summary:")[1]
        assert "alpha" in summary
        assert "beta" in summary
        assert "gamma" in summary

    def test_summary_marks_failed_dirs(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit):
            app(["ls", "nonexistent_file"])

        output = capfd.readouterr().out
        summary = output.split("Summary:")[1]
        assert "❌" in summary

    def test_no_summary_when_no_subdirs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit):
            app(["echo", "hi"])

        output = capfd.readouterr().out
        assert "Summary:" not in output


class TestEdgeCases:
    def test_no_subdirs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Running in a directory with no subdirectories should not fail."""
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit) as exc_info:
            app(["echo", "hello"])
        assert exc_info.value.code == 0

    def test_ignores_files(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Should only process directories, not files."""
        (tmp_path / "subdir").mkdir()
        (tmp_path / "regular_file.txt").write_text("not a dir")
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            app(["pwd"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert "subdir" in output
        assert output.count("📂") == 1

    def test_command_with_shell_features(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Commands with shell features like pipes should work."""
        monkeypatch.chdir(workspace)
        with pytest.raises(SystemExit) as exc_info:
            app(["echo", "hello", "|", "cat"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert output.count("hello") == 3

    def test_empty_command_raises_value_error(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Calling run_in_subdirs with an empty command list raises ValueError."""
        monkeypatch.chdir(workspace)
        with pytest.raises(ValueError, match="Must provide a command to run"):
            run_in_subdirs_fn([])


def test_main_usage_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--not-an-option"])
    # Cyclopts >=5 exits 2 on invalid usage, as argparse, click and clap do.
    # sysexits(3) would say 64, but 2 is the far wider convention.
    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (FileNotFoundError("missing.txt"), EX_NOINPUT),
        (PermissionError("locked.txt"), EX_NOPERM),
        (ConnectionError("down"), EX_UNAVAILABLE),
        # a subclass lands on its parent's code
        (ConnectionRefusedError("refused"), EX_UNAVAILABLE),
    ],
)
def test_main_reported_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
    code: int,
) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise error

    monkeypatch.setattr(cli, "app", explode)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == code
    assert capsys.readouterr().err == f"error: {error}\n"


def test_main_unhandled_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # Accept the call that `main` makes, so that the RuntimeError below is what
    # reaches it, rather than a TypeError over the signature.
    def explode(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError

    monkeypatch.setattr(cli, "app", explode)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == EX_SOFTWARE
