## Description

<!-- Provide a clear and concise description of your changes -->
<!-- Please review CONTRIBUTING.md before submitting: https://github.com/jmduea/RimGym/blob/main/CONTRIBUTING.md -->

Fixes #(issue number)

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🔧 Configuration change
- [ ] ♻️ Code refactoring
- [ ] ⚡ Performance improvement
- [ ] ✅ Test addition/update

## Component

<!-- Mark all components affected by this PR -->

- [ ] C# Mod (RimWorld)
- [ ] Python Client
- [ ] Docker Infrastructure
- [ ] Protobuf Schema
- [ ] Documentation
- [ ] CI/CD
- [ ] Tests

## Changes Made

<!-- List the specific changes made in this PR -->

-
-
-

## Testing

<!-- Describe the tests you ran to verify your changes -->

### Unit Tests

- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Test coverage maintained or improved

```bash
# Commands run:
uv run pytest src/RimGym/tests/ -v
dotnet test tests/RimTCP.Tests/RimTCP.Tests.csproj -c Release
```

### Integration Tests

- [ ] Tested with Docker container
- [ ] Tested with actual RimWorld instance
- [ ] Tested in both Training and Inference modes

### Manual Testing

<!-- Describe manual testing performed -->

- [ ] Tested on Windows
- [ ] Tested on Linux
- [ ] Tested on macOS (if applicable)

**Test scenario**:
<!-- Describe what you did to test -->

**Result**:
<!-- What happened -->

## Performance Impact

<!-- If applicable, describe any performance implications -->

- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance degraded (explain why this is acceptable)

**Benchmarks** (if applicable):

```
Before: X ms/op
After: Y ms/op
```

## Breaking Changes

<!-- If this PR introduces breaking changes, describe them and migration path -->

- [ ] No breaking changes
- [ ] Breaking changes (describe below)

**Migration Guide** (if breaking):
<!-- How should users update their code? -->

## Documentation

- [ ] Updated relevant documentation
- [ ] Added/updated code comments
- [ ] Updated CHANGELOG.md
- [ ] Updated README.md (if applicable)
- [ ] Added/updated examples

## Checklist

<!-- Ensure all items are completed before requesting review -->

- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings or errors
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots / Recordings

<!-- If applicable, add screenshots or recordings to demonstrate the changes -->

## Additional Context

<!-- Add any other context about the PR here -->

## Reviewer Notes

<!-- Any specific areas you'd like reviewers to focus on? -->

---

**For Maintainers**:

- [ ] Code review completed
- [ ] Tests verified
- [ ] Documentation reviewed
- [ ] Ready to merge
