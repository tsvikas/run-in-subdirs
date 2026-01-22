import importlib.metadata

import run_in_subdirs


def test_version() -> None:
    assert importlib.metadata.version("run_in_subdirs") == run_in_subdirs.__version__
