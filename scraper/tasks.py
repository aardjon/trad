"""
Development/CI scripts to be used with `invoke` (https://www.pyinvoke.org/).

The `invoke` command must be invoked from the scraper source root directory, i.e. the one containing
this file.
"""

from invoke import task
from invoke.context import Context

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
    Run the configured linters on all source files.
    """
    context.run("echo 'Not yet available - coming soon!'")


@task
def bootstrap(context: Context) -> None:
    """
    Initialize the development environment.

    This installs all (dev) dependencies into the current virtualenv. After that, all other `invoke`
    scripts can be executed.
    """
    context.run(f"pip install -U '{_PIPTOOLS_PKG_NAME}>={_PIPTOOLS_MIN_VERSION}'")
    context.run(
        "pip-compile "
        "-q "
        "--strip-extras "
        "--output-file=app-requirements.txt "
        "pyproject.toml"
    )
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
def run(context: Context) -> None:
    """
    Run the scraper application.
    """
    with context.cd("src"):
        context.run("python app.py")


@task
def test(context: Context) -> None:
    """
    Run all unit tests for the scraper application.
    """
    context.run("PYTHONPATH=src pytest test")


@task
def upgrade(context: Context) -> None:
    """
    Upgrade all dependencies to their most current (allowed) versions.

    This recreates the requirements.txt files and upgrades all dependency packages in the current
    virtual env.
    """
    print("Upgrading app requirements...")
    context.run(
        "pip-compile "
        "-q "
        "--strip-extras "
        "--upgrade "
        "--output-file=app-requirements.txt "
        "pyproject.toml"
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
