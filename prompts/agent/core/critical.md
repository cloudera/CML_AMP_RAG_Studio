# Critical Requirements

C1. **No Incomplete Code**: You must deliver a complete and functional application. Do not use placeholders, TODO comments, or stubbed-out functions that are not fully implemented.

C2. **Strict Adherence to Standards**: All code and project structure must strictly conform to the specifications in python.md and pyproject.toml. No style violations or structural deviations are permitted.

C3. **Mandatory and Passing Tests**: All new code must be accompanied by corresponding unit and integration tests. All tests, both new and existing, must pass before the task is considered complete.

C4. **Secure Configuration**: Do not hardcode any secrets such as API keys, tokens, or passwords in the source code. All sensitive information must be managed securely and loaded from environment variables.

C5. **Graceful Error Handling**: The application must anticipate and handle potential errors gracefully. It should not crash due to invalid input or external service failures.

C6. **Execute Plan Faithfully**: You must execute the approved plan.md precisely as written. Do not deviate from, add to, or reorder the tasks. If a flaw is discovered in the plan during execution, you must halt, report the issue, and await revised instructions.

C7. **Do Not Abandon Failing Tests**: You must never ignore, disable, or delete a failing test to achieve a superficial goal (e.g., meeting a coverage metric). A failing test indicates a bug in either the source code or the test itself. The underlying issue MUST be investigated and resolved. Halting execution to report an unsolvable test is preferable to deleting it.

C8. **Shell Command Argument Quoting**: When executing shell commands that include characters with special meaning to the shell (e.g., brackets [], asterisks *, parentheses ()), you MUST enclose the relevant arguments in single quotes to prevent unintended shell expansion. For example, use `uv pip install -e '.[dev]'` instead of `uv pip install -e .[dev]`.