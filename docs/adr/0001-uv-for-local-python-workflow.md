# UV for local Python workflow

UV is the canonical local Python workflow for this repository. The project uses UV to provide a reproducible Python interpreter, dependency environment, lockfile, and command runner so humans and agents do not depend on whatever `python`, `python3`, or `pytest` happens to be available on the shell `PATH`.

The canonical local test command is `uv run python -m unittest discover -s tests`. The existing tests use Python's standard `unittest` framework, so pytest is intentionally not a project dependency until the suite needs pytest-specific features.

Considered alternatives were ad hoc system Python commands, pyenv plus pip, pytest as an immediate dependency, and Docker-only execution. System Python is too fragile for agent handoffs, pyenv does not manage project dependencies, pytest is unnecessary for the current test suite, and Docker remains the expected PySpark/Jupyter runtime rather than the lightest path for local unit tests.
