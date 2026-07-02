# Intelligent Tool Routing - Decision Tree

## The Routing Engine Flow

```
Input: Files + Prompt + Current Context
         ↓
    Constraint Evaluation
         ↓
    Context Analysis
         ↓
    Tool Selection Algorithm
         ↓
    Optimal Tool Choice
```

## Decision Factors Matrix

| Factor | Weight | Impact on Tool Selection |
|--------|--------|-------------------------|
| **File Count** | High | 1-3 files → aider_local<br>4-8 files → claude_code<br>9+ files → vscode_editor |
| **Total Lines** | High | <500 lines → aider_local<br>500-2000 lines → claude_code<br>2000+ lines → vscode_editor |
| **Complexity** | Medium | Simple refactor → aider_local<br>Architecture change → claude_code<br>Legacy code → vscode_editor |
| **Git State** | Critical | Dirty worktree → vscode_editor (always) |
| **Path Restrictions** | Critical | Outside allowlist → vscode_editor (always) |
| **Quota Status** | Medium | Claude >80% used → aider_local |
| **File Types** | Low | Mixed types → claude_code<br>Pure Python → aider_local |

## Routing Examples

### Example 1: Simple Refactoring
```yaml
Input:
  files: ["src/utils.py"]          # 1 file
  lines: 245                       # Small file
  prompt: "Extract helper method"  # Simple task
  git_clean: true                  # No violations
  
Decision Path:
  ✅ Git state clean
  ✅ Path allowed (src/*.py)
  ✅ File count (1) < limit (12)
  ✅ File size (245 lines) < complex threshold (500)
  ✅ Task complexity: SIMPLE
  
→ Result: aider_local
→ Reasoning: "Small, simple change - local tool optimal"
```

### Example 2: Complex Architecture Change
```yaml
Input:
  files: ["src/auth/*.py", "src/models/*.py"]  # 8 files
  lines: 1847                                  # Large changeset
  prompt: "Implement OAuth2 with JWT refresh" # Complex task
  git_clean: true                              # No violations
  
Decision Path:
  ✅ Git state clean
  ✅ Paths allowed
  ⚠️  File count (8) approaching limit
  ⚠️  Total lines (1847) > complexity threshold
  ⚠️  Task complexity: COMPLEX (architecture keywords)
  
→ Result: claude_code
→ Reasoning: "Large, complex changeset requires sophisticated reasoning"
```

### Example 3: Constraint Violation
```yaml
Input:
  files: ["migrations/001_add_users.py"]  # Restricted path
  lines: 89                               # Small file
  prompt: "Fix column type"               # Simple task
  git_clean: true
  
Decision Path:
  ✅ Git state clean
  ❌ Path violation: migrations/ not in allowlist
  [HARD_BLOCK triggered]
  
→ Result: vscode_editor
→ Reasoning: "Path restriction requires manual review"
```

### Example 4: Quota-Based Fallback
```yaml
Input:
  files: ["src/api/endpoints.py"]  # 1 file
  lines: 892                       # Medium complexity
  prompt: "Add rate limiting"      # Moderate task
  git_clean: true
  claude_quota: 85%                # Near limit
  
Decision Path:
  ✅ Git state clean
  ✅ Path allowed
  ✅ File count OK
  ⚠️  Normally would choose claude_code
  ❌ Claude quota >80% threshold
  
→ Result: aider_local
→ Reasoning: "Quota protection - fallback to local tool"
```

## Smart Routing Rules

### Primary Tool Selection Logic
```python
def select_tool(files, context):
    # Critical violations always route to editor
    if has_hard_violations(files, context):
        return "vscode_editor"
    
    # Calculate complexity score
    complexity_score = (
        file_count_factor(len(files)) +
        size_factor(total_lines(files)) +
        task_complexity_factor(context.prompt) +
        git_complexity_factor(context.git_state)
    )
    
    # Quota-aware selection
    if complexity_score > 70 and quota_available("claude_code"):
        return "claude_code"
    elif complexity_score < 30:
        return "aider_local"
    elif quota_available("claude_code"):
        return "claude_code"
    else:
        return "aider_local"  # Fallback
```

### Context-Aware Adjustments
```yaml
# Time-based routing (save expensive tools for complex work)
time_preferences:
  peak_hours: "09:00-17:00"
  during_peak:
    prefer_local: true
    claude_threshold: 0.6  # Require higher complexity
  
  off_hours: "18:00-08:00"  
  during_off_hours:
    claude_threshold: 0.4  # More liberal usage

# Project-specific routing
project_rules:
  critical_paths:
    - "src/security/**"    # Always require manual review
    - "src/payment/**"     # High-stakes code
  
  safe_paths:
    - "src/utils/**"       # Liberal automation OK
    - "tests/**"           # Testing code
```

## Adaptive Learning (Future Enhancement)

The system can learn from past routing decisions:

```yaml
# Learning metrics tracked
routing_history:
  tool_success_rates:
    aider_local:
      simple_tasks: 0.94      # 94% success rate
      moderate_tasks: 0.78    # 78% success rate
    
    claude_code:
      moderate_tasks: 0.91    # 91% success rate  
      complex_tasks: 0.87     # 87% success rate
  
  user_override_patterns:
    - scenario: "migration files"
      system_choice: "aider_local"
      user_choice: "vscode_editor"
      frequency: 0.89         # User overrides 89% of time
      
# Adaptive thresholds based on success rates
adaptive_routing:
  enabled: true
  adjustment_frequency: "weekly"
  
  threshold_adjustments:
    - metric: "aider_local.moderate_tasks"
      current_success: 0.78
      target_success: 0.85
      action: "increase_complexity_threshold"  # Route more to claude_code
```

## Why This Is "Intelligent"

### 1. **Multi-Factor Analysis**
Doesn't just look at one thing (file count) but considers:
- File characteristics (size, count, type)
- Task complexity (keywords, scope)
- System state (quotas, git status)
- Historical success patterns

### 2. **Context Sensitivity**
Same files might route differently based on:
- What you're trying to do
- Current system state
- Time of day/quota usage
- Previous success patterns

### 3. **Graceful Degradation**
Always has a fallback path:
```
Preferred Tool → Alternative Tool → Manual Editor → Always Works
```

### 4. **Policy-Driven**
All routing logic defined in configuration:
- Easy to tune thresholds
- Add new decision factors
- Override for special cases
- Audit decision reasoning

### 5. **Cost-Aware**
Balances capability with cost:
- Uses expensive tools (Claude Code) when justified
- Falls back to free tools when possible
- Protects against quota exhaustion

## Real-World Scenarios

### Development Team Using the System

**Morning (Fresh quotas, complex work planned):**
```bash
# System routes complex tasks to Claude Code
→ 8 files, architecture change → claude_code
→ 2 files, bug fix → aider_local  
→ 15 files, refactor → vscode_editor (too large)
```

**Afternoon (Quota 70% used, simple tasks):**
```bash
# System conserves premium quota
→ 8 files, architecture change → claude_code (still justified)
→ 2 files, bug fix → aider_local
→ 4 files, feature add → aider_local (normally claude_code)
```

**Late Evening (Quota 95% used):**
```bash
# System preserves remaining quota
→ 8 files, architecture change → aider_local (quota protection)
→ 2 files, bug fix → aider_local
→ Any constraint violation → vscode_editor
```

The system makes these routing decisions **automatically** and **consistently**, optimizing for success rate, cost efficiency, and safety constraints.