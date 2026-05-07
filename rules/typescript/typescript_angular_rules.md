## TypeScript / Angular Review Rules

Apply these when TypeScript or Angular component/template/style files are changed.

### TypeScript Correctness
- [TS-COR-001] Flag unsafe `any`, double casts, non-null assertions, and optional chaining that masks invalid states in changed logic.
- [TS-COR-002] Check promise flows for missing awaits, unhandled rejections, race conditions, and errors swallowed by catch handlers.
- [TS-COR-003] Verify changed interfaces, DTOs, and API client contracts remain compatible with backend expectations.
- [TS-COR-004] Watch for date, number, locale, and currency handling that can change behavior across browsers or regions.

### Angular Architecture
- [NG-ARCH-001] Keep components focused on presentation and orchestration; flag business logic that belongs in services or state layers.
- [NG-ARCH-002] Check Observable subscriptions for leaks; prefer `async` pipe, `takeUntilDestroyed`, or framework-managed lifecycle cleanup.
- [NG-ARCH-003] Flag direct DOM access, bypassed Angular sanitization, or manual change detection unless strongly justified.
- [NG-ARCH-004] Ensure reactive forms and validators enforce required business constraints, not only UI hints.
- [NG-ARCH-005] Verify route guards, resolvers, interceptors, and auth-sensitive UI changes do not rely on client checks alone.

### Security
- [NG-SEC-001] Flag `innerHTML`, `bypassSecurityTrust*`, dynamic template injection, and unsafe URL construction.
- [NG-SEC-002] Ensure user-controlled data is encoded or sanitized before display, routing, storage, analytics, or logs.
- [NG-SEC-003] Watch for tokens or sensitive data placed in localStorage, query strings, client logs, or browser-readable config.

### Performance & UX Reliability
- [NG-PERF-001] Flag expensive template method calls, nested subscriptions, repeated HTTP calls, and avoidable change-detection churn.
- [NG-PERF-002] Check large lists for pagination, virtualization, trackBy, or server-side filtering when scale is likely.
- [NG-PERF-003] Ensure loading, empty, retry, and error states are handled for user-facing async flows.

### Testing
- [NG-TEST-001] Expect tests for changed services, components, validators, interceptors, guards, and observable error paths.
- [NG-TEST-002] Prefer behavior-oriented tests with realistic inputs over fragile snapshot or DOM-structure-only assertions.
- [NG-TEST-003] For template changes, verify important accessibility behavior such as labels, keyboard flow, ARIA usage, and disabled states.
