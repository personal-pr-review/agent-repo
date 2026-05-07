## Java / Spring Boot Review Rules

Apply these when Java, Spring Boot, Maven, or Gradle files are changed.

### Java Correctness
- [JAVA-COR-001] Flag null handling gaps, unchecked Optional usage, mutable static state, and equality/hashCode issues that affect behavior.
- [JAVA-COR-002] Check stream operations for repeated traversal, accidental parallelism, side effects, and unbounded collection materialization.
- [JAVA-COR-003] Verify exception handling preserves useful context and does not convert important failures into generic success paths.
- [JAVA-COR-004] Watch for thread-safety issues in singletons, cached objects, schedulers, and shared collections.

### Spring Boot Architecture
- [SPRING-ARCH-001] Keep controllers thin; business rules should live in services and persistence details in repositories/adapters.
- [SPRING-ARCH-002] Check transaction boundaries for partial writes, lazy-loading surprises, external calls inside transactions, and rollback behavior.
- [SPRING-ARCH-003] Verify validation annotations and programmatic validation cover required request and domain constraints.
- [SPRING-ARCH-004] Ensure configuration properties have safe defaults, validation, and environment-specific behavior that will not surprise production.
- [SPRING-ARCH-005] Check scheduled jobs, listeners, and async handlers for idempotency, concurrency limits, retries, and observability.

### Security
- [SPRING-SEC-001] Flag missing method/endpoint authorization, tenant ownership checks, unsafe SpEL, and trust in caller-supplied identity fields.
- [SPRING-SEC-002] Check JPA/native queries for parameterization and avoid string-built query fragments from user input.
- [SPRING-SEC-003] Ensure actuator, CORS, CSRF, cookies, JWT, and session changes use least-privilege production defaults.
- [SPRING-SEC-004] Do not expose secrets through application.yml/properties, logs, error responses, or test fixtures.

### Data & Performance
- [SPRING-DATA-001] Flag JPA N+1 queries, missing fetch strategy consideration, large eager loads, and pagination omissions.
- [SPRING-DATA-002] Review migrations/schema changes for locking, data loss, backward compatibility, and safe rollout order.
- [SPRING-PERF-001] Require timeouts and bounded resource usage for HTTP clients, database calls, message consumers, and file processing.

### Testing
- [SPRING-TEST-001] Expect tests for changed services, controllers, validation, repositories, security rules, and transaction behavior.
- [SPRING-TEST-002] Use slice or integration tests where framework configuration, serialization, security filters, or transactions matter.
- [SPRING-TEST-003] For bug fixes, require a regression test that fails on the old behavior.
