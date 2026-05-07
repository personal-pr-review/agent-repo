## Universal Review Standards

Use these rules for every PR. Focus on changed behavior, not unrelated legacy code.

### Security & Safety
- [COMMON-SEC-001] Flag secrets, credentials, tokens, private keys, or sensitive connection strings committed to code, config, logs, tests, or examples.
- [COMMON-SEC-002] Require validation and safe handling for external input, request payloads, CLI arguments, files, environment variables, and deserialized data.
- [COMMON-SEC-003] Watch for injection risks in SQL, shell commands, templates, path handling, LDAP, XML, HTML, and dynamic evaluation.
- [COMMON-SEC-004] Flag unsafe authorization changes, privilege escalation paths, missing ownership checks, and trust placed in client-controlled fields.
- [COMMON-SEC-005] Ensure sensitive data is not logged, returned in errors, exposed in telemetry, or stored without appropriate protection.

### Correctness & Reliability
- [COMMON-COR-001] Check whether the new behavior matches the stated PR intent and comparison-agent behavioral summary.
- [COMMON-COR-002] Flag edge cases introduced by null, empty, malformed, duplicate, concurrent, large, slow, or missing inputs.
- [COMMON-COR-003] Verify error paths return safe, actionable outcomes and do not mask important failures.
- [COMMON-COR-004] Watch for partial updates, non-atomic workflows, race conditions, stale reads, and idempotency regressions.
- [COMMON-COR-005] Treat changes to public APIs, data contracts, migrations, auth, payments, or background jobs as higher risk.

### Architecture & Maintainability
- [COMMON-ARCH-001] Prefer small, cohesive changes with clear ownership boundaries and minimal cross-layer coupling.
- [COMMON-ARCH-002] Flag duplicated business logic when it creates inconsistent behavior or future maintenance risk.
- [COMMON-ARCH-003] Apply SOLID, DRY, and KISS pragmatically; avoid abstracting unless it reduces real complexity.
- [COMMON-ARCH-004] Check whether new dependencies are justified, maintained, pinned appropriately, and used narrowly.
- [COMMON-ARCH-005] Watch for changes that bypass existing validation, authorization, caching, transaction, or observability patterns.

### Operability
- [COMMON-OPS-001] Ensure logs have useful context but do not leak secrets or personal data.
- [COMMON-OPS-002] Recommend metrics, traces, alerts, or audit events only when production diagnosis would otherwise be difficult.
- [COMMON-OPS-003] Flag retries without backoff, timeouts, cancellation, idempotency, or clear failure boundaries.
- [COMMON-OPS-004] Verify config changes have safe defaults and do not silently change production behavior.

### Testing & Documentation
- [COMMON-TEST-001] Require tests for changed logic, boundary conditions, failure paths, and security-sensitive behavior.
- [COMMON-TEST-002] Flag test updates that only assert implementation details instead of observable behavior.
- [COMMON-TEST-003] Expect documentation updates for public API, workflow, deployment, configuration, or operational changes.

### Response Guidance
- [COMMON-RESP-001] Generate comments only for actionable issues tied to the changed diff.
- [COMMON-RESP-002] Prefer one concise comment per distinct issue; avoid repeating the same concern across nearby lines.
- [COMMON-RESP-003] If a concern cannot be anchored to a valid added line, include it in issues_found rather than suggested_comments.
- [COMMON-RESP-004] Do not manufacture comments for clean or low-risk PRs; an empty suggested_comments array is a valid senior review outcome.
- [COMMON-RESP-005] Inline comments must explain practical impact, not just state that code could be improved.
