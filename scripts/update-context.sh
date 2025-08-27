#!/bin/bash
# Context update script for pre-commit hooks

echo "🧠 Updating development context..."

# Update session context if tools exist
if [ -f ".vscode/context-tools/sync-session.js" ]; then
    echo "🔄 Updating session context..."
    node .vscode/context-tools/sync-session.js
fi

# Update Augment context if tools exist
if [ -f ".vscode/context-tools/update-augment-context.js" ]; then
    echo "🤖 Updating Augment context..."
    node .vscode/context-tools/update-augment-context.js
fi

# Update timestamp in key files
current_date=$(date +%Y-%m-%d)

# Update MASTER_CONTEXT.md timestamp
if [ -f ".augment/MASTER_CONTEXT.md" ]; then
    sed -i "s/\*\*Last Updated\*\*: [0-9-]*/\*\*Last Updated\*\*: $current_date/" .augment/MASTER_CONTEXT.md
fi

# Update DEVELOPMENT_CONTEXT.md timestamp
if [ -f "docs/DEVELOPMENT_CONTEXT.md" ]; then
    sed -i "s/\*\*Last Updated\*\*: [0-9-]*/\*\*Last Updated\*\*: $current_date/" docs/DEVELOPMENT_CONTEXT.md
fi

echo "✅ Context updated successfully"
exit 0
