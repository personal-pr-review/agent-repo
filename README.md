# agent-repo

Centralized PR review agent reused by target repositories through GitHub Actions reusable workflows.

## Dynamic rulebook engine

The Review Agent loads only the rulebooks relevant to the changed files in a PR:

- `rules/common/common_rules.md` is always loaded.
- `rules/python/python_rules.md` is loaded for Python changes.
- `rules/typescript/typescript_angular_rules.md` is loaded for TypeScript / Angular changes.
- `rules/dotnet/dotnet_rules.md` is loaded for .NET / C# changes.
- `rules/java/java_springboot_rules.md` is loaded for Java / Spring Boot changes.

Implementation modules:

- `src/pr_review/framework_detector.py`
- `src/pr_review/rulebook_loader.py`
- `src/pr_review/prompt_builder.py`

The Comparison Agent remains rulebook-free and answers “what changed?”. The Review Agent receives the selected rulebooks and answers “should this change be accepted?”.
