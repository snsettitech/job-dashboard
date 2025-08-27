#!/bin/bash
echo "🔄 Auto-updating Recruitly context..."

# Update session context
node .vscode/context-tools/sync-session.js

# Update git context
echo "## Recent Changes" > .context/session/git-context.md
git log --oneline -10 >> .context/session/git-context.md
echo "" >> .context/session/git-context.md
echo "## Current Status" >> .context/session/git-context.md
git status >> .context/session/git-context.md

echo "✅ Context updated successfully!"