# Java Style Guide

This document defines the coding standards for Java modules in this project. It is modeled after the Python style guide and tailored to the structure and conventions of the backend Java codebase.

**Dependency Management**

JV1. Use Gradle for all dependency and build management. Do not use Maven or manual JAR management.
JV2. All dependencies must be declared in `build.gradle.kts`. No dependencies may be managed outside of Gradle.

**Project Structure**

JV3. All source code must reside in `src/main/java/`. All tests must be located in `src/test/java/`.
JV4. Use standard Java package naming conventions (e.g., `com.cloudera.cai.rag`).
JV5. Each Java class must be in its own file, named after the class.
JV6. Organize code by feature/module (e.g., `rag/`, `util/`, `configuration/`, `datasources/`).

**Class and Method Design**

JV7. Model the domain with cohesive classes; expose behavior via instance or static methods as appropriate.
JV8. Prefer composition over inheritance. Each class should have a single responsibility.
JV9. Use dependency injection (e.g., Spring's `@Autowired` or constructor injection) for all external dependencies.
JV10. Forbid global mutable state. Use beans, configuration, or method parameters for state management.

**Type Safety and Annotations**

JV11. Use explicit types for all public method parameters and return values. Avoid raw types and unchecked casts.
JV12. Annotate REST controllers, services, and configuration classes with appropriate Spring annotations (`@RestController`, `@Service`, `@Configuration`, etc.).
JV13. Use Lombok for boilerplate reduction (e.g., `@Slf4j`, `@Data`, `@Value`) but document any non-obvious behavior.

**Documentation and Comments**

JV14. Every public class and method must have a Javadoc comment describing its purpose and usage.
JV15. Javadoc must use the standard format. The `@param` and `@return` tags are mandatory for all methods with parameters or return values.
JV16. All source files must include the project license header at the top.

**Code Style and Formatting**

JV17. Enforce Google Java Style (or a project-approved formatter) using Spotless or a similar tool. No style violations are permitted.
JV18. Use 2 spaces for indentation. No tabs.
JV19. Use structured logging via SLF4J. Never use `System.out.println` or `printStackTrace` for logging.
JV20. Do not leave TODOs, placeholders, or partial implementations in committed code.

**Configuration and Secrets**

JV21. Source all configuration from environment variables or `application.properties`. Never hardcode secrets or credentials in source files.
JV22. Use Spring's configuration mechanisms (`@Value`, `@ConfigurationProperties`) for injecting config values.

**Testing and Coverage**

JV23. Provide unit tests for every public class and method. Read testing.md for more information on testing patterns.
JV24. Use JUnit 5 for all tests. Place tests in the corresponding package under `src/test/java/`.
JV25. Fail CI on unused imports, variables, or dead code.

**Build and Execution**

JV26. The project must build and run via Gradle (`./gradlew build`).
JV27. The main entry point must be defined in a class with a `main` method, annotated with `@SpringBootApplication` if using Spring Boot.
JV28. All application startup configuration must be in `application.properties` or environment variables.

**Miscellaneous**

JV29. Do not use deprecated APIs or libraries.
JV30. Use Java 17 or later (project default is Java 17).
JV31. Always use imports, rather than fully qualified class names, whenever possible.

---

Adherence to this style guide is mandatory for all Java modules in this project. Code reviews and CI will enforce these standards.
