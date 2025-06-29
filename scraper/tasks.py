"""
Development/CI scripts to be used with `invoke` (https://www.pyinvoke.org/).

The `invoke` command must be invoked from the scraper source root directory, i.e. the one containing
this file.
"""

import fileinput
import platform
import shutil
from pathlib import Path
from typing import Literal

from invoke import task
from invoke.context import Context
from invoke.exceptions import UnexpectedExit

_PIPTOOLS_PKG_NAME = "pip-tools"
"""
The 'pip-tools' package name to install during bootstrap.
"""
_PIPTOOLS_MIN_VERSION = "7.4.1"
"""
The minimum 'pip-tools' package version to install during bootstrap.
"""


@task
def analyze(context: Context) -> None:
    """
    Run all configured linters on all source files.

    If any of the linter commands fails (i.e. finds some issues), only the last failure is
    propagated.
    """

    def print_step(linter_name: str) -> None:
        print()
        print("*" * 80)
        print(f"Linting with {linter_name}")
        print("*" * 80)

    last_failure = None
    print_step("ruff")
    try:
        lint_ruff(context)
    except UnexpectedExit as e:
        last_failure = e

    print_step("mypy")
    try:
        lint_mypy(context)
    except UnexpectedExit as e:
        last_failure = e

    print_step("pylint")
    try:
        lint_pylint(context)
    except UnexpectedExit as e:
        last_failure = e

    if last_failure:
        raise last_failure
    print("No linter complained. Congratulations!")


@task
def bootstrap(context: Context) -> None:
    """
    Initialize the development environment.

    This installs all (dev) dependencies into the current virtualenv. After that, all other `invoke`
    scripts can be executed.
    """
    if platform.system() == "Windows":
        context.run(f"pip install -U {_PIPTOOLS_PKG_NAME}>={_PIPTOOLS_MIN_VERSION}")
    else:
        context.run(f"pip install -U '{_PIPTOOLS_PKG_NAME}>={_PIPTOOLS_MIN_VERSION}'")
    context.run("pip-compile -q --strip-extras --output-file=app-requirements.txt pyproject.toml")
    context.run(
        "pip-compile "
        "-q "
        "--strip-extras "
        "--extra=dev "
        "--constraint=app-requirements.txt "
        "--output-file=dev-requirements.txt "
        "pyproject.toml"
    )
    context.run("pip-sync dev-requirements.txt")


@task
def clean(context: Context) -> None:
    """
    Deletes local files that are generated during other tasks, e.g. build files and coverage
    information.
    """
    context.run("rm -rf coverage")


@task(name="format")
def autoformat(context: Context) -> None:
    """
    Auto-format all source files according to our formatting rules.
    """
    # Sort all imports (same as 'isort')
    context.run("python -m ruff check --select I --fix .")
    # Format all sources
    context.run("python -m ruff format .")


@task
def generate_schema(context: Context, dbname: Literal["routedb"]) -> None:
    """
    (Re-)Generate all files that are generated from the DBML definition.
    Files are generated for both the scraper and the mobile app. Existing files are overwritten.
    """
    dbmlfile = Path(f"../doc/sql_schemes/{dbname}/dbdiagram.io")
    template_dir = Path(f"../doc/sql_schemes/{dbname}/jinja_templates/")
    output_dir = Path(f"../doc/sql_schemes/{dbname}/generated/")

    output_dir.mkdir(parents=True, exist_ok=True)
    context.run(f"dinja {dbmlfile} {template_dir} {output_dir}")

    scraper = next(f for f in output_dir.iterdir() if f.suffix == ".py")
    shutil.copy(scraper, Path("src/trad/pipes/db_v1/"))

    mobileapp = next(f for f in output_dir.iterdir() if f.suffix == ".dart")
    shutil.copy(mobileapp, Path("../mobileapp/adapters/lib/src/storage/routedb/"))


@task
def lint_mypy(context: Context) -> None:
    """
    Run MyPy on all source files.
    """
    context.run("mypy .")


@task
def lint_pylint(context: Context) -> None:
    """
    Run PyLint on all source files.
    """
    context.run("python -m pylint src test/trad test/integration")


@task
def lint_ruff(context: Context) -> None:
    """
    Run ruff on all source files.
    """
    context.run("python -m ruff check .")


@task
def run(context: Context) -> None:
    """
    Run the scraper application.
    """
    Path("routedb").mkdir(parents=True)
    with context.cd("src"):
        context.run("python scraper.py ../routedb")


@task
def test(context: Context) -> None:
    """
    Run all unit tests for the scraper application and collect coverage data.
    """
    # Explicitly include all source directories to also capture unimported source files
    dirnames = ",".join({str(f.parent) for f in Path("src").glob("**/*.py")})
    setpythonpath = "set PYTHONPATH=src &&" if platform.system() == "Windows" else "PYTHONPATH=src"
    context.run(f"{setpythonpath} coverage run --source '{dirnames}' -m pytest test")


@task
def coverage(context: Context) -> None:
    """
    Calculates test coverage for the whole scraper application. 'invoke test' must have been
    executed before.
    """
    context.run("coverage html")


@task
def upgrade(context: Context) -> None:
    """
    Upgrade all dependencies to their most current (allowed) versions.

    This recreates the requirements.txt files and upgrades all dependency packages in the current
    virtual env.
    """
    print("Upgrading app requirements...")
    context.run(
        "pip-compile -q --strip-extras --upgrade --output-file=app-requirements.txt pyproject.toml"
    )
    print("Upgrading dev requirements...")
    context.run(
        "pip-compile "
        "-q "
        "--strip-extras "
        "--upgrade "
        "--extra=dev "
        "--constraint=app-requirements.txt "
        "--output-file=dev-requirements.txt "
        "pyproject.toml"
    )
    print("Syncing environment...")
    context.run("pip-sync dev-requirements.txt")


@task
def version(_context: Context, version: str) -> None:
    """
    Set the scraper application version to be `version`, which should be of the format
    "MAJOR.MINOR.PATCH" (e.g. "1.2.3") and must match the Python Software Version Specification
    (https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers)
    """

    def replace_line_in_file(file: Path, line_head: str, replacement: str) -> None:
        """
        Replace all lines starting with `line_head` with `replacement` within the given `file`.
        """
        with fileinput.input(file, inplace=True) as f:
            for line in f:
                if line.startswith(line_head):
                    print(replacement)
                else:
                    print(line, end="")

    # Update appmeta.py (source code)
    replace_line_in_file(
        Path("src", "trad", "crosscuttings", "appmeta.py"),
        "APPLICATION_VERSION: Final = ",
        f'APPLICATION_VERSION: Final = "{version}"',
    )
    # Update pyproject.toml (meta data)
    replace_line_in_file(
        Path("pyproject.toml"),
        "version = ",
        f'version = "{version}"',
    )
