"""CLI for run_in_subdirs.

Currently, a placeholder until the real CLI will be added.
"""

from typing import Annotated

import cyclopts.types
from cyclopts import App, Parameter

app = App(name="run-in-subdirs")
app.register_install_completion_command()


@app.default()
def do_something(
    target: cyclopts.types.File,
    /,
    *,
    code: Annotated[str, Parameter(alias="-c")] = "CODE",
) -> int:
    """Do something.

    Parameters
    ----------
    target
        Path to the target file
    code
        The code to use
    """
    print(target, code)
    return 0
