const fs = require('fs');
const { execSync } = require('child_process');

class RecruitlyContextSync {
  constructor() {
    this.sessionPath = '.context/session/';
    this.masterPath = '.context/master/';
  }

  async updateSessionContext() {
    console.log('🧠 Updating Recruitly session context...');

    try {
      // 1. Get current git context
      const gitBranch = execSync('git branch --show-current').toString().trim();
      const gitStatus = execSync('git status --porcelain').toString();
      const recentCommits = execSync('git log --oneline -5').toString();

      // 2. Get modified files with context
      const modifiedFiles = gitStatus
        .split('\n')
        .filter(line => line.trim())
        .map(line => {
          const status = line.substring(0, 2);
          const file = line.substring(3);
          return { status, file };
        });

      // 3. Analyze file relationships
      const coreFiles = [
        'src/App.tsx',
        'src/components/ResumeOptimizer.tsx',
        'backend/main.py',
        'backend/app/services/enhanced_ai_service.py'
      ];

      const coreFilesModified = modifiedFiles.filter(f =>
        coreFiles.some(core => f.file.includes(core))
      );

      // 4. Create session context
      const sessionContext = {
        timestamp: new Date().toISOString(),
        session: {
          branch: gitBranch,
          modifiedFiles: modifiedFiles.length,
          coreFilesAffected: coreFilesModified.length,
          lastCommits: recentCommits.split('\n').filter(l => l.trim()).slice(0, 3)
        },
        activeContext: {
          focusArea: this.determineFocusArea(modifiedFiles),
          aiSuggestions: this.generateAISuggestions(modifiedFiles),
          relatedFiles: this.findRelatedFiles(modifiedFiles)
        },
        warnings: this.checkForWarnings(modifiedFiles)
      };

      // 5. Write session file
      fs.writeFileSync(
        `${this.sessionPath}current-session.json`,
        JSON.stringify(sessionContext, null, 2)
      );

      // 6. Update context summary for AIs
      const contextSummary = this.createContextSummary(sessionContext);
      fs.writeFileSync(
        `${this.sessionPath}ai-context-summary.md`,
        contextSummary
      );

      console.log('✅ Session context updated successfully!');
      console.log(`📊 Focus: ${sessionContext.activeContext.focusArea}`);
      console.log(`📝 Files: ${modifiedFiles.length} modified`);

      return sessionContext;

    } catch (error) {
      console.error('❌ Context sync failed:', error.message);
      return null;
    }
  }

  determineFocusArea(modifiedFiles) {
    const files = modifiedFiles.map(f => f.file.toLowerCase());

    if (files.some(f => f.includes('enhanced_ai_service'))) return 'AI Pipeline';
    if (files.some(f => f.includes('resumeoptimizer'))) return 'Core UI';
    if (files.some(f => f.includes('app.tsx'))) return 'Architecture';
    if (files.some(f => f.includes('main.py'))) return 'Backend API';
    if (files.some(f => f.includes('package.json'))) return 'Dependencies';

    return 'General Development';
  }

  generateAISuggestions(modifiedFiles) {
    const files = modifiedFiles.map(f => f.file);
    const suggestions = [];

    if (files.some(f => f.includes('.py'))) {
      suggestions.push('Consider FastAPI async patterns and error handling');
    }
    if (files.some(f => f.includes('.tsx') || f.includes('.ts'))) {
      suggestions.push('Ensure TypeScript interfaces and mobile responsiveness');
    }
    if (files.some(f => f.includes('ai_service'))) {
      suggestions.push('Monitor OpenAI token usage and cost implications');
    }

    return suggestions;
  }

  findRelatedFiles(modifiedFiles) {
    const relationships = {
      'enhanced_ai_service.py': ['ResumeOptimizer.tsx', 'main.py'],
      'ResumeOptimizer.tsx': ['App.tsx', 'enhanced_ai_service.py'],
      'App.tsx': ['ResumeOptimizer.tsx', 'main.py'],
      'main.py': ['enhanced_ai_service.py']
    };

    const related = new Set();
    modifiedFiles.forEach(f => {
      Object.keys(relationships).forEach(key => {
        if (f.file.includes(key)) {
          relationships[key].forEach(rel => related.add(rel));
        }
      });
    });

    return Array.from(related);
  }

  checkForWarnings(modifiedFiles) {
    const warnings = [];
    const files = modifiedFiles.map(f => f.file);

    if (files.some(f => f.includes('enhanced_ai_service.py'))) {
      warnings.push('⚠️ AI service modified - test cost impact');
    }
    if (files.some(f => f.includes('package.json') || f.includes('requirements.txt'))) {
      warnings.push('⚠️ Dependencies changed - update deployment');
    }
    if (files.length > 10) {
      warnings.push('⚠️ Many files modified - consider smaller commits');
    }

    return warnings;
  }

  createContextSummary(sessionContext) {
    return `# Current Recruitly Development Session

**Time**: ${new Date(sessionContext.timestamp).toLocaleString()}
**Branch**: ${sessionContext.session.branch}
**Focus Area**: ${sessionContext.activeContext.focusArea}

## Modified Files (${sessionContext.session.modifiedFiles})
${sessionContext.session.modifiedFiles > 0 ? 'Files have been modified in this session.' : 'No files modified yet.'}

## AI Development Suggestions
${sessionContext.activeContext.aiSuggestions.map(s => `- ${s}`).join('\n')}

## Related Files to Consider
${sessionContext.activeContext.relatedFiles.map(f => `- ${f}`).join('\n')}

${sessionContext.warnings.length > 0 ? `\n## Warnings\n${sessionContext.warnings.join('\n')}` : ''}

---
*Auto-generated by Recruitly Context Sync*
`;
  }
}

// Run sync
const sync = new RecruitlyContextSync();
sync.updateSessionContext();
