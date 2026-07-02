#!/bin/bash
# Practical Multi-CLI Framework Implementation
# This works with existing CLI tools without requiring them to "talk" to each other

set -euo pipefail

# Global config
WORKSPACE_ROOT="$(pwd)"
AI_DIR="$WORKSPACE_ROOT/.ai"
TASK_QUEUE="$AI_DIR/task-queue.json"
CONTEXT_DIR="$AI_DIR/context"

# Ensure directories exist
mkdir -p "$AI_DIR" "$CONTEXT_DIR"

# Logging
log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$AI_DIR/orchestrator.log"
}

# Task complexity calculator
calculate_complexity() {
    local files=("$@")
    local score=0
    
    # File count factor (0-30 points)
    score=$((score + ${#files[@]} * 3))
    
    # File size factor (0-40 points)
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            lines=$(wc -l < "$file" 2>/dev/null || echo 0)
            score=$((score + lines / 25))
        fi
    done
    
    # Cap at 100
    if ((score > 100)); then score=100; fi
    echo $score
}

# Intelligent tool router
route_task() {
    local task_desc="$1"
    shift
    local files=("$@")
    
    local complexity=$(calculate_complexity "${files[@]}")
    log "Task complexity: $complexity/100"
    
    # Check constraints
    if (( ${#files[@]} > 10 )); then
        echo "vscode_manual"
        return
    fi
    
    # Route based on complexity
    if (( complexity < 30 )); then
        echo "aider"
    elif (( complexity < 70 )); then
        echo "claude_then_aider"
    else
        echo "copilot_then_claude_then_aider"
    fi
}

# Execute with Aider
execute_aider() {
    local task_desc="$1"
    shift
    local files=("$@")
    
    log "🔧 Executing with Aider: $task_desc"
    
    if command -v aider >/dev/null 2>&1; then
        aider --yes --message "$task_desc" "${files[@]}" 2>&1 | tee "$AI_DIR/aider-output.log"
        return ${PIPESTATUS[0]}
    else
        log "❌ Aider not found"
        return 1
    fi
}

# Execute with Claude Code
execute_claude() {
    local task_desc="$1"
    shift
    local files=("$@")
    
    log "🧠 Executing with Claude Code: $task_desc"
    
    # Create context file
    local context_file="$CONTEXT_DIR/claude-context-$(date +%s).md"
    cat > "$context_file" << EOF
# Task Context

## Description
$task_desc

## Files to modify
$(printf '%s\n' "${files[@]}")

## Instructions
Please analyze and implement the requested changes. Focus on:
1. Understanding the current code structure
2. Making minimal, focused changes
3. Maintaining code quality and consistency

If this task is too complex for a single operation, suggest breaking it down.
EOF

    if command -v claude >/dev/null 2>&1; then
        claude --file "$context_file" "${files[@]}" 2>&1 | tee "$AI_DIR/claude-output.log"
        return ${PIPESTATUS[0]}
    else
        log "❌ Claude Code not found"
        return 1
    fi
}

# Execute with GitHub Copilot
execute_copilot() {
    local task_desc="$1"
    shift
    local files=("$@")
    
    log "🤖 Getting suggestions from GitHub Copilot: $task_desc"
    
    if command -v gh >/dev/null 2>&1 && gh extension list | grep -q copilot; then
        # Generate suggestions
        local suggestions_file="$CONTEXT_DIR/copilot-suggestions-$(date +%s).md"
        echo "# Copilot Suggestions for: $task_desc" > "$suggestions_file"
        echo "" >> "$suggestions_file"
        
        gh copilot suggest "$task_desc for files: $(printf '%s ' "${files[@]}")" >> "$suggestions_file" 2>&1
        
        log "💡 Copilot suggestions saved to: $suggestions_file"
        cat "$suggestions_file"
        return 0
    else
        log "❌ GitHub Copilot CLI not found"
        return 1
    fi
}

# Main orchestration function
orchestrate_task() {
    local task_desc="$1"
    shift
    local files=("$@")
    
    log "🎯 Starting task: $task_desc"
    log "📁 Files: $(printf '%s ' "${files[@]}")"
    
    # Route the task
    local routing_decision=$(route_task "$task_desc" "${files[@]}")
    log "🎲 Routing decision: $routing_decision"
    
    # Execute based on routing
    case "$routing_decision" in
        "aider")
            execute_aider "$task_desc" "${files[@]}"
            ;;
        "claude_then_aider")
            log "📋 Phase 1: Claude analysis"
            if execute_claude "Analyze and plan: $task_desc" "${files[@]}"; then
                log "📋 Phase 2: Aider implementation"
                execute_aider "Implement the planned changes for: $task_desc" "${files[@]}"
            else
                log "⚠️  Claude failed, falling back to Aider only"
                execute_aider "$task_desc" "${files[@]}"
            fi
            ;;
        "copilot_then_claude_then_aider")
            log "📋 Phase 1: Copilot suggestions"
            execute_copilot "$task_desc" "${files[@]}"
            
            log "📋 Phase 2: Claude analysis"
            if execute_claude "Based on the Copilot suggestions, analyze and plan: $task_desc" "${files[@]}"; then
                log "📋 Phase 3: Aider implementation"
                execute_aider "Implement the planned changes for: $task_desc" "${files[@]}"
            else
                log "⚠️  Claude failed, proceeding with Aider based on Copilot suggestions"
                execute_aider "$task_desc" "${files[@]}"
            fi
            ;;
        "vscode_manual")
            log "🚨 Manual intervention required"
            echo "Task complexity or constraints require manual review."
            echo "Files: $(printf '%s ' "${files[@]}")"
            echo "Task: $task_desc"
            echo ""
            echo "Please handle this manually in VS Code."
            return 1
            ;;
        *)
            log "❌ Unknown routing decision: $routing_decision"
            return 1
            ;;
    esac
    
    log "✅ Task orchestration completed"
}

# Status check function
status_check() {
    log "🔍 System Status Check"
    
    echo "Available tools:"
    command -v aider >/dev/null && echo "  ✅ Aider" || echo "  ❌ Aider"
    command -v claude >/dev/null && echo "  ✅ Claude Code" || echo "  ❌ Claude Code"
    command -v gh >/dev/null && echo "  ✅ GitHub CLI" || echo "  ❌ GitHub CLI"
    
    if command -v gh >/dev/null; then
        gh extension list | grep -q copilot && echo "  ✅ GitHub Copilot CLI" || echo "  ❌ GitHub Copilot CLI"
    fi
    
    echo ""
    echo "Git status:"
    if git status --porcelain | grep -q .; then
        echo "  ⚠️  Working directory has uncommitted changes"
    else
        echo "  ✅ Working directory clean"
    fi
}

# Usage function
usage() {
    cat << EOF
Multi-CLI AI Tool Orchestrator

Usage:
  $0 orchestrate "task description" file1 file2 ...
  $0 status
  $0 route "task description" file1 file2 ...  (show routing decision only)

Examples:
  $0 orchestrate "Add error handling" src/auth.py src/middleware.py
  $0 orchestrate "Refactor the user authentication system" src/auth/
  $0 status

The orchestrator will:
1. Analyze task complexity
2. Route to appropriate tool(s)
3. Execute in sequence with context passing
4. Log all operations

EOF
}

# Main script logic
main() {
    case "${1:-}" in
        "orchestrate")
            shift
            if (( $# < 2 )); then
                echo "Error: orchestrate requires task description and at least one file"
                usage
                exit 1
            fi
            orchestrate_task "$@"
            ;;
        "status")
            status_check
            ;;
        "route")
            shift
            if (( $# < 2 )); then
                echo "Error: route requires task description and at least one file"
                usage
                exit 1
            fi
            local task_desc="$1"
            shift
            echo "Routing decision: $(route_task "$task_desc" "$@")"
            ;;
        "help"|"--help"|"-h"|"")
            usage
            ;;
        *)
            echo "Error: Unknown command '$1'"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"