#!/usr/bin/env python3
"""
Recruitly Development Workflow Automation
Handles feature development pipeline with automatic context updates and Git integration
"""

import os
import sys
import json
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class RecruitlyDevWorkflow:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docs_dir = self.project_root / "docs"
        self.scripts_dir = self.project_root / "scripts"
        self.augment_dir = self.project_root / ".augment"
        self.context_file = self.docs_dir / "DEVELOPMENT_CONTEXT.md"
        self.feature_log = self.docs_dir / "FEATURE_LOG.json"
        self.master_context = self.augment_dir / "MASTER_CONTEXT.md"
        self.roadmap_file = self.augment_dir / "ROADMAP.md"

        # Ensure directories exist
        self.docs_dir.mkdir(exist_ok=True)
        self.scripts_dir.mkdir(exist_ok=True)
        self.augment_dir.mkdir(exist_ok=True)

    def start_feature(self, feature_name: str, description: str) -> Dict:
        """Start a new feature development cycle"""
        print(f"🚀 Starting feature: {feature_name}")

        feature_data = {
            "name": feature_name,
            "description": description,
            "start_time": datetime.datetime.now().isoformat(),
            "status": "in_progress",
            "files_changed": [],
            "tests_added": [],
            "documentation_updated": []
        }

        # Load existing features
        features = self._load_feature_log()
        features[feature_name] = feature_data
        self._save_feature_log(features)

        # Create feature branch
        self._run_git_command(f"checkout -b feature/{feature_name}")

        print(f"✅ Feature '{feature_name}' started")
        print(f"📝 Branch: feature/{feature_name}")
        return feature_data

    def update_feature_progress(self, feature_name: str, files_changed: List[str] = None,
                              tests_added: List[str] = None, notes: str = None):
        """Update feature development progress"""
        features = self._load_feature_log()

        if feature_name not in features:
            print(f"❌ Feature '{feature_name}' not found")
            return

        feature = features[feature_name]

        if files_changed:
            feature["files_changed"].extend(files_changed)
        if tests_added:
            feature["tests_added"].extend(tests_added)
        if notes:
            feature.setdefault("notes", []).append({
                "timestamp": datetime.datetime.now().isoformat(),
                "note": notes
            })

        feature["last_updated"] = datetime.datetime.now().isoformat()

        self._save_feature_log(features)
        print(f"📝 Updated progress for feature: {feature_name}")

    def complete_feature(self, feature_name: str, commit_message: str = None) -> bool:
        """Complete feature development and trigger automated workflow"""
        print(f"🎯 Completing feature: {feature_name}")

        features = self._load_feature_log()
        if feature_name not in features:
            print(f"❌ Feature '{feature_name}' not found")
            return False

        feature = features[feature_name]

        # Run tests
        if not self._run_tests():
            print("❌ Tests failed. Feature completion aborted.")
            return False

        # Update documentation
        self._update_context_documentation(feature)

        # Update Augment context
        self._update_augment_context(feature)

        # Update README status
        self._update_readme_status(feature_name)

        # Update roadmap
        self._update_roadmap_progress(feature_name, feature)

        # Commit changes
        commit_msg = commit_message or f"feat: {feature['description']}"
        if not self._commit_and_push(feature_name, commit_msg):
            print("❌ Git operations failed")
            return False

        # Mark feature as complete
        feature["status"] = "completed"
        feature["completion_time"] = datetime.datetime.now().isoformat()
        self._save_feature_log(features)

        print(f"🎉 Feature '{feature_name}' completed successfully!")
        print(f"📚 Documentation updated")
        print(f"🧠 Augment context updated")
        print(f"🗺️ Roadmap progress updated")
        print(f"🔄 Changes committed and pushed to GitHub")

        return True

    def _run_tests(self) -> bool:
        """Run the test suite"""
        print("🧪 Running tests...")

        # Backend tests
        backend_result = self._run_command(
            "python -m pytest",
            cwd=self.project_root / "backend"
        )

        # Frontend tests
        frontend_result = self._run_command(
            "npm test -- --watchAll=false",
            cwd=self.project_root / "frontend"
        )

        if backend_result and frontend_result:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed")
            return False

    def _update_context_documentation(self, feature: Dict):
        """Update the development context documentation"""
        print("📝 Updating context documentation...")

        # Read current context
        if self.context_file.exists():
            content = self.context_file.read_text()
        else:
            content = "# Development Context\n\n"

        # Add feature to completed section
        feature_entry = f"- [x] {feature['name']}: {feature['description']}\n"

        # Update the completed features section
        if "### ✅ Completed (Working 100%)" in content:
            # Find the section and add the feature
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("### 🔄 In Progress"):
                    lines.insert(i, feature_entry)
                    break
            content = '\n'.join(lines)

        # Update last modified timestamp
        content = content.replace(
            "**Last Updated**: 2025-08-26",
            f"**Last Updated**: {datetime.datetime.now().strftime('%Y-%m-%d')}"
        )

        self.context_file.write_text(content)
        print("✅ Context documentation updated")

    def _update_readme_status(self, feature_name: str):
        """Update README.md with latest status"""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return

        content = readme_path.read_text()

        # Update last updated timestamp
        content = content.replace(
            "**Last Updated**: 2025-08-26",
            f"**Last Updated**: {datetime.datetime.now().strftime('%Y-%m-%d')}"
        )

        readme_path.write_text(content)
        print("✅ README.md updated")

    def _update_augment_context(self, feature: Dict):
        """Update Augment context files with feature completion"""
        if not self.master_context.exists():
            return

        content = self.master_context.read_text()

        # Update last updated timestamp
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        content = content.replace(
            "**Last Updated**: 2025-08-27",
            f"**Last Updated**: {today}"
        )

        # Add completed feature to working section
        feature_entry = f"- [x] {feature['name']}: {feature['description']}"

        # Find the working section and add the feature
        if "### ✅ **Working (Verified)**" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "### ✅ **Working (Verified)**" in line:
                    # Find the next section and insert before it
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("### ") and j > i + 1:
                            lines.insert(j, feature_entry)
                            break
                    break
            content = '\n'.join(lines)

        self.master_context.write_text(content)
        print("✅ Augment master context updated")

    def _update_roadmap_progress(self, feature_name: str, feature: Dict):
        """Update roadmap with completed feature"""
        if not self.roadmap_file.exists():
            return

        content = self.roadmap_file.read_text()

        # Update last updated timestamp
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        content = content.replace(
            "**Last Updated**: 2025-08-27",
            f"**Last Updated**: {today}"
        )

        # Mark feature as completed in roadmap
        feature_pattern = f"- [ ] {feature_name}"
        completed_pattern = f"- [x] {feature_name}"

        if feature_pattern in content:
            content = content.replace(feature_pattern, completed_pattern)

        # Update progress indicators
        if "🔄 **In Progress**" in content and feature_name in content:
            # Move from in progress to completed
            content = content.replace(
                f"- [ ] {feature_name}",
                f"- [x] {feature_name}"
            )

        self.roadmap_file.write_text(content)
        print("✅ Roadmap updated")

    def _commit_and_push(self, feature_name: str, commit_message: str) -> bool:
        """Commit changes and push to GitHub"""
        print("📤 Committing and pushing changes...")

        try:
            # Add all changes
            self._run_git_command("add .")

            # Commit with message
            self._run_git_command(f'commit -m "{commit_message}"')

            # Push to origin
            self._run_git_command(f"push origin feature/{feature_name}")

            # Switch back to main and merge
            self._run_git_command("checkout main")
            self._run_git_command(f"merge feature/{feature_name}")
            self._run_git_command("push origin main")

            # Clean up feature branch
            self._run_git_command(f"branch -d feature/{feature_name}")
            self._run_git_command(f"push origin --delete feature/{feature_name}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False

    def _run_git_command(self, command: str):
        """Run a git command"""
        full_command = f"git {command}"
        return self._run_command(full_command)

    def _run_command(self, command: str, cwd: Path = None) -> bool:
        """Run a shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {command}")
            print(f"Error: {e.stderr}")
            return False

    def _load_feature_log(self) -> Dict:
        """Load the feature log"""
        if self.feature_log.exists():
            return json.loads(self.feature_log.read_text())
        return {}

    def _save_feature_log(self, features: Dict):
        """Save the feature log"""
        self.feature_log.write_text(json.dumps(features, indent=2))

    def show_project_status(self) -> Dict:
        """Show current project status"""
        print("📊 Recruitly Project Status")
        print("=" * 30)

        # Git status
        try:
            branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
            status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
            modified_files = len([line for line in status.split('\n') if line.strip()])

            print(f"📝 Git Branch: {branch}")
            print(f"📁 Modified Files: {modified_files}")
        except:
            print("📝 Git: Not available")

        # Feature status
        features = self._load_feature_log()
        active_features = [f for f in features.values() if f.get("status") == "in_progress"]
        completed_features = [f for f in features.values() if f.get("status") == "completed"]

        print(f"🚀 Active Features: {len(active_features)}")
        print(f"✅ Completed Features: {len(completed_features)}")

        if active_features:
            print("\n🔄 Active Features:")
            for feature in active_features:
                print(f"  - {feature['name']}: {feature['description']}")

        # Test status
        print(f"\n🧪 Test Status:")
        backend_tests = self.project_root / "backend" / "tests"
        frontend_tests = self.project_root / "frontend" / "src" / "App.test.tsx"

        print(f"  Backend Tests: {'✅' if backend_tests.exists() else '❌'}")
        print(f"  Frontend Tests: {'✅' if frontend_tests.exists() else '❌'}")

        # Documentation status
        print(f"\n📚 Documentation:")
        docs = [
            "docs/DEVELOPMENT_CONTEXT.md",
            ".augment/MASTER_CONTEXT.md",
            "README.md"
        ]

        for doc in docs:
            doc_path = self.project_root / doc
            print(f"  {doc}: {'✅' if doc_path.exists() else '❌'}")

        return {
            "git_branch": branch if 'branch' in locals() else "unknown",
            "modified_files": modified_files if 'modified_files' in locals() else 0,
            "active_features": len(active_features),
            "completed_features": len(completed_features)
        }

def main():
    parser = argparse.ArgumentParser(description="Recruitly Development Workflow")
    parser.add_argument("action", choices=["start", "update", "complete", "status"],
                       help="Action to perform")
    parser.add_argument("--feature", help="Feature name")
    parser.add_argument("--description", help="Feature description")
    parser.add_argument("--files", nargs="*", help="Files changed")
    parser.add_argument("--tests", nargs="*", help="Tests added")
    parser.add_argument("--notes", help="Progress notes")
    parser.add_argument("--message", help="Commit message")

    args = parser.parse_args()

    workflow = RecruitlyDevWorkflow()

    if args.action == "start":
        if not args.feature or not args.description:
            print("❌ Feature name and description required for starting a feature")
            sys.exit(1)
        workflow.start_feature(args.feature, args.description)

    elif args.action == "update":
        if not args.feature:
            print("❌ Feature name required for updating progress")
            sys.exit(1)
        workflow.update_feature_progress(
            args.feature,
            files_changed=args.files,
            tests_added=args.tests,
            notes=args.notes
        )

    elif args.action == "complete":
        if not args.feature:
            print("❌ Feature name required for completing feature")
            sys.exit(1)
        success = workflow.complete_feature(args.feature, args.message)
        sys.exit(0 if success else 1)

    elif args.action == "status":
        workflow.show_project_status()

if __name__ == "__main__":
    main()
