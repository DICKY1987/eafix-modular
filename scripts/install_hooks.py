#!/usr/bin/env python3
"""
Agentic Framework v3.0 - Git Hooks Installer
Installs safety hooks to prevent unsafe commits
"""

import os
import shutil
import subprocess
from pathlib import Path

def install_git_hooks():
    """Install git hooks for safety validation"""
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        print("❌ Not a git repository. Run 'git init' first.")
        return False
    
    git_hooks_dir = Path('.git/hooks')
    scripts_dir = Path('scripts')
    
    # Ensure scripts directory exists
    if not scripts_dir.exists():
        print("❌ Scripts directory not found")
        return False
    
    commit_guard = scripts_dir / 'commit_guard.sh'
    if not commit_guard.exists():
        print("❌ commit_guard.sh not found in scripts/")
        return False
    
    # Install pre-commit hook
    pre_commit_hook = git_hooks_dir / 'pre-commit'
    
    pre_commit_content = f"""#!/bin/bash
# Agentic Framework Pre-commit Hook
# Automatically runs safety checks before commits

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Run the commit guard
"$PROJECT_ROOT/scripts/commit_guard.sh"
"""
    
    try:
        pre_commit_hook.write_text(pre_commit_content)
        # Make executable
        if os.name != 'nt':  # Not Windows
            os.chmod(pre_commit_hook, 0o755)
        
        print("✅ Pre-commit hook installed")
        
        # Install pre-push hook for additional safety
        pre_push_hook = git_hooks_dir / 'pre-push'
        pre_push_content = f"""#!/bin/bash
# Agentic Framework Pre-push Hook
# Final safety check before pushing

echo "🔒 Running pre-push safety checks..."

# Check for any .env or secrets files
if git ls-files | grep -E "\.env$|secrets\.|credentials\.|\.key$|\.pem$"; then
    echo "❌ BLOCKED: Secrets or config files detected in repository"
    echo "   These files should not be committed:"
    git ls-files | grep -E "\.env$|secrets\.|credentials\.|\.key$|\.pem$"
    exit 1
fi

# Check branch protection for main/master
protected_branch=$(git config --get init.defaultBranch || echo "main")
current_branch=$(git branch --show-current)

if [[ "$current_branch" == "$protected_branch" || "$current_branch" == "master" || "$current_branch" == "main" ]]; then
    echo "⚠️  Warning: Pushing directly to $current_branch"
    read -p "   Continue? This should typically be done via Pull Request (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Push cancelled"
        exit 1
    fi
fi

echo "✅ Pre-push checks passed"
"""
        
        pre_push_hook.write_text(pre_push_content)
        if os.name != 'nt':  # Not Windows
            os.chmod(pre_push_hook, 0o755)
        
        print("✅ Pre-push hook installed")
        
        # Install commit-msg hook for message validation
        commit_msg_hook = git_hooks_dir / 'commit-msg'
        commit_msg_content = """#!/bin/bash
# Agentic Framework Commit Message Hook
# Validates commit messages follow good practices

commit_msg_file=$1
commit_msg=$(cat $commit_msg_file)

# Skip if it's a merge commit
if [[ $commit_msg == Merge* ]]; then
    exit 0
fi

# Check minimum length
if [ ${#commit_msg} -lt 10 ]; then
    echo "❌ BLOCKED: Commit message too short (minimum 10 characters)"
    echo "   Current: '$commit_msg'"
    exit 1
fi

# Check maximum length for first line
first_line=$(echo "$commit_msg" | head -n1)
if [ ${#first_line} -gt 72 ]; then
    echo "⚠️  Warning: First line longer than 72 characters (${#first_line})"
    echo "   Consider shortening: '$first_line'"
fi

# Suggest conventional commits format
if ! [[ $first_line =~ ^(feat|fix|docs|style|refactor|test|chore|ci|build|revert)(\(.+\))?:\ .+ ]]; then
    echo "💡 Suggestion: Use conventional commits format:"
    echo "   feat: add new feature"
    echo "   fix: fix a bug" 
    echo "   docs: update documentation"
    echo "   Your message: '$first_line'"
fi

exit 0
"""
        
        commit_msg_hook.write_text(commit_msg_content)
        if os.name != 'nt':  # Not Windows
            os.chmod(commit_msg_hook, 0o755)
        
        print("✅ Commit-msg hook installed")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to install hooks: {e}")
        return False

def setup_gitattributes():
    """Setup .gitattributes for consistent line endings and file handling"""
    
    gitattributes_content = """# Agentic Framework v3.0 - Git Attributes

# Text files
*.py text eol=lf
*.js text eol=lf
*.ts text eol=lf
*.json text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.sh text eol=lf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pdf binary

# Archive files
*.zip binary
*.tar.gz binary

# Database files
*.db binary
*.sqlite binary

# Security - Never diff these files
*.key binary
*.pem binary
*.p12 binary
.env binary
secrets.* binary
credentials.* binary
"""
    
    try:
        Path('.gitattributes').write_text(gitattributes_content)
        print("✅ .gitattributes configured")
        return True
    except Exception as e:
        print(f"❌ Failed to create .gitattributes: {e}")
        return False

def configure_git_settings():
    """Configure git settings for better security"""
    
    try:
        # Configure git to always sign commits (if GPG is available)
        try:
            subprocess.run(['git', 'config', '--global', 'commit.gpgsign', 'true'], 
                         check=False, capture_output=True)
            print("✅ GPG signing enabled (if available)")
        except:
            print("⚠️  GPG not available, commits will not be signed")
        
        # Configure git to use the commit guard for this repo
        subprocess.run(['git', 'config', 'core.hooksPath', '.git/hooks'], 
                      check=True, capture_output=True)
        print("✅ Git hooks path configured")
        
        # Set up better defaults
        subprocess.run(['git', 'config', 'pull.rebase', 'false'], 
                      check=True, capture_output=True)
        subprocess.run(['git', 'config', 'init.defaultBranch', 'main'], 
                      check=True, capture_output=True)
        
        print("✅ Git configuration optimized")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Some git configuration failed: {e}")
        return False

def main():
    """Main installation function"""
    print("🔧 Installing Agentic Framework safety hooks...")
    
    success = True
    
    # Install hooks
    if not install_git_hooks():
        success = False
    
    # Setup gitattributes
    if not setup_gitattributes():
        success = False
    
    # Configure git settings
    if not configure_git_settings():
        success = False
    
    if success:
        print("\n✅ All safety hooks installed successfully!")
        print("🛡️  Your repository is now protected against unsafe commits")
        print("\n📋 What was installed:")
        print("   • Pre-commit hook: Runs safety checks before each commit")
        print("   • Pre-push hook: Final validation before pushing")
        print("   • Commit-msg hook: Validates commit message quality")
        print("   • .gitattributes: Ensures consistent file handling")
        print("   • Git configuration: Optimized security settings")
        
        print("\n🚀 Next steps:")
        print("   1. Test with: git commit -m 'test: verify hooks work'")
        print("   2. View hook logs in .git/hooks/")
        print("   3. Configure your API keys in .env file")
        
    else:
        print("\n❌ Some installations failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())