# Bootstrap

## Bootstrap Phase 1: Project Comprehension and Success Definition

B1.1. **Internalize Core Documents**: Read and integrate the information from `critical.md` and `architecture.md` to understand foundational directives.

B1.2. **Internalize Project Requirements**: Check for the existence of `project.md` to build a comprehensive model of the project's objectives, constraints, and architecture. If `project.md` does not exist, stop and collaborate with the User to create it.

B1.3. **Determine Language**: If this looks like a Python project, read `python.md`. If it looks like a Java project, read `java/java.md and java/testing.md`. If it is unclear, ask the User for clarification.

## Bootstrap Phase 2: Tactical Planning

B2.1. **Understand Current State**: Check for the existence of `plan.md`. 
    - If `plan.md` exists: read it and understand you are continuing a project that you started.
        - Read `continue_project.md`. 
    - If there is no `plan.md`:
        - This indicates that you are either working on an existing project you did not create, or it is a brand new project.
        - Check for other program artifacts such as source and build tool configuration. If these exist, it is likely not a new project.
        - If you are CONFIDENT this is a new project, read `new_project.md`.
        - If there is any ambiguity, ask the User before choosing to start a new project or continue.

B2.2. **Post-Installation Tool Verification**: Immediately after a plan step that installs or syncs dependencies, you MUST add a subsequent verification step. This step involves running the `--version` command for each essential command-line tool (e.g., `black --version`, `ruff --version`, `mypy --version`) to confirm it is correctly installed and accessible in the environment's `PATH` before proceeding.

B2.3. **Anticipate Tool Side-Effects**: Before executing a command, anticipate its effects on the filesystem (e.g., `pyproject.toml` modification by `uv add`). Do not create redundant plan steps that manually perform actions already automated by the tool. Trust your tools to perform their documented function.

## Bootstrap Phase 3: Iterative Execution and Verification

B3.1. **Error Handling and Adaptation**: If a task fails or an unexpected issue arises, pause execution. Analyze the problem by referencing the source documents and, if necessary, ask the user for clarification before modifying the plan and resuming.

B3.2. **Final Review**: Upon completing all tasks, perform a final review of the implementation against the agreed-upon Acceptance Criteria to ensure all requirements have been met.

B3.3. **Deliver Final Summary**: Conclude the process by summarizing the completed work and how it fulfills the project's defined goals.
