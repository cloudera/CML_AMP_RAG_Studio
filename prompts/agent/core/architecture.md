# Architecture Guidelines

A1. **Application Entrypoint**: The main entry point of the application will be an App class. This class will be instantiated and its primary method (e.g., run()) will be invoked from a main function, which is triggered by the standard `if __name__ == "__main__":` block.

A2. **Composition over Inheritance**: The architecture will be component-based, favoring composition to build complex functionality. The App class will act as an orchestrator, delegating tasks to specialized service or manager classes ("sub-systems").

A3. **Dependency Injection**: Dependencies (such as services, data adapters, or configuration objects) must not be created within a class. Instead, they must be "injected" into the class's constructor (`__init__`).

A4. **Domain Modeling**: The core logic of the problem domain should be modeled with cohesive classes. Each class should represent a single, well-defined entity and its associated behaviors.

A5. **Single Responsibility Principle**: Every class must have only one primary responsibility. This keeps classes focused, understandable, and easier to maintain.

A6. **Pragmatic Abstraction**: Strive for a reasonable balance in design. Avoid premature or excessive abstraction. Favor simple, clear solutions over overly complex and speculative designs.
