# Commit Conventions

## Overview

This document outlines the commit message conventions for the AI Search Match Framework (ASMF) project. We follow conventional commits with special standards for AI-generated contributions.

## Standard Commit Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (formatting, missing semicolons, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvements
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Examples

```
feat(providers): add Claude AI provider support
fix(parsers): handle edge case in PDF text extraction
docs(readme): update installation instructions
test(analyzers): add unit tests for BaseAnalyzer
```

## AI-Generated Contributions

### Why Track AI Contributions?

We track AI-generated commits for two important reasons:

1. **Accessibility Advocacy**: Demonstrate how AI tools improve productivity for developers with accessibility needs
2. **Productivity Metrics**: Measure the impact of AI assistance on development velocity and code quality

### AI Commit Format

When using AI assistants (GitHub Copilot, Claude, Gemini, etc.) to generate commits, use the `[AI]` prefix:

```
[AI] <type>(<scope>): <subject>

[optional body]

---
AI-Generated-By: <Tool Name> (<Model>)
```

### AI Attribution Footer

Always include the attribution footer at the end of AI-generated commits:

```
---
AI-Generated-By: <Tool Name> (<Model>)
```

**Examples:**
- `AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)`
- `AI-Generated-By: GitHub Copilot (GPT-4)`
- `AI-Generated-By: Cursor (Claude Opus)`
- `AI-Generated-By: Gemini 1.5 Pro`
- `AI-Generated-By: ChatGPT (GPT-4o)`

### When to Use [AI] Prefix

Use the `[AI]` prefix when:

- ✅ AI generated the majority of the code changes
- ✅ AI wrote the commit message
- ✅ AI suggested the implementation approach
- ✅ You used AI pair programming for the entire feature

Do NOT use `[AI]` prefix when:

- ❌ You only used AI for debugging or understanding existing code
- ❌ AI helped with a small portion and you wrote most of the code
- ❌ You significantly modified AI-generated code
- ❌ AI only helped with documentation/comments (use standard `docs:` type)

**Rule of thumb**: If AI contributed >50% of the intellectual work, use `[AI]` prefix.

### AI Commit Examples

#### Feature Addition
```
[AI] feat(providers): add support for Azure OpenAI

Implement AzureOpenAIProvider class with authentication,
rate limiting, and error handling.

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
```

#### Bug Fix
```
[AI] fix(parsers): handle malformed PDF headers

Add validation for PDF header structure and gracefully
handle corrupted files with appropriate error messages.

---
AI-Generated-By: GitHub Copilot (GPT-4)
```

#### Documentation
```
[AI] docs(api): add comprehensive docstrings to BaseAnalyzer

Include parameter descriptions, return types, and usage
examples for all public methods.

---
AI-Generated-By: Cursor (Claude Opus)
```

#### Refactoring
```
[AI] refactor(utils): simplify configuration loading logic

Reduce complexity by extracting helper functions and
improving error handling paths.

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
```

#### Testing
```
[AI] test(providers): add integration tests for Gemini provider

Cover authentication, retry logic, and error handling
scenarios with mocked API responses.

---
AI-Generated-By: GitHub Copilot (GPT-4)
```

## Git Aliases

To simplify AI commit creation, use the provided git aliases:

### Bash/Linux/Mac
```bash
# Source the aliases file
source scripts/git-aliases.sh

# Use the alias
git aic "feat(providers): add new provider"
```

### Windows PowerShell
```powershell
# Source the aliases file
. .\scripts\git-aliases.ps1

# Use the alias
git aic "feat(providers): add new provider"
```

See [`scripts/git-aliases.sh`](../scripts/git-aliases.sh) and [`scripts/git-aliases.ps1`](../scripts/git-aliases.ps1) for installation instructions.

## Multi-line Commit Messages

For commits requiring detailed explanations:

```
[AI] feat(analyzers): implement batch processing

Add support for processing multiple documents in parallel
with configurable batch sizes and error handling.

Changes:
- Add BatchAnalyzer class
- Implement parallel processing with ThreadPoolExecutor
- Add progress reporting and error aggregation
- Include comprehensive unit tests

Performance: Reduces analysis time by 60% for 100+ documents

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
```

## Best Practices

1. **Keep subject lines under 72 characters**
2. **Use imperative mood** ("add feature" not "added feature")
3. **Capitalize first letter** of the subject
4. **No period at end** of subject line
5. **Separate subject from body** with a blank line
6. **Wrap body at 72 characters**
7. **Use body to explain what and why**, not how
8. **Reference issues** in footer (e.g., `Closes #123`)

## Hybrid Contributions

For commits where both human and AI contributed significantly, use your judgment:

- If primarily AI-driven: use `[AI]` prefix
- If primarily human-driven: use standard format
- When in doubt: use `[AI]` prefix and note human contributions in body

**Example:**
```
[AI] feat(parsers): add DOCX parser with custom extraction

AI generated base implementation, human added domain-specific
extraction rules and edge case handling.

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
Co-authored-by: Human Developer <human@example.com>
```

## Verification

Before committing, verify your message follows the format:

```bash
# Check your last commit message
git log -1 --pretty=%B

# Amend if needed
git commit --amend
```

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contributing guidelines
