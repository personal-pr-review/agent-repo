# Dynamic Rulebook Runtime Examples

## Architecture

- `rules/common/common_rules.md` is loaded for every PR.
- `rules/python/python_rules.md` is loaded for Python changes.
- `rules/typescript/typescript_angular_rules.md` is loaded for TypeScript or Angular-signaled changes.
- `rules/dotnet/dotnet_rules.md` is loaded for C#/.NET changes.
- `rules/java/java_springboot_rules.md` is loaded for Java/Spring Boot changes.
- `src/pr_review/framework_detector.py` detects ecosystems from changed file paths.
- `src/pr_review/rulebook_loader.py` reads, deduplicates, and merges selected rulebooks.
- `src/pr_review/prompt_builder.py` appends only selected rulebook context to the Review Agent prompt.

## Runtime Flow

1. GitHub API returns changed PR files.
2. Comparison Agent reviews each file without rulebooks and explains what changed.
3. Rulebook Loader analyzes changed file paths and loads only relevant rulebooks.
4. Review Agent receives PR metadata, comparison results, and selected rulebook context.
5. Review Agent returns `summary`, `issues_found`, `suggested_comments`, and `final_recommendation`.

## Python PR Prompt Shape

Changed files:

```text
src/service/retry.py
tests/test_retry.py
```

Selected rulebooks:

```text
Common Review Rules
Python Review Rules
```

Prompt includes the base Review Agent instructions plus common and Python-specific rules. TypeScript, .NET, and Java rules are not loaded.

## TypeScript / Angular PR Prompt Shape

Changed files:

```text
src/app/orders/order-detail.component.ts
src/app/orders/order-detail.component.html
src/app/orders/order-detail.component.scss
```

Selected rulebooks:

```text
Common Review Rules
TypeScript / Angular Review Rules
```

Prompt includes Angular-specific checks for subscriptions, template safety, validators, async states, and component/service boundaries.

## Mixed-Language PR Prompt Shape

Changed files:

```text
src/api/OrderController.cs
src/app/orders/order.service.ts
src/app/orders/order-detail.component.html
```

Selected rulebooks:

```text
Common Review Rules
TypeScript / Angular Review Rules
.NET / C# Review Rules
```

Prompt includes shared universal rules once, then only the TypeScript/Angular and .NET review intelligence. Python and Java/Spring rules are not loaded.
