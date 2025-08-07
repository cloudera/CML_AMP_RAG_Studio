# `uv` rules

UV1. Manage all project dependencies using `uv` through the `pyproject.toml` file. Always commit the uv.lock file to ensure reproducible builds.
UV2. ALWAYS `uv` directly, using the default `.venv`. DO NOT use `uv pip`.
UV3. Add new packages with `uv add`. Use `uv sync` if you want to ensure things are up to date.
UV4. Local, editable dependencies are defined in the `[tool.uv.sources]` table in `pyproject.toml`. This is the standard for including local packages in the project.
UV5. Use `uv add <package>` to add a new dependency and `uv sync` to install dependencies listed in `uv.lock`.
UV6. Development-specific dependencies (e.g., `pytest`, `mypy`, `ruff`, `black`) MUST be defined in the `[project.optional-dependencies.dev]` table. Add them using the command `uv add --dev-dependency <package>` or `uv add -G dev <package>`.
UV7. When setting up a New Project, install the dev tools immediately: `pytest`, `black`, `ruff`, `mypy`, `setuptools`
