# TUM Design/Build/Fly WS 2026/27

## Subteams

- [Aerodynamics](Aerodynamics/)
- [Structure](Structure/)
- [Propulsion](Propulsion/)
- [Performance](Performance/)

## Python Project Workflow

### Run style

- This project is organized as a multi-module Python project.
- Run executable modules from the repository root with module mode:
	- `python -m Performance.score_calculation`
	- `python -m Performance.mission_sim`

### VS Code Run/Debug

- Use the launch configurations in `.vscode/launch.json`:
	- `Run score_calculation (module)`
	- `Run mission_sim (module)`
- These use module execution, so no `sys.path` hacks are needed in source files.

### Tests

- Tests live in `tests/` and are run with pytest.
- Run from repo root:
	- `python -m pytest`

### Tooling

The project uses `pyproject.toml` to centralize config for formatting, linting, typing, and tests.

- `pytest`: runs automated tests and reports failures.
- `ruff`: fast linter that catches common bugs and style issues.
- `black`: auto-formats Python code to a consistent style.
- `mypy`: static type checker that catches interface/type mismatches before runtime.

Suggested setup in your virtual environment:

- `python -m pip install -e .[dev]`
