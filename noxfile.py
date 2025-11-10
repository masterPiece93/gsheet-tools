"""Nox configuration file for automating testing tasks.

This script defines the Nox sessions for testing the project across multiple
Python versions. It uses `pytest` as the test runner and includes support for
generating test coverage reports.

Attributes:
    python_versions (list): A list of Python versions to test against.
"""

import nox

# Define the Python versions you want to test with
# NOTE: Use pyenv for maintaining multiple Python versions
python_versions = ["3.10", "3.11", "3.12", "3.13"]

@nox.session(python=python_versions)
def test_python_versions(session: nox.Session):
    """Run tests across multiple Python versions.

    This session installs the project, along with the required dependencies
    for testing, and then runs the test suite using `pytest`.

    Args:
        session (nox.Session): The Nox session object.
    """
    # Install Self
    session.install(f".")
    # Install additional dependencies required for testing
    session.install("pytest")  # Pytest: Test runner
    session.install("pytest-cov")
    # Run Pytest
    session.run("pytest")
