## Python Review Rules

Apply these when Python source, packaging, or test files are changed.

### Runtime Correctness
- [PY-COR-001] Flag mutable default arguments, late-binding closure surprises, broad truthiness checks, and shadowed built-ins when they affect behavior.
- [PY-COR-002] Check exception handling for swallowed stack traces, overly broad except blocks, and retries that hide permanent failures.
- [PY-COR-003] Verify file, network, database, and subprocess resources use context managers, timeouts, and deterministic cleanup.
- [PY-COR-004] Watch for timezone-naive datetime usage in persisted data, scheduling, auth expiry, or cross-region workflows.
- [PY-COR-005] Flag serialization/deserialization changes that alter schema compatibility or trust unvalidated input.

### Security
- [PY-SEC-001] Flag unsafe `eval`, `exec`, `pickle`, YAML unsafe loaders, dynamic imports, shell=True, and string-built subprocess commands.
- [PY-SEC-002] Check SQL/ORM calls for parameterization and avoid building filters from raw user-controlled strings.
- [PY-SEC-003] Ensure path joins prevent traversal when handling uploads, archive extraction, local files, or generated reports.

### Async, Concurrency & Performance
- [PY-ASYNC-001] For async code, flag blocking I/O in event loops, un-awaited coroutines, unmanaged tasks, and missing cancellation handling.
- [PY-PERF-001] Watch for N+1 database calls, repeated expensive work in loops, unbounded reads into memory, and inefficient pandas/dataframe operations.
- [PY-PERF-002] Require streaming or chunking for large files, API responses, or generated artifacts when size can grow.

### Design & Maintainability
- [PY-MNT-001] Prefer explicit types and narrow interfaces for public functions, service boundaries, and complex data structures.
- [PY-MNT-002] Flag circular imports, hidden module side effects, and import-time network or filesystem work.
- [PY-MNT-003] Check dependency updates for security posture, Python version compatibility, lockfile consistency, and unnecessary transitive bloat.

### Testing
- [PY-TEST-001] Expect pytest/unit coverage for changed branches, exceptions, validation, and boundary conditions.
- [PY-TEST-002] For bug fixes, require a regression test that fails on the old behavior.
- [PY-TEST-003] Prefer deterministic tests over sleeps, real network calls, local machine paths, or order-dependent assertions.
