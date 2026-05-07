## .NET / C# Review Rules

Apply these when C#, project, solution, Razor, or NuGet-related files are changed.

### Correctness & API Behavior
- [DOTNET-COR-001] Flag nullable reference misuse, unchecked nulls, and suppression operators that can hide invalid states.
- [DOTNET-COR-002] Check async flows for missing awaits, sync-over-async, fire-and-forget tasks, and missing cancellation tokens.
- [DOTNET-COR-003] Verify public API, DTO, serialization, model binding, and validation changes remain backward-compatible where required.
- [DOTNET-COR-004] Watch for LINQ queries that change execution timing, materialize too early, or execute repeatedly against databases.

### ASP.NET / Service Architecture
- [DOTNET-API-001] Ensure controllers/endpoints delegate business logic to services and enforce model validation consistently.
- [DOTNET-API-002] Check authorization attributes, policies, claims, tenant checks, and ownership validation for protected operations.
- [DOTNET-API-003] Require clear status codes and problem details for API error paths without leaking implementation details.
- [DOTNET-API-004] Verify dependency injection lifetimes are safe; flag singleton services depending on scoped services or mutable shared state.

### Data, Transactions & Performance
- [DOTNET-DATA-001] Flag EF Core N+1 queries, missing indexes for new query patterns, accidental client evaluation, and unbounded includes.
- [DOTNET-DATA-002] Check migrations for destructive operations, default values, locking risk, rollback strategy, and backward compatibility.
- [DOTNET-PERF-001] Prefer streaming for large responses and avoid loading entire files/results into memory unless bounded.

### Security
- [DOTNET-SEC-001] Flag raw SQL string interpolation, unsafe deserialization, path traversal, weak crypto, and insecure temp-file handling.
- [DOTNET-SEC-002] Ensure configuration/secrets use secure providers and are not committed in appsettings or test fixtures.
- [DOTNET-SEC-003] Check CORS, cookie, auth, and token changes for least privilege and safe production defaults.

### Testing
- [DOTNET-TEST-001] Expect unit or integration tests for changed services, validators, authorization, mapping, and data access behavior.
- [DOTNET-TEST-002] Prefer realistic WebApplicationFactory/integration coverage for endpoint behavior and middleware-sensitive changes.
- [DOTNET-TEST-003] For bug fixes, require a regression test that captures the previous failure mode.
