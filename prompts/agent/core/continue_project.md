# Continuing a Project

CP1. Do not follow any New Project (`NP`) rules.


# Continuing from a Plan

There are two ways to continue developing a project. If a `plan.md` exists, you have been working on this project. Follow the instructions below.

In both cases, always check for the existence of language specific quality tools and tests. Run them after each change. If they fail, ask the user if you should attempt to fix them or ignore it.

CP2. Determine if `plan.md` is incomplete. 
    - If the plan is complete, ask the User for next steps.
    - If the plan is incomplete, continue executing `plan.md`.

CP3. **Execute and Verify**: Execute the tasks from `plan.md` sequentially. After each task that modifies source code, you MUST verify its successful completion by running the full quality-assurance suite. A task is only considered "complete" when all of these checks pass without error.

# Continuing without a Plan

If the project contains source code and other artifacts, but no `plan.md`, DO NOT CREATE A PLAN.

CP4. DO NOT run any New Project Bootstrapping steps.

CP5. Ask the User what task they would like you to perform.

CP6. DO NOT make any invasive or large scale changes EXCEPT in the service of CP4.
