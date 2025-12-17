# AI Assistant Guidelines

Copy to your AI assistant configuration directory (`.cursor/rules/`, `.clinerules/`, etc.)

## Action-Focused Behavior

**ALWAYS:**
- Implement immediately when asked to "do it" or "fix it"
- Check ALL command exit codes (0 = success, non-zero = failure)
- Read COMPLETE stdout AND stderr output
- Report errors immediately with exact error text
- **Use temporary files for large messages** (PR bodies >100 chars, multi-line commits)
- Verify tests pass before claiming success
- Add AI attribution to commits: `[AI]` prefix + attribution footer

**NEVER:**
- Claim success without checking exit codes
- Ignore stderr/stdout output
- Use `--no-verify` to bypass checks
- Make multiple assumptions - verify first
- Create issues instead of implementing fixes
- Ask for permission after "do it" commands

## Token Efficiency

Target: <5K tokens per simple task, <10K for complex tasks

**Waste Prevention:**
- Don't explain - implement
- Don't offer options - pick best solution
- Don't repeat context - reference memory files
- Don't over-ask - clarify once, proceed
- Don't over-document - code should be self-explanatory

## Verification Checklist

Before claiming "done":
1. ✅ Exit code is 0
2. ✅ No errors in output
3. ✅ Tests pass
4. ✅ Files exist where expected
5. ✅ Changes committed if needed

## Using Files for Messages

To avoid token waste and formatting issues, use temporary files for:
- PR descriptions >100 characters
- Multi-line commit messages
- Complex command input

**Example:**
```powershell
# PR creation
@'
Short description

Changes:
- Point 1
- Point 2
'@ | Out-File -FilePath pr-body.txt -Encoding utf8
gh pr create --title "Title" --body-file pr-body.txt
rm pr-body.txt

# Commit messages
@'
feat: add new feature

Detailed explanation

---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
'@ | Out-File -FilePath commit-msg.txt -Encoding utf8
git commit -F commit-msg.txt
rm commit-msg.txt
```

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
