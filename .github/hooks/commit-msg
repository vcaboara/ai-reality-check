#!/bin/bash
# Pre-commit hook to validate AI commit message format

commit_msg_file="$1"
commit_msg=$(cat "$commit_msg_file")

# Check if commit message starts with [AI]
if [[ ! "$commit_msg" =~ ^\[AI\] ]]; then
    echo "ERROR: Commit message must start with [AI] prefix"
    echo "Format: [AI] <type>: <description>"
    exit 1
fi

# Check if commit has attribution footer
if [[ ! "$commit_msg" =~ AI-Generated-By: ]]; then
    echo "ERROR: Commit message must include AI attribution footer"
    echo "Add: ---"
    echo "AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)"
    exit 1
fi

exit 0
