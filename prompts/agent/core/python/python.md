# Python Style Guide

`uv` is used for dependency management, NOT `pip`. Read `uv.md`.

PY1. Model the domain with cohesive classes; expose behavior via instance, @classmethod, or @staticmethod.
PY2. Type-annotate every public parameter, return, attribute, and collection; pass `mypy –strict`.
PY3. At the top level of a module, allow only import statements, module-level constants (e.g., `_LOGGER`), and a main execution block (`if __name__ == "__main__":`)
PY4. Hide I/O, env, network, and secrets behind thin adapters injected into core logic.
PY5. One responsibility per class; prefer composition over inheritance.
PY6. Forbid global state; inject dependencies via constructors or function args.
PY7. Enforce PEP 8 and PEP 257 with ruff, black, and mypy; no style violations.
PY8. Use structured logging; never print; treat logs as 12-Factor event streams.
PY9. Source all configuration from environment variables. A .env file may be used for local development, loaded at application startup.
PY10. Provide docstrings and unit tests for every public path; maintain ≥ 80 % coverage.
PY12. Fail CI on unused imports, variables, or dead code.
PY13. Emit no TODOs, placeholders, or partial implementations—deliver complete, working code.
PY14. Do not define instance attributes outside of `__init__`
PY15. All source code must reside in the src/ directory. All tests must be located in the tests/ directory.
PY16. When running commands, ensure the local venv is running. Activate `.venv` if it is not. Never reinitialize the `venv` if it exists already.

PY17. ALL Docstrings MUST USE Google-style format. The Args: section is mandatory for any function or method with parameters. Each argument must include its type.
Example:
```python
"""Fetches records from the database.

Args:
user_id (int): The ID of the user to fetch.
include_inactive (bool): Flag to include inactive records.

Returns:
list[Record]: A list of database records.
"""
```

PY18. Require `python >=3.10`
PY19. Do not use `requirements.txt`, only use `pyprojects.toml`.
PY20. The project entry point is defined in the `[project.scripts]` section of pyproject.toml
PY21. The project uses setuptools as the build system, as specified in the `[build-system]` table of `pyproject.toml`.
PY22. Before running any project commands, ensure the virtual environment is activated. The virtual environment should be named `.venv` and located in the project's root directory.
PY23. Package Initialization: Every directory within src/ that contains Python source files MUST also contain an `__init__.py` file. This ensures the directory is treated as a regular package, which is critical for predictable module discovery by interpreters and static analysis tools.
PY24. Absolute Imports: All local project imports within the src directory MUST be absolute, starting from src (e.g., from `src.models.ship import Ship`). Do not use relative imports (e.g., `from .models.ship import Ship`) between different top-level modules.
PY25. `src` Layout and `pytest` Configuration: When using a `src` layout, `pytest` MUST be configured to recognize the `src` directory as a source root. Add the following configuration to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
pythonpath = [
  "src"
]
```
Abandoning this configuration in favor of modifying import paths is forbidden.

PY26. **Absolute Imports from Package Root**: With the `pythonpath` correctly set for a `src` layout (as per rule PY25), all local imports in both source code (`src/`) and tests (`tests/`) MUST be absolute from the package root, not the `src` directory.
    - Correct: `from saver.app import App`
    - Incorrect: `from src.saver.app import App`

PY27. **Correct Mock Patching**: When using `unittest.mock.patch`, the target string must point to the object where it is looked up, not where it is defined. If `module_a.py` contains from `module_b import Thing` and you are testing a function in `module_a` that uses `Thing`, you must patch `module_a.Thing`, not `module_b.Thing`.

PY28. **Type-Safe Mocking**: To ensure `mypy` compatibility, prefer using `@patch` decorators or context managers which produce correctly typed mock objects. Avoid manually re-assigning instance methods to a `MagicMock` instance in tests, as this obscures the type information from the static analyzer.

PY29. **ruff Configuration**: The ruff linter MUST be configured in the `[tool.ruff]` section of `pyproject.toml`. Core options like `line-length` reside at the top level of this table. Lint rule selections (e.g., `select`, `ignore`) MUST be placed within the `[tool.ruff.lint]` sub-table.
Correct Example:
```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B"]
```

PY30. **No Imports Within Functions**: Imports MUST NOT be placed inside functions or methods. All imports should be at the top level of the module to ensure clarity and avoid repeated import overhead. The only exception is for resolving circular dependencies, which must be explicitly justified and commented. This reinforces the principle of `PY3`.

PY31. **Quality Assurance Suite**:

Run this set of quality assurance tools after every change:

- Format the code with `black`.
- Lint the code with `ruff --fix`.
- Statically analyze the code with `mypy --strict`.
- Run all tests with pytest.
