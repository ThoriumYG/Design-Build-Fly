# TUM Design/Build/Fly WS 2026/27

## Subteams

- [Aerodynamics](aerodynamics/)
- [Structure](structure/)
- [Propulsion](propulsion/)
- [Performance](performance/)

## Python Project Workflow

### Run style

- This project is organized as a multi-module Python project.
- Run executable modules from the repository root with module mode:
	- `python main.py`
	- `python -m performance.score_calculation`
	- `python -m performance.mission_sim`
	- `python -m aerodynamics.aero_coefficients`
- Running a file from inside its folder (e.g. `cd aerodynamics && python aero_coefficients.py`)
  does not work, because imports are relative to the repository root.

### Lowercase folder names (Windows / macOS users)

The subteam folders were renamed from `Aerodynamics`, `Performance`, `Propulsion`, `Structure`
and `Analysis_and_Optimization` to lowercase. Windows and macOS treat `Aerodynamics` and
`aerodynamics` as the same name by default, so pulling this change can go wrong there.

- Commit or stash all your changes before pulling the rename.
- After pulling, check that the folders are lowercase (`git ls-files` and your file explorer
  should both show `aerodynamics/`, not `Aerodynamics/`).
- If a folder still has the old name, or git shows files as deleted/untracked that you did
  not touch, the easiest fix is a fresh clone of the repository.
- If you have an open branch that still uses the old names, merge or rebase it onto the
  renamed branch instead of renaming folders by hand.

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
