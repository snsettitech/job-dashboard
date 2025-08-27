#!/usr/bin/env python3
"""
Automated Git Commit and Push System for Recruitly
Triggers when features are 100% complete and tested locally
"""

import os
import sys
import subprocess
import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

class AutoCommitSystem:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docs_dir = self.project_root / "docs"
        self.commit_log = self.docs_dir / "COMMIT_LOG.json"
        
    def check_feature_ready(self, feature_name: str) -> bool:
        """Check if feature is ready for commit (100% complete and tested)"""
        print(f"🔍 Checking if feature '{feature_name}' is ready for commit...")
        
        # Check if tests pass
        if not self._run_tests():
            print("❌ Tests not passing - feature not ready")
            return False
        
        # Check if backend is running
        if not self._check_backend_health():
            print("❌ Backend not healthy - feature not ready")
            return False
        
        # Check if frontend builds
        if not self._check_frontend_build():
            print("❌ Frontend build fails - feature not ready")
            return False
        
        print("✅ Feature is ready for commit")
        return True
    
    def auto_commit_feature(self, feature_name: str, description: str, 
                          files_changed: List[str] = None) -> bool:
        """Automatically commit and push a completed feature"""
        print(f"🚀 Auto-committing feature: {feature_name}")
        
        if not self.check_feature_ready(feature_name):
            return False
        
        # Generate commit message
        commit_message = self._generate_commit_message(feature_name, description)
        
        # Update documentation
        self._update_documentation(feature_name, description)
        
        # Perform git operations
        if not self._git_commit_and_push(commit_message, files_changed):
            return False
        
        # Log the commit
        self._log_commit(feature_name, description, commit_message)
        
        print(f"🎉 Feature '{feature_name}' successfully committed and pushed!")
        return True
    
    def _run_tests(self) -> bool:
        """Run comprehensive test suite"""
        print("🧪 Running test suite...")
        
        # Backend tests
        backend_test = self._run_command(
            ["python", "-m", "pytest", "-v"],
            cwd=self.project_root / "backend"
        )
        
        # Frontend tests
        frontend_test = self._run_command(
            ["npm", "test", "--", "--watchAll=false", "--coverage"],
            cwd=self.project_root / "frontend"
        )
        
        # API integration test
        api_test = self._test_api_integration()
        
        all_passed = backend_test and frontend_test and api_test
        
        if all_passed:
            print("✅ All tests passed")
        else:
            print("❌ Some tests failed")
            
        return all_passed
    
    def _check_backend_health(self) -> bool:
        """Check if backend is running and healthy"""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_frontend_build(self) -> bool:
        """Check if frontend builds successfully"""
        return self._run_command(
            ["npm", "run", "build"],
            cwd=self.project_root / "frontend"
        )
    
    def _test_api_integration(self) -> bool:
        """Test API integration"""
        try:
            import requests
            
            # Test main endpoints
            endpoints = [
                "http://localhost:8000/",
                "http://localhost:8000/health",
                "http://localhost:8000/api/dashboard"
            ]
            
            for endpoint in endpoints:
                response = requests.get(endpoint, timeout=5)
                if response.status_code not in [200, 404]:  # 404 is ok for some endpoints
                    return False
            
            return True
        except:
            return False
    
    def _generate_commit_message(self, feature_name: str, description: str) -> str:
        """Generate conventional commit message"""
        # Determine commit type
        if "fix" in feature_name.lower() or "bug" in feature_name.lower():
            commit_type = "fix"
        elif "test" in feature_name.lower():
            commit_type = "test"
        elif "doc" in feature_name.lower():
            commit_type = "docs"
        elif "refactor" in feature_name.lower():
            commit_type = "refactor"
        else:
            commit_type = "feat"
        
        # Generate message
        message = f"{commit_type}: {description}"
        
        # Add scope if applicable
        if "backend" in feature_name.lower():
            message = f"{commit_type}(backend): {description}"
        elif "frontend" in feature_name.lower():
            message = f"{commit_type}(frontend): {description}"
        elif "ai" in feature_name.lower():
            message = f"{commit_type}(ai): {description}"
        
        return message
    
    def _update_documentation(self, feature_name: str, description: str):
        """Update project documentation"""
        print("📝 Updating documentation...")
        
        # Update development context
        context_file = self.docs_dir / "DEVELOPMENT_CONTEXT.md"
        if context_file.exists():
            content = context_file.read_text()
            
            # Add to completed features
            new_feature = f"- [x] {feature_name}: {description}"
            
            # Find the completed section and add the feature
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "### ✅ Completed (Working 100%)" in line:
                    # Find the next section and insert before it
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("### "):
                            lines.insert(j, new_feature)
                            break
                    break
            
            # Update timestamp
            content = '\n'.join(lines)
            content = content.replace(
                "**Last Updated**: 2025-08-26",
                f"**Last Updated**: {datetime.datetime.now().strftime('%Y-%m-%d')}"
            )
            
            context_file.write_text(content)
        
        # Update README if needed
        readme_file = self.project_root / "README.md"
        if readme_file.exists():
            content = readme_file.read_text()
            content = content.replace(
                "**Last Updated**: 2025-08-26",
                f"**Last Updated**: {datetime.datetime.now().strftime('%Y-%m-%d')}"
            )
            readme_file.write_text(content)
    
    def _git_commit_and_push(self, commit_message: str, files_changed: List[str] = None) -> bool:
        """Perform git commit and push operations"""
        print("📤 Committing and pushing to GitHub...")
        
        try:
            # Add files
            if files_changed:
                for file in files_changed:
                    self._run_git_command(["add", file])
            else:
                self._run_git_command(["add", "."])
            
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.project_root,
                capture_output=True
            )
            
            if result.returncode == 0:
                print("ℹ️ No changes to commit")
                return True
            
            # Commit
            self._run_git_command(["commit", "-m", commit_message])
            
            # Push to origin
            self._run_git_command(["push", "origin", "main"])
            
            print("✅ Successfully committed and pushed to GitHub")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False
    
    def _run_git_command(self, args: List[str]):
        """Run a git command"""
        return subprocess.run(
            ["git"] + args,
            cwd=self.project_root,
            check=True,
            capture_output=True,
            text=True
        )
    
    def _run_command(self, args: List[str], cwd: Path = None) -> bool:
        """Run a command and return success status"""
        try:
            result = subprocess.run(
                args,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {' '.join(args)}")
            print(f"Error: {e.stderr}")
            return False
    
    def _log_commit(self, feature_name: str, description: str, commit_message: str):
        """Log the commit for tracking"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "feature_name": feature_name,
            "description": description,
            "commit_message": commit_message,
            "status": "success"
        }
        
        # Load existing log
        if self.commit_log.exists():
            log_data = json.loads(self.commit_log.read_text())
        else:
            log_data = {"commits": []}
        
        log_data["commits"].append(log_entry)
        
        # Keep only last 50 commits
        log_data["commits"] = log_data["commits"][-50:]
        
        self.commit_log.write_text(json.dumps(log_data, indent=2))

def main():
    if len(sys.argv) < 3:
        print("Usage: python auto-commit.py <feature_name> <description>")
        sys.exit(1)
    
    feature_name = sys.argv[1]
    description = sys.argv[2]
    files_changed = sys.argv[3:] if len(sys.argv) > 3 else None
    
    auto_commit = AutoCommitSystem()
    success = auto_commit.auto_commit_feature(feature_name, description, files_changed)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
