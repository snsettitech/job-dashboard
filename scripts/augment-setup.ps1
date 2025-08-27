# Recruitly Augment Agent Setup Script
param(
    [string]$Action = "setup"
)

function Write-Banner {
    param([string]$Message)
    Write-Host "`n🤖 $Message" -ForegroundColor Cyan
    Write-Host ("=" * ($Message.Length + 4)) -ForegroundColor Cyan
}

function Test-AugmentIntegration {
    Write-Banner "Testing Augment Integration"
    
    # Check if context files exist
    $contextFiles = @(
        ".augment/MASTER_CONTEXT.md",
        ".augment/LEARNING_STRATEGY.md", 
        ".augment/ARCHITECTURE.md",
        ".augment/ROADMAP.md",
        "docs/PRODUCT_VISION.md",
        "docs/AI_OPTIMIZATION_PLAN.md"
    )
    
    $allExist = $true
    foreach ($file in $contextFiles) {
        if (Test-Path $file) {
            Write-Host "✅ $file" -ForegroundColor Green
        } else {
            Write-Host "❌ $file - Missing!" -ForegroundColor Red
            $allExist = $false
        }
    }
    
    # Check VS Code settings
    if (Test-Path ".vscode/settings.json") {
        $settings = Get-Content ".vscode/settings.json" -Raw
        if ($settings -match "augment\.contextFiles") {
            Write-Host "✅ VS Code Augment configuration found" -ForegroundColor Green
        } else {
            Write-Host "❌ VS Code Augment configuration missing" -ForegroundColor Red
            $allExist = $false
        }
    }
    
    # Check context tools
    if (Test-Path ".vscode/context-tools/update-augment-context.js") {
        Write-Host "✅ Augment context updater found" -ForegroundColor Green
    } else {
        Write-Host "❌ Augment context updater missing" -ForegroundColor Red
        $allExist = $false
    }
    
    return $allExist
}

function Start-AugmentSession {
    Write-Banner "Starting Augment Session"
    
    # Update context
    Write-Host "🔄 Updating context..." -ForegroundColor Yellow
    node .vscode/context-tools/update-augment-context.js
    
    # Generate session prompt
    $prompt = @"
# 🤖 Recruitly Augment Session Started

## Context Loaded
✅ Master Context: Strategic overview and priorities
✅ Learning Strategy: Self-improving AI system plan  
✅ Architecture: Technical implementation details
✅ Roadmap: Phase-by-phase execution plan
✅ Product Vision: 10K user goal and market strategy
✅ AI Optimization Plan: 3-stage pipeline architecture

## Current Status
📍 **Phase**: 1C - AI Issues Resolution & Deployment Prep
🎯 **Goal**: Fix AI optimization and deploy to production
⏰ **Timeline**: This week

## Immediate Priorities
1. 🔧 Fix OpenAI API key configuration
2. 🔧 Resolve numpy compatibility issue  
3. 🚀 Deploy to Railway + Netlify
4. 👥 Get 20 beta users for validation

## Decision Framework
Every decision evaluated on:
- 📈 Business Impact (toward 10K users)
- 🧠 Learning Opportunity (AI improvement)  
- 💰 Revenue Potential (monetization)
- 👤 User Experience (core optimization flow)

## Working Principles
- Speed > Perfection
- Users > Code  
- Revenue > Features
- Data > Opinions
- Done > Perfect

Ready to help with strategic decisions, technical implementation, and execution planning.

**What would you like to work on?**
"@

    Write-Host $prompt -ForegroundColor White
    
    # Copy to clipboard if possible
    try {
        $prompt | Set-Clipboard
        Write-Host "`n📋 Session prompt copied to clipboard!" -ForegroundColor Green
        Write-Host "Paste this into Augment Agent to load full context." -ForegroundColor Yellow
    } catch {
        Write-Host "`n💡 Copy the above prompt and paste into Augment Agent" -ForegroundColor Yellow
    }
}

function Update-AugmentContext {
    Write-Banner "Updating Augment Context"
    
    # Run context updater
    if (Test-Path ".vscode/context-tools/update-augment-context.js") {
        node .vscode/context-tools/update-augment-context.js
        Write-Host "✅ Context updated successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Context updater not found" -ForegroundColor Red
        return $false
    }
    
    # Update session context
    $sessionContext = @{
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        project = @{
            name = "Recruitly"
            phase = "1C - AI Issues Resolution & Deployment Prep"
            priorities = @(
                "Fix AI optimization issues (OpenAI + numpy)",
                "Deploy to production (Railway + Netlify)",
                "Get 20 beta users for validation",
                "Implement learning data collection"
            )
        }
        git_status = @{
            branch = (git branch --show-current).Trim()
            modified_files = (git status --porcelain | Measure-Object -Line).Lines
        }
        servers = @{
            backend_running = (netstat -an | Select-String ":8000") -ne $null
            frontend_running = (netstat -an | Select-String ":3000") -ne $null
        }
    }
    
    $sessionPath = ".augment/session-context.json"
    $sessionContext | ConvertTo-Json -Depth 10 | Out-File $sessionPath -Encoding UTF8
    Write-Host "✅ Session context saved to $sessionPath" -ForegroundColor Green
    
    return $true
}

function Show-AugmentCommands {
    Write-Banner "Augment Integration Commands"
    
    $commands = @"
## Quick Start Commands

### Load Full Context
```
Load context from .augment/MASTER_CONTEXT.md and help me with [specific task].
Focus on self-improving AI optimization as described in docs/AI_OPTIMIZATION_PLAN.md
```

### Strategic Decision Making
```
Based on our context in .augment/MASTER_CONTEXT.md, should we prioritize [option A] or [option B]?
Consider business impact, learning opportunity, revenue potential, and user experience.
```

### Feature Development
```
Using the strategy in docs/AI_OPTIMIZATION_PLAN.md, implement [feature name] with learning loop integration.
Reference .augment/ARCHITECTURE.md for technical implementation details.
```

### Code Review
```
Review this code considering our learning system goals from docs/AI_OPTIMIZATION_PLAN.md.
Ensure it aligns with our self-improving AI strategy.
```

### Progress Assessment
```
Review our progress against .augment/ROADMAP.md and suggest next priorities.
Focus on moving toward 10,000 user goal.
```

## VS Code Integration

### Command Palette
- Ctrl+Shift+P → "Tasks: Run Task" → "📋 Update Recruitly Context"
- Ctrl+Shift+P → "Tasks: Run Task" → "🧠 Quick Context Check"

### Auto-Context Updates
- Context automatically updates when you save .py, .tsx, .jsx files
- Augment context updates when you save .augment/*.md files
- Session tracking via .vscode/context-tools/sync-session.js

## PowerShell Integration

### Update Context
```powershell
.\scripts\augment-setup.ps1 -Action update
```

### Start Session
```powershell
.\scripts\augment-setup.ps1 -Action session
```

### Test Integration
```powershell
.\scripts\augment-setup.ps1 -Action test
```
"@

    Write-Host $commands -ForegroundColor White
}

# Main execution
switch ($Action.ToLower()) {
    "setup" {
        Write-Banner "Recruitly Augment Agent Setup"
        
        if (Test-AugmentIntegration) {
            Write-Host "`n🎉 Augment integration is ready!" -ForegroundColor Green
            Write-Host "Run: .\scripts\augment-setup.ps1 -Action session" -ForegroundColor Yellow
        } else {
            Write-Host "`n❌ Setup incomplete. Check missing files above." -ForegroundColor Red
        }
    }
    
    "test" {
        $result = Test-AugmentIntegration
        if ($result) {
            Write-Host "`n✅ All tests passed!" -ForegroundColor Green
        } else {
            Write-Host "`n❌ Some tests failed." -ForegroundColor Red
        }
    }
    
    "update" {
        Update-AugmentContext
    }
    
    "session" {
        Start-AugmentSession
    }
    
    "commands" {
        Show-AugmentCommands
    }
    
    default {
        Write-Host "Usage: .\scripts\augment-setup.ps1 -Action [setup|test|update|session|commands]" -ForegroundColor Yellow
    }
}
