# AI Assistant Guidelines

## ⚠️ CRITICAL: AI Commit Attribution

**MANDATORY:** Every AI-generated commit MUST have:
- **[AI] prefix**: `[AI] feat: add feature`
- **Attribution footer**: `---\nAI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)`

**Use file-based commits:**
```powershell
@'
[AI] feat: add feature

Description

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
'@ | Out-File -FilePath commit-msg.txt -Encoding utf8
git commit -F commit-msg.txt; rm commit-msg.txt
```

## Action-Focused Behavior

**ALWAYS:**
- Implement immediately on "do it"/"fix it"
- Check exit codes (0 = success)
- Read stdout AND stderr completely
- Use temp files for messages >100 chars
- Verify tests pass before claiming success

**NEVER:**
- Claim success without checking exit code
- Ignore errors
- Use `--no-verify`
- Ask permission after "do it"

## Token Efficiency

Target: <5K tokens/simple task

- Implement, don't explain
- Pick best solution, don't offer options
- Clarify once, then proceed

## Verification

Before "done":
1. Exit code = 0
2. No errors in output
3. Tests pass

## Command Verification

```bash
# Check exit code
echo $LASTEXITCODE  # PowerShell
echo $?             # Bash

# Always look for
"error", "fail", "warning", "not set", "missing", "denied", "invalid"
```

## Memory Files (if applicable)

Reference these for context:
- `memory/docs/product_requirement_docs.md` - Project goals
- `memory/docs/architecture.md` - System design
- `memory/docs/technical.md` - Tech stack
- `memory/tasks/tasks_plan.md` - Current status
- `memory/tasks/active_context.md` - Working context

## Framework Usage

### Search Workflow
```python
from src.aggregator.aggregator import Aggregator
results = aggregator.search("query", count=20)
```

### AI Evaluation
```python
from src.ai.llm_interface import LLMInterface
llm = LLMInterface()
scored = llm.batch_evaluate(items, criteria="...")
```

### Status Tracking
```python
from src.tracker.tracker import get_tracker
tracker = get_tracker()
tracker.track(item)
tracker.update_status(id, "completed")
```

## Emergency Reset

If assistant becomes inefficient:
1. Stop current work
2. Review actual task requirements
3. Pick ONE solution
4. Implement immediately
5. Verify exit codes
6. Report outcome

## Configuration

See `docs/CONFIGURATION.md` for:
- Block list setup
- Provider configuration
- LLM settings
- Rate limiting
