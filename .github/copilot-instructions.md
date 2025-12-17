# AI Search Match Framework (ASMF)

## Project Overview

This is a reusable Python framework for building AI-powered search and analysis applications. It provides core infrastructure that can be shared across multiple domain-specific projects (patent analysis, grant finding, contract analysis, etc.).

## Core Components

### 1. AI Providers (`asmf.providers`)
- **BaseAIProvider**: Abstract interface for AI providers
- **GeminiProvider**: Google Gemini API integration
- **OllamaProvider**: Local Ollama integration
- **AIProviderFactory**: Automatic provider selection with fallback chain (Gemini → Ollama)

### 2. Document Parsers (`asmf.parsers`)
- **PDFParser**: Generic PDF text extraction (pypdf + pdfplumber)
- **DocumentParser**: Base class for document parsing
- Support for various document formats (PDF, DOCX, TXT)

### 3. Base Analyzers (`asmf.analyzers`)
- **BaseAnalyzer**: Abstract analyzer pattern
- Reusable analysis workflows
- Result formatting and scoring patterns

### 4. Utilities (`asmf.utils`)
- Configuration management
- Logging setup
- Common helper functions

## Technology Stack

- **Python**: 3.10+
- **AI**: google-generativeai (Gemini), httpx (Ollama)
- **PDF**: pypdf, pdfplumber
- **Data**: pydantic for models
- **Testing**: pytest, pytest-cov
- **Packaging**: uv for fast installs
- **Containers**: Docker support

## Package Structure

```
ai-search-match-framework/
├── src/
│   └── asmf/
│       ├── __init__.py
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base_provider.py
│       │   ├── gemini_provider.py
│       │   ├── ollama_provider.py
│       │   └── provider_factory.py
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── base_parser.py
│       │   └── pdf_parser.py
│       ├── analyzers/
│       │   ├── __init__.py
│       │   └── base_analyzer.py
│       └── utils/
│           ├── __init__.py
│           ├── config.py
│           └── logging.py
├── tests/
├── pyproject.toml
├── README.md
└── Dockerfile
```

## Development Guidelines

### Code Style
- **PEP 8** compliance
- **Type hints** for all public APIs
- **Docstrings** (Google style) for all public functions/classes
- **Black** for formatting (line length 120)
- **isort** for import sorting

### Testing
- Unit tests for all public APIs
- pytest fixtures for common test data
- Mock external APIs (Gemini, Ollama)
- Aim for >80% code coverage

### Documentation
- Clear README with usage examples
- Docstrings for all public APIs
- Type hints for IDE support

### API Design
- Keep interfaces generic and extensible
- Domain-specific logic should NOT be in this framework
- Configuration via environment variables or constructor args
- Graceful error handling with informative messages

## Usage Example

```python
# Install
pip install ai-search-match-framework

# Use providers
from asmf.providers import AIProviderFactory

provider = AIProviderFactory.create_provider()
result = provider.analyze_text("Analyze this document...")

# Use parsers
from asmf.parsers import PDFParser

parser = PDFParser()
text = parser.extract_text("document.pdf")

# Extend for domain-specific use
from asmf.analyzers import BaseAnalyzer

class MyDomainAnalyzer(BaseAnalyzer):
    def analyze(self, data):
        # Domain-specific logic here
        pass
```

## Projects Using ASMF

1. **ai-patent-eval**: Patent analysis for pyrolysis technologies
2. **ai-grant-finder** (planned): Grant opportunity matching
3. **ai-contract-analyzer** (planned): Contract review and risk analysis

## Development Workflow

1. Changes to framework → PR to `main`
2. Version bump after merge
3. Dependent projects update their `pyproject.toml` dependency version

## AI Commit Attribution Standards

### When to Use [AI] Prefix

When GitHub Copilot or other AI tools generate commits, use the `[AI]` prefix to track AI contributions:

**Format:**
```
[AI] <type>: <description>

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
```

### Use Files for Large Messages

For token efficiency and to avoid formatting issues, use temporary files for:
- PR descriptions with multiple sections or >100 characters
- Multi-line commit messages with detailed explanations
- Any message that includes code blocks or complex formatting

**PowerShell Example:**
```powershell
# Create commit message in file
@'
[AI] feat: add comprehensive feature

Implemented:
- Feature A
- Feature B

Tested with unit tests.

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
'@ | Out-File -FilePath commit-msg.txt -Encoding utf8
git commit -F commit-msg.txt
rm commit-msg.txt

# Create PR with file-based body
@'
## Changes
- Fix X
- Add Y

## Testing
All tests pass
'@ | Out-File -FilePath pr-body.txt -Encoding utf8
gh pr create --title "fix: description" --body-file pr-body.txt
rm pr-body.txt
```

**Benefits:**
- Avoids wasting tokens on debugging escape sequences
- Easier to edit and review before submission
- Cleaner command history

### When to Apply [AI] Prefix

Use `[AI]` prefix when:
- AI generated the majority (>50%) of code changes
- AI wrote the commit message
- AI suggested the implementation approach
- You used AI pair programming for the entire feature

Do NOT use `[AI]` when:
- AI only helped with debugging or understanding existing code
- You significantly modified AI-generated code
- AI contributed a minor portion of the changes

### Attribution Footer Format

Always include the attribution footer for AI-generated commits:

```
---
AI-Generated-By: <Tool Name> (<Model>)
```

**Examples:**
- `AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)`
- `AI-Generated-By: GitHub Copilot (GPT-4)`
- `AI-Generated-By: Cursor (Claude Opus)`

### Complete Examples

```
[AI] feat(providers): add Azure OpenAI provider

Implement AzureOpenAIProvider class with authentication
and rate limiting support.

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
```

```
[AI] fix(parsers): handle malformed PDF headers

Add validation and error handling for corrupted PDF files.

---
AI-Generated-By: GitHub Copilot (GPT-4)
```

### Purpose

We track AI contributions for:
1. **Accessibility Advocacy**: Demonstrate productivity improvements for developers with accessibility needs
2. **Productivity Metrics**: Measure AI's impact on development velocity

### Quick Setup

Use the provided git alias for easy AI commits:

```bash
# Source the alias
source scripts/git-aliases.sh

# Use it
git aic "feat(providers): add new provider"
```

For complete details, see [commit-conventions.md](commit-conventions.md).

## Code Review Guidelines

### AI-Powered Code Reviews

When reviewing pull requests, refer to [CODE_REVIEW_PATTERNS.md](CODE_REVIEW_PATTERNS.md) for comprehensive anti-patterns to catch automatically.

### Key Focus Areas

**Performance Anti-Patterns:**
- Regex compilation inside loops (compile at module/class level)
- Repeated dictionary/list lookups in loops (cache values)
- String concatenation with `+=` in loops (use `str.join()`)
- Repeated function calls with identical arguments (call once, cache result)

**Code Quality Anti-Patterns:**
- Imports in conditional blocks or functions (move to top)
- Deep nesting >3 levels (use early returns, extract helpers)
- Bare `except:` clauses (catch specific exceptions)
- Missing error handling in type conversions (`int()`, `float()`)
- Mutable default arguments (use `None` with conditional init)
- Silent exception handling (always log before swallowing)

**Python-Specific Anti-Patterns:**
- Complex list comprehensions with error handling (use explicit loops)
- Using `assert` for data validation (use `raise ValueError`)
- Not using context managers for resources (use `with` statements)
- Eager string formatting in log statements (use lazy formatting)

**Security Anti-Patterns:**
- SQL injection via string formatting (use parameterized queries)
- Unsafe deserialization with `pickle.load()` or `eval()` (use JSON)
- Hardcoded credentials (use environment variables)
- Path traversal vulnerabilities (validate and normalize paths)

### Review Process

1. **Automated Checks**: Run linters (black, isort, flake8, ruff, mypy) before manual review
2. **Pattern Detection**: Scan for anti-patterns from CODE_REVIEW_PATTERNS.md
3. **Context Analysis**: Consider performance impact, security implications, and maintainability
4. **Constructive Feedback**: Provide specific examples and rationale for suggested changes
5. **Acknowledge Good Patterns**: Highlight well-written code that follows best practices

### Quick Review Checklist

- [ ] No regex compilation in loops
- [ ] All imports at top of file
- [ ] Specific exceptions caught (no bare `except:`)
- [ ] Type conversions wrapped in try/except
- [ ] No mutable default arguments
- [ ] Nesting depth ≤3 levels
- [ ] Resources use `with` statements
- [ ] No hardcoded credentials
- [ ] SQL queries are parameterized
- [ ] File paths are validated

See [CODE_REVIEW_PATTERNS.md](CODE_REVIEW_PATTERNS.md) for detailed examples and rationale.
