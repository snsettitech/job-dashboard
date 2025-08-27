const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class AugmentContextUpdater {
  constructor() {
    this.projectRoot = process.cwd();
    this.augmentDir = path.join(this.projectRoot, '.augment');
    this.contextFiles = [
      '.augment/MASTER_CONTEXT.md',
      '.augment/LEARNING_STRATEGY.md', 
      '.augment/ARCHITECTURE.md',
      '.augment/ROADMAP.md',
      'docs/PRODUCT_VISION.md',
      'docs/AI_OPTIMIZATION_PLAN.md',
      'docs/DEVELOPMENT_CONTEXT.md'
    ];
  }

  updateAugmentContext() {
    console.log('🧠 Updating Augment Agent context...');
    
    try {
      // 1. Get current project status
      const projectStatus = this.getProjectStatus();
      
      // 2. Update context summary
      const contextSummary = this.generateContextSummary(projectStatus);
      
      // 3. Create session context for Augment
      const sessionContext = {
        timestamp: new Date().toISOString(),
        project: {
          name: "Recruitly",
          phase: "1C - AI Issues Resolution & Deployment Prep",
          priorities: [
            "Fix AI optimization issues (OpenAI + numpy)",
            "Deploy to production (Railway + Netlify)",
            "Get 20 beta users for validation",
            "Implement learning data collection"
          ]
        },
        current_status: projectStatus,
        context_files: this.contextFiles,
        quick_context: contextSummary
      };

      // 4. Write session context
      const sessionPath = path.join(this.augmentDir, 'session-context.json');
      fs.writeFileSync(sessionPath, JSON.stringify(sessionContext, null, 2));

      // 5. Update master context with latest status
      this.updateMasterContextStatus(projectStatus);

      console.log('✅ Augment context updated successfully');
      console.log(`📁 Context files: ${this.contextFiles.length}`);
      console.log(`🎯 Current phase: ${sessionContext.project.phase}`);
      
    } catch (error) {
      console.error('❌ Error updating Augment context:', error.message);
    }
  }

  getProjectStatus() {
    try {
      // Get git status
      const gitBranch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
      const gitStatus = execSync('git status --porcelain', { encoding: 'utf8' });
      const modifiedFiles = gitStatus.split('\n').filter(line => line.trim()).length;

      // Check if servers are running
      const backendRunning = this.checkServerRunning(8000);
      const frontendRunning = this.checkServerRunning(3000);

      // Get recent commits
      const recentCommits = execSync('git log --oneline -3', { encoding: 'utf8' })
        .split('\n')
        .filter(line => line.trim())
        .slice(0, 3);

      // Check test status
      const testStatus = this.getTestStatus();

      return {
        git: {
          branch: gitBranch,
          modified_files: modifiedFiles,
          recent_commits: recentCommits
        },
        servers: {
          backend_running: backendRunning,
          frontend_running: frontendRunning
        },
        tests: testStatus,
        last_updated: new Date().toISOString()
      };
    } catch (error) {
      return {
        error: `Failed to get project status: ${error.message}`,
        last_updated: new Date().toISOString()
      };
    }
  }

  checkServerRunning(port) {
    try {
      execSync(`netstat -an | findstr :${port}`, { encoding: 'utf8' });
      return true;
    } catch {
      return false;
    }
  }

  getTestStatus() {
    try {
      // Check if test files exist and get basic info
      const backendTests = fs.existsSync(path.join(this.projectRoot, 'backend', 'tests'));
      const frontendTests = fs.existsSync(path.join(this.projectRoot, 'frontend', 'src', 'App.test.tsx'));
      
      return {
        backend_tests_exist: backendTests,
        frontend_tests_exist: frontendTests,
        last_run: "Manual check required"
      };
    } catch {
      return {
        backend_tests_exist: false,
        frontend_tests_exist: false,
        last_run: "Unknown"
      };
    }
  }

  generateContextSummary(projectStatus) {
    const summary = [];
    
    // Current focus
    summary.push("🎯 CURRENT FOCUS: Fix AI optimization issues and deploy to production");
    
    // Git status
    if (projectStatus.git) {
      summary.push(`📝 Git: ${projectStatus.git.branch} branch, ${projectStatus.git.modified_files} modified files`);
    }
    
    // Server status
    if (projectStatus.servers) {
      const backendStatus = projectStatus.servers.backend_running ? "✅" : "❌";
      const frontendStatus = projectStatus.servers.frontend_running ? "✅" : "❌";
      summary.push(`🖥️ Servers: Backend ${backendStatus} Frontend ${frontendStatus}`);
    }
    
    // Key priorities
    summary.push("🚨 IMMEDIATE PRIORITIES:");
    summary.push("  1. Fix OpenAI API key configuration");
    summary.push("  2. Resolve numpy compatibility issue");
    summary.push("  3. Deploy to Railway + Netlify");
    summary.push("  4. Get 20 beta users");
    
    // Success criteria
    summary.push("🎯 SUCCESS CRITERIA:");
    summary.push("  - AI optimization works without fallback");
    summary.push("  - Production deployment successful");
    summary.push("  - 20 beta users providing feedback");
    summary.push("  - Learning data collection active");

    return summary.join('\n');
  }

  updateMasterContextStatus(projectStatus) {
    try {
      const masterContextPath = path.join(this.augmentDir, 'MASTER_CONTEXT.md');
      if (!fs.existsSync(masterContextPath)) return;

      let content = fs.readFileSync(masterContextPath, 'utf8');
      
      // Update the last updated timestamp
      const today = new Date().toISOString().split('T')[0];
      content = content.replace(
        /\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}/,
        `**Last Updated**: ${today}`
      );

      // Update current status section if it exists
      const statusSection = `## Current Status (Auto-Updated)
- **Git Branch**: ${projectStatus.git?.branch || 'unknown'}
- **Modified Files**: ${projectStatus.git?.modified_files || 0}
- **Backend Server**: ${projectStatus.servers?.backend_running ? '✅ Running' : '❌ Stopped'}
- **Frontend Server**: ${projectStatus.servers?.frontend_running ? '✅ Running' : '❌ Stopped'}
- **Last Context Update**: ${new Date().toLocaleString()}

`;

      // Add or update status section
      if (content.includes('## Current Status (Auto-Updated)')) {
        content = content.replace(
          /## Current Status \(Auto-Updated\)[\s\S]*?(?=\n## |\n---|\n$)/,
          statusSection
        );
      } else {
        // Add status section before the file references
        content = content.replace(
          '## File References & Context Sources',
          statusSection + '## File References & Context Sources'
        );
      }

      fs.writeFileSync(masterContextPath, content);
    } catch (error) {
      console.error('❌ Error updating master context status:', error.message);
    }
  }

  generateAugmentPrompt() {
    return `
# Recruitly Context Loaded

I have loaded the complete Recruitly project context including:

📋 **Strategic Documents**:
- Master Context: Project mission, priorities, and decision framework
- Product Vision: 10K user goal and market strategy  
- AI Optimization Plan: Self-improving AI system architecture
- Learning Strategy: Continuous improvement and pattern recognition
- Technical Architecture: Current implementation and roadmap
- Development Roadmap: Phase-by-phase execution plan

🎯 **Current Phase**: 1C - AI Issues Resolution & Deployment Prep

🚨 **Immediate Priorities**:
1. Fix AI optimization issues (OpenAI API key + numpy compatibility)
2. Deploy to production (Railway + Netlify)
3. Get 20 beta users for validation
4. Implement learning data collection system

💡 **Decision Framework**: Every decision evaluated on:
- Business Impact (toward 10K users)
- Learning Opportunity (AI improvement)
- Revenue Potential (monetization)
- User Experience (core optimization flow)

Ready to help with strategic decisions, technical implementation, and execution planning.

What would you like to work on?
`;
  }
}

// Run the context updater
const updater = new AugmentContextUpdater();
updater.updateAugmentContext();

module.exports = AugmentContextUpdater;
