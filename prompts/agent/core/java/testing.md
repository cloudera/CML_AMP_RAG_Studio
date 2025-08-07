# Java Testing Standards: Nullables and Test Doubles Pattern

This document supplements the main Java Style Guide with project-specific testing conventions. The backend Java module uses a **nullables/test doubles** pattern for testing, which emphasizes testing with explicit in-memory or no-op implementations (test doubles), rather than mocks or stubs.

## What is the Nullables/Test Doubles Pattern?

In this project, the nullables pattern means providing dependencies as explicit test doubles—such as in-memory, no-op, or fake implementations—using static factory methods (e.g., `createNull()`). These test doubles implement the same interface as production code, but avoid side effects and external dependencies. This approach enables fast, deterministic, and isolated tests, without the complexity or brittleness of mocking frameworks.

## Guidelines

JT1. **Use Test Doubles via Factory Methods**: When testing a class with dependencies, inject test doubles created by static factory methods (e.g., `Repository.createNull()`). Do not use mocks or pass `null` directly.

JT2. **No Mocking Frameworks**: Do not use Mockito, EasyMock, or similar libraries. All test doubles must be implemented as real classes in the codebase.

JT3. **Constructor Injection**: Design classes so that dependencies can be injected via constructors. This enables easy substitution of test doubles in tests.

JT4. **Test Real Logic**: Write tests that exercise real service logic, with dependencies replaced by test doubles. Avoid verifying interactions; assert on observable outcomes.

JT5. **Keep Test Doubles Simple**: Test doubles should be minimal, in-memory, and side-effect-free. They should be easy to reason about and maintain.

JT6. **No Nulls for Required Dependencies**: Never pass `null` for required dependencies. Use a test double instead. Only pass `null` if the production code is explicitly designed to accept it.

JT7. **Document Test Double Factories**: Clearly document static factory methods (e.g., `createNull()`) that provide test doubles, so their behavior is well understood.

JT8. **Test Coverage**: Maintain ≥ 80% test coverage, as required by the main style guide.

JT9. **JUnit 5**: All tests must use JUnit 5 and be placed in the corresponding package under `src/test/java/`.

JT10. **No Reflection for Injection**: Do not use reflection to inject dependencies or alter private state in tests.

JT11. **Assertions**: Use AssertJ for assertions in all unit tests. Prefer fluent, readable assertions (e.g., `assertThat(value).isEqualTo(expected)`) over JUnit's built-in assertions. AssertJ enables expressive checks for collections, exceptions, and object properties, improving test clarity and failure diagnostics.

## Example

```java
// Production code
public class MyService {
    private final MyRepository repo;
    public MyService(MyRepository repo) {
        this.repo = repo;
    }
    public String getValue(String key) {
        return repo.find(key).orElse("default");
    }
}

// Test double (in production code):
public class MyRepository {
    public Optional<String> find(String key) { /* real implementation */ }

    // nullables below here
    public static MyRepository createNull() {
        return new MyRepository() {
            @Override
            public Optional<String> find(String key) { return Optional.empty(); }
        };
    }
}

// Test code
@Test
void returnsDefaultWhenRepoReturnsEmpty() {
    MyService service = new MyService(MyRepository.createNull());
    assertThat(service.getValue("any")).isEqualTo("default");
}
```

---

Adherence to the nullables/test doubles pattern is mandatory for all Java tests in this project. Code reviews and CI will enforce these standards.
