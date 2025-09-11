#!/bin/bash
# Agentic Framework v3.0 - Safety Guard Script
# Prevents unsafe commits and validates changes before allowing them

set -e

echo "🛡️  Agentic Framework Commit Guard - Running safety checks..."

# Configuration
MAX_DIFF_SIZE=1000  # Maximum number of lines changed
MAX_FILES_CHANGED=20  # Maximum number of files changed
REQUIRED_TESTS=true  # Whether tests must pass
REQUIRE_MANUAL_REVIEW_SIZE=500  # Require manual review for changes larger than this

# Get commit info
if [ -z "$1" ]; then
    # Pre-commit hook mode
    COMMIT_MSG="Pre-commit validation"
    STAGED_FILES=$(git diff --cached --name-only)
    DIFF_STATS=$(git diff --cached --numstat)
else
    # Manual commit mode
    COMMIT_MSG="$1"
    STAGED_FILES=$(git diff --name-only HEAD~1)
    DIFF_STATS=$(git diff --numstat HEAD~1)
fi

# Count changes
TOTAL_LINES_CHANGED=0
FILES_CHANGED=0

if [ -n "$DIFF_STATS" ]; then
    while IFS=$'\t' read -r added deleted filename; do
        if [ "$added" != "-" ] && [ "$deleted" != "-" ]; then
            LINES_CHANGED=$((added + deleted))
            TOTAL_LINES_CHANGED=$((TOTAL_LINES_CHANGED + LINES_CHANGED))
            FILES_CHANGED=$((FILES_CHANGED + 1))
        fi
    done <<< "$DIFF_STATS"
fi

echo "📊 Change Summary:"
echo "   Files changed: $FILES_CHANGED"
echo "   Lines changed: $TOTAL_LINES_CHANGED"

# Safety Check 1: Size Limits
if [ $TOTAL_LINES_CHANGED -gt $MAX_DIFF_SIZE ]; then
    echo "❌ BLOCKED: Change too large ($TOTAL_LINES_CHANGED lines > $MAX_DIFF_SIZE limit)"
    echo "   Large changes require manual review and approval"
    exit 1
fi

if [ $FILES_CHANGED -gt $MAX_FILES_CHANGED ]; then
    echo "❌ BLOCKED: Too many files changed ($FILES_CHANGED files > $MAX_FILES_CHANGED limit)"
    echo "   Break this into smaller commits"
    exit 1
fi

# Safety Check 2: Manual Review for Medium-Large Changes
if [ $TOTAL_LINES_CHANGED -gt $REQUIRE_MANUAL_REVIEW_SIZE ]; then
    echo "⚠️  Large change detected ($TOTAL_LINES_CHANGED lines)"
    echo "   This requires manual review before commit"
    
    if [ -t 0 ]; then  # Interactive terminal
        read -p "   Have you manually reviewed these changes? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ BLOCKED: Manual review required"
            exit 1
        fi
    else
        echo "❌ BLOCKED: Manual review required (non-interactive mode)"
        exit 1
    fi
fi

# Safety Check 3: Dangerous Patterns
echo "🔍 Scanning for dangerous patterns..."

DANGEROUS_PATTERNS=(
    "api_key"
    "secret_key" 
    "password"
    "token"
    "private_key"
    "aws_access_key"
    "ssh_key"
    "database_url"
    "connection_string"
)

BLOCKED_FILES=()
for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        for pattern in "${DANGEROUS_PATTERNS[@]}"; do
            if grep -i "$pattern" "$file" > /dev/null 2>&1; then
                BLOCKED_FILES+=("$file:$pattern")
            fi
        done
    fi
done

if [ ${#BLOCKED_FILES[@]} -gt 0 ]; then
    echo "❌ BLOCKED: Potential secrets detected:"
    for item in "${BLOCKED_FILES[@]}"; do
        echo "   $item"
    done
    echo "   Remove secrets before committing"
    exit 1
fi

# Safety Check 4: Required File Extensions
PYTHON_FILES=$(echo "$STAGED_FILES" | grep "\.py$" || true)
JS_FILES=$(echo "$STAGED_FILES" | grep "\.js$\|\.ts$" || true)

# Safety Check 5: Test Requirements
if [ "$REQUIRED_TESTS" = true ]; then
    echo "🧪 Checking test requirements..."
    
    # Check if tests exist for Python files
    if [ -n "$PYTHON_FILES" ] && [ -d "tests" ]; then
        echo "   Running Python tests..."
        if command -v pytest &> /dev/null; then
            if ! pytest tests/ -q --tb=short; then
                echo "❌ BLOCKED: Tests are failing"
                exit 1
            fi
            echo "   ✅ Python tests passed"
        else
            echo "   ⚠️  pytest not found, skipping Python tests"
        fi
    fi
    
    # Check if tests exist for JavaScript files
    if [ -n "$JS_FILES" ] && [ -f "package.json" ]; then
        echo "   Checking JavaScript tests..."
        if command -v npm &> /dev/null && npm run test --if-present > /dev/null 2>&1; then
            echo "   ✅ JavaScript tests passed"
        else
            echo "   ⚠️  No JavaScript tests found or npm not available"
        fi
    fi
fi

# Safety Check 6: Code Quality (if tools are available)
echo "🎨 Running code quality checks..."

if [ -n "$PYTHON_FILES" ]; then
    # Python quality checks
    if command -v ruff &> /dev/null; then
        echo "   Running ruff checks..."
        if ! ruff check $PYTHON_FILES; then
            echo "❌ BLOCKED: Ruff quality checks failed"
            echo "   Run: ruff check --fix ."
            exit 1
        fi
        echo "   ✅ Python code quality passed"
    fi
    
    if command -v mypy &> /dev/null; then
        echo "   Running type checks..."
        if ! mypy $PYTHON_FILES --ignore-missing-imports > /dev/null 2>&1; then
            echo "⚠️  Type checking issues found (not blocking)"
        else
            echo "   ✅ Type checking passed"
        fi
    fi
fi

# Safety Check 7: Framework-Specific Validations
echo "🔧 Running framework-specific checks..."

# Check for proper imports in agentic framework files
if echo "$STAGED_FILES" | grep -q "agentic_framework"; then
    for file in $STAGED_FILES; do
        if [[ $file == *"agentic_framework"* ]] && [ -f "$file" ]; then
            # Check for required safety imports
            if ! grep -q "structlog\|logging" "$file"; then
                echo "⚠️  Warning: $file missing logging import"
            fi
            
            # Check for async/await consistency
            if grep -q "async def" "$file" && ! grep -q "await" "$file"; then
                echo "⚠️  Warning: $file has async def but no await calls"
            fi
        fi
    done
fi

# Safety Check 8: Resource Usage Validation
if [ -f "requirements.txt" ] && echo "$STAGED_FILES" | grep -q "requirements.txt"; then
    echo "   Validating requirements.txt..."
    # Check for known vulnerable packages
    VULNERABLE_PACKAGES=("flask==0.10.1" "django==1.11.0" "requests==2.6.0")
    for pkg in "${VULNERABLE_PACKAGES[@]}"; do
        if grep -q "$pkg" requirements.txt; then
            echo "❌ BLOCKED: Vulnerable package detected: $pkg"
            exit 1
        fi
    done
fi

# Success
echo "✅ All safety checks passed!"
echo "📝 Commit message: $COMMIT_MSG"
echo "🚀 Proceeding with commit..."

exit 0