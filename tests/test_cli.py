from pathlib import Path

import pytest

from run_in_subdirs import __version__
from run_in_subdirs.cli import app


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        app("--version")
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_no_command_raises_error() -> None:
    with pytest.raises(ValueError, match="Must provide a command to run"):
        app([""])


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
            app(["echo hello | cat"])
        assert exc_info.value.code == 0

        output = capfd.readouterr().out
        assert output.count("hello") == 3
