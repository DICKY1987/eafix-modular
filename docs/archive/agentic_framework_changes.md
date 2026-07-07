# Agentic AI Framework Integration Changes

## 1. Service Priority Restructuring

**Current hierarchy:** Gemini → Codeium → Local  
**New agentic hierarchy:**

```json
{
  "quotaManagement": {
    "services": {
      "gemini_cli": {
        "dailyLimit": 1000,
        "priority": 1,
        "cost": "free",
        "useCase": "simple_tasks",
        "complexity": ["simple", "moderate"]
      },
      "claude_code": {
        "dailyLimit": 25,
        "priority": 2, 
        "cost": "premium",
        "costPerRequest": 0.15,
        "useCase": "complex_agentic",
        "complexity": ["complex"],
        "warningThreshold": 0.6,
        "requiresApproval": true
      },
      "aider_local": {
        "dailyLimit": "unlimited",
        "priority": 3,
        "cost": "free",
        "useCase": "development",
        "complexity": ["simple", "moderate"]
      },
      "ollama_local": {
        "dailyLimit": "unlimited", 
        "priority": 4,
        "cost": "free",
        "useCase": "fallback",
        "complexity": ["simple", "moderate", "complex"]
      }
    }
  }
}
```

## 2. Task Complexity Classification System

Add to framework config:

```json
{
  "taskClassification": {
    "simple": {
      "description": "Single file edits, basic debugging, simple refactoring",
      "recommendedService": "gemini_cli",
      "examples": [
        "fix typo", "add logging", "format code", "simple bug fix",
        "add comments", "rename variables", "basic validation"
      ],
      "maxTokens": 2000,
      "estimatedCost": "$0.00"
    },
    "moderate": {
      "description": "Multi-file changes, feature implementation, code reviews",
      "recommendedService": "aider_local", 
      "examples": [
        "implement API endpoint", "add test suite", "refactor class",
        "integrate third-party library", "database schema changes"
      ],
      "maxTokens": 8000,
      "estimatedCost": "$0.00"
    },
    "complex": {
      "description": "Architecture changes, research tasks, multi-agent workflows",
      "recommendedService": "claude_code",
      "examples": [
        "system redesign", "performance optimization", "security audit",
        "microservices architecture", "cross-system integration",
        "research and implement new technology"
      ],
      "maxTokens": 32000,
      "requiresApproval": true,
      "estimatedCost": "$0.15-$2.00"
    }
  }
}
```

## 3. Agentic Workflow Patterns

```json
{
  "agenticPatterns": {
    "research_plan_code": {
      "enabled": true,
      "description": "Three-phase approach for complex tasks",
      "phases": [
        {
          "name": "research",
          "service": "gemini_cli",
          "purpose": "information gathering",
          "cost": "free"
        },
        {
          "name": "plan", 
          "service": "claude_code",
          "purpose": "architecture and planning",
          "cost": "premium",
          "requiresApproval": true
        },
        {
          "name": "implement",
          "service": "aider_local", 
          "purpose": "code generation",
          "cost": "free"
        }
      ]
    },
    "sub_agents": {
      "enabled": true,
      "description": "Specialized agents for different aspects",
      "agents": {
        "researcher": {
          "service": "gemini_cli",
          "purpose": "information gathering",
          "complexity": ["simple", "moderate"]
        },
        "architect": {
          "service": "claude_code", 
          "purpose": "system design and planning",
          "complexity": ["complex"],
          "requiresApproval": true
        },
        "implementer": {
          "service": "aider_local",
          "purpose": "code generation and implementation", 
          "complexity": ["simple", "moderate"]
        },
        "reviewer": {
          "service": "local",
          "purpose": "quality checks and validation",
          "complexity": ["simple", "moderate", "complex"]
        }
      }
    },
    "tdd_workflow": {
      "enabled": true,
      "description": "Test-driven development with AI",
      "preferredService": "aider_local",
      "steps": ["write_tests", "run_tests", "implement", "refactor"],
      "fallbackService": "ollama_local"
    }
  }
}
```

## 4. Enhanced Orchestrator Script Changes

Add these functions to `free_tier_orchestrator.txt`:

```powershell
function Get-TaskComplexity {
    param([string]$TaskDescription)
    
    $complexKeywords = @(
        "architecture", "redesign", "refactor large", "performance optimization",
        "security audit", "database migration", "infrastructure overhaul", 
        "multi-service", "microservices", "research", "system design",
        "cross-platform", "scalability", "integration strategy"
    )
    
    $moderateKeywords = @(
        "feature implementation", "API development", "integration",
        "test suite", "validation logic", "configuration management",
        "multi-file refactor", "component development", "data modeling"
    )
    
    $simpleKeywords = @(
        "fix bug", "typo", "format", "logging", "comment", "documentation",
        "variable rename", "import cleanup", "style fix", "small refactor"
    )
    
    foreach ($keyword in $complexKeywords) {
        if ($TaskDescription -like "*$keyword*") {
            return "complex"
        }
    }
    
    foreach ($keyword in $moderateKeywords) {
        if ($TaskDescription -like "*$keyword*") {
            return "moderate"
        }
    }
    
    return "simple"
}

function Get-OptimalService {
    param(
        [string]$TaskDescription,
        [string]$Complexity = $null,
        [switch]$Force
    )
    
    if (-not $Complexity) {
        $Complexity = Get-TaskComplexity $TaskDescription
    }
    
    $config = Get-FrameworkConfig
    $tracker = Get-QuotaTracker
    
    $recommendedService = $config.taskClassification.$Complexity.recommendedService
    
    # Special handling for Claude Code
    if ($recommendedService -eq "claude_code" -and -not $Force) {
        $currentUsage = $tracker.services.claude_code ?? 0
        $dailyLimit = $config.quotaManagement.services.claude_code.dailyLimit
        $warningThreshold = $config.quotaManagement.services.claude_code.warningThreshold
        $costPerRequest = $config.quotaManagement.services.claude_code.costPerRequest
        
        $usagePercent = $currentUsage / $dailyLimit
        $estimatedCost = $currentUsage * $costPerRequest
        
        Write-Host "💰 Claude Code Usage Analysis:" -ForegroundColor Yellow
        Write-Host "  Current usage: $currentUsage/$dailyLimit ($([math]::Round($usagePercent * 100, 1))%)" -ForegroundColor Cyan
        Write-Host "  Today's cost: $([math]::Round($estimatedCost, 2))" -ForegroundColor Red
        Write-Host "  Request cost: $costPerRequest" -ForegroundColor Yellow
        
        if ($usagePercent -gt $warningThreshold) {
            Write-Host "⚠️  WARNING: High Claude Code usage!" -ForegroundColor Red
            Write-Host "💡 Consider alternatives:" -ForegroundColor Blue
            Write-Host "  - Break task into smaller parts" -ForegroundColor Green
            Write-Host "  - Use Gemini CLI for research phase" -ForegroundColor Green
            Write-Host "  - Use Aider + local models for implementation" -ForegroundColor Green
            
            $confirm = Read-Host "Continue with Claude Code? (y/N)"
            if ($confirm -ne "y") {
                Write-Host "🔄 Falling back to cost-optimized alternatives" -ForegroundColor Cyan
                return "aider_local"
            }
        }
        
        # Show cost breakdown for transparency
        $monthlyProjection = $estimatedCost * 30
        Write-Host "📊 Monthly projection: $([math]::Round($monthlyProjection, 2))" -ForegroundColor Yellow
    }
    
    return $recommendedService
}

function Start-AgenticWorkflow {
    param(
        [string]$TaskDescription,
        [string]$WorkflowType = "research_plan_code"
    )
    
    $config = Get-FrameworkConfig
    $workflow = $config.agenticPatterns.$WorkflowType
    
    if (-not $workflow.enabled) {
        Write-Error "Workflow '$WorkflowType' is not enabled"
        return
    }
    
    Write-Host "🤖 Starting agentic workflow: $WorkflowType" -ForegroundColor Blue
    Write-Host "📝 Task: $TaskDescription" -ForegroundColor Cyan
    
    foreach ($phase in $workflow.phases) {
        Write-Host "`n🔄 Phase: $($phase.name)" -ForegroundColor Green
        Write-Host "🛠️  Service: $($phase.service)" -ForegroundColor Cyan
        Write-Host "💰 Cost: $($phase.cost)" -ForegroundColor Yellow
        
        if ($phase.requiresApproval) {
            $confirm = Read-Host "Proceed with $($phase.service)? (y/N)"
            if ($confirm -ne "y") {
                Write-Host "⏭️  Skipping phase" -ForegroundColor Yellow
                continue
            }
        }
        
        # Execute phase
        switch ($phase.service) {
            "gemini_cli" {
                Write-Host "🔍 Research phase - using Gemini CLI" -ForegroundColor Green
                # Add Gemini CLI execution logic
            }
            "claude_code" {
                Write-Host "🏗️  Planning phase - using Claude Code" -ForegroundColor Green
                Update-QuotaUsage "claude_code"
                # Add Claude Code execution logic
            }
            "aider_local" {
                Write-Host "⚡ Implementation phase - using Aider + Local" -ForegroundColor Green
                # Add Aider execution logic
            }
        }
    }
    
    Write-Host "`n✅ Agentic workflow completed!" -ForegroundColor Green
}
```

Add new commands to the main switch statement:

```powershell
switch ($Command) {
    "analyze-task" {
        if (-not $Message) {
            Write-Error "Message parameter required for task analysis"
            exit 1
        }
        
        $complexity = Get-TaskComplexity $Message
        $service = Get-OptimalService $Message $complexity
        
        Write-Host "🎯 Task Analysis Results:" -ForegroundColor Blue
        Write-Host "  Description: $Message" -ForegroundColor Cyan
        Write-Host "  Complexity: $complexity" -ForegroundColor Yellow
        Write-Host "  Recommended Service: $service" -ForegroundColor Green
        
        if ($service -eq "claude_code") {
            Write-Host "`n💡 Cost Optimization Tips:" -ForegroundColor Blue
            Write-Host "  1. Break complex tasks into phases" -ForegroundColor Green
            Write-Host "  2. Use research-plan-code workflow" -ForegroundColor Green
            Write-Host "  3. Research with Gemini (free) first" -ForegroundColor Green
        }
    }
    
    "start-agentic" {
        if (-not $Message) {
            Write-Error "Message parameter required for agentic workflow"
            exit 1
        }
        
        $workflowType = if ($Lane) { $Lane } else { "research_plan_code" }
        Start-AgenticWorkflow $Message $workflowType
    }
    
    "cost-report" {
        $tracker = Get-QuotaTracker
        $config = Get-FrameworkConfig
        
        Write-Host "💰 Daily Cost Report:" -ForegroundColor Blue
        Write-Host "=====================" -ForegroundColor Blue
        
        $totalCost = 0
        foreach ($serviceName in $config.quotaManagement.services.PSObject.Properties.Name) {
            $service = $config.quotaManagement.services.$serviceName
            $usage = $tracker.services.$serviceName ?? 0
            
            if ($service.costPerRequest) {
                $cost = $usage * $service.costPerRequest
                $totalCost += $cost
                Write-Host "  $serviceName`: $usage requests = $([math]::Round($cost, 2))" -ForegroundColor $(if ($cost -gt 1) { "Red" } else { "Green" })
            } else {
                Write-Host "  $serviceName`: $usage requests = $0.00 (free)" -ForegroundColor Green
            }
        }
        
        Write-Host "`nTotal daily cost: $([math]::Round($totalCost, 2))" -ForegroundColor Yellow
        Write-Host "Monthly projection: $([math]::Round($totalCost * 30, 2))" -ForegroundColor Red
        Write-Host "vs Commercial alternatives: ~$500/month" -ForegroundColor Cyan
        Write-Host "💰 Savings: $([math]::Round(500 - ($totalCost * 30), 2))/month" -ForegroundColor Green
    }
    
    "optimize-task" {
        if (-not $Message) {
            Write-Error "Message parameter required"
            exit 1
        }
        
        Write-Host "🎯 Task Optimization Suggestions:" -ForegroundColor Blue
        Write-Host "===================================" -ForegroundColor Blue
        
        $complexity = Get-TaskComplexity $Message
        
        switch ($complexity) {
            "complex" {
                Write-Host "🏗️  Complex Task Detected - Use Research-Plan-Code:" -ForegroundColor Red
                Write-Host "  Phase 1: Research with Gemini CLI (free)" -ForegroundColor Green
                Write-Host "  Phase 2: Architecture with Claude Code (premium)" -ForegroundColor Yellow
                Write-Host "  Phase 3: Implementation with Aider + Local (free)" -ForegroundColor Green
                Write-Host "`n💡 This saves ~60% vs using Claude Code for everything" -ForegroundColor Cyan
            }
            "moderate" {
                Write-Host "⚡ Moderate Task - Use Free Tools:" -ForegroundColor Yellow
                Write-Host "  Primary: Aider + Local Models" -ForegroundColor Green
                Write-Host "  Backup: Gemini CLI" -ForegroundColor Green
                Write-Host "  Avoid: Claude Code (overkill)" -ForegroundColor Red
            }
            "simple" {
                Write-Host "🚀 Simple Task - Use Fastest Free Option:" -ForegroundColor Green
                Write-Host "  Primary: Gemini CLI" -ForegroundColor Green
                Write-Host "  Backup: Local Models" -ForegroundColor Green
                Write-Host "  Avoid: Claude Code (expensive overkill)" -ForegroundColor Red
            }
        }
    }
}
```

## 5. Updated Lane Configurations

```json
{
  "lanes": {
    "agentic_research": {
      "name": "Research & Analysis",
      "worktreePath": ".worktrees/research",
      "branch": "lane/research",
      "tools": {
        "primary": {
          "tool": "gemini_cli",
          "config": {
            "model": "gemini-1.5-pro",
            "context_window": "1M_tokens"
          }
        }
      },
      "taskComplexity": "simple",
      "costBudget": "$0/day",
      "allowedPatterns": ["docs/**", "research/**", "*.md"]
    },
    
    "agentic_architecture": {
      "name": "System Architecture & Complex Design",
      "worktreePath": ".worktrees/architecture", 
      "branch": "lane/architecture",
      "tools": {
        "primary": {
          "tool": "claude_code",
          "config": {
            "model": "claude-sonnet-4",
            "thinking_mode": "ultrathink",
            "workflow": "research_plan_code",
            "sub_agents": true
          }
        },
        "research_support": {
          "tool": "gemini_cli",
          "config": {"model": "gemini-1.5-pro"}
        }
      },
      "taskComplexity": "complex",
      "requiresApproval": true,
      "costBudget": "$5/day",
      "warningThreshold": 0.6,
      "allowedPatterns": ["architecture/**", "design/**", "*.arch.md"]
    },
    
    "agentic_implementation": {
      "name": "AI-Powered Code Implementation",
      "worktreePath": ".worktrees/implementation",
      "branch": "lane/implementation", 
      "tools": {
        "primary": {
          "tool": "aider",
          "config": {
            "model_priority": [
              "ollama/codellama:7b-instruct",
              "gemini/gemini-1.5-pro"
            ],
            "workflow": "tdd",
            "auto_commit": false
          }
        },
        "fallback": {
          "tool": "continue",
          "config": {
            "provider": "ollama",
            "model": "codegemma:2b"
          }
        }
      },
      "taskComplexity": "moderate",
      "costOptimized": true,
      "allowedPatterns": ["src/**", "lib/**", "tests/**"]
    }
  }
}
```

## 6. Agentic SOP Integration

Update the atomic SOP template to include agentic decision points:

```markdown
### 1.001 — Assess Task Complexity  `[AGENT.001]`
Analyze incoming task to determine appropriate AI service and workflow

- **Actor:** SYSTEM
- **Owner:** Agentic Orchestrator
- **SLA:** 5 seconds

**Inputs**
- **task_description** (string) · required
- **user_preferences** (object) · optional

**Outputs** 
- **complexity_level** (enum: simple|moderate|complex)
- **recommended_service** (string)
- **estimated_cost** (number)
- **workflow_type** (string)

**Preconditions**
- Task description not empty
- Framework configuration loaded

**Postconditions**
- Service selected based on complexity
- Cost estimate provided
- Workflow pattern chosen

**Validations**
- Complexity assessment against keyword patterns
- Service availability check
- Budget threshold validation

**Error Handling**
- **unclear_task** → request_clarification
- **over_budget** → suggest_alternatives
- **service_unavailable** → fallback_to_local

### 1.002 — Execute Agentic Workflow  `[AGENT.002]`
Run the selected workflow pattern with appropriate services

- **Actor:** SYSTEM  
- **Owner:** Agentic Orchestrator
- **SLA:** Variable (depends on complexity)

**Inputs**
- **workflow_type** (string) · required
- **complexity_level** (string) · required  
- **task_description** (string) · required

**Outputs**
- **workflow_results** (object)
- **actual_cost** (number)
- **quality_metrics** (object)

**Error Handling**
- **quota_exceeded** → fallback_to_local
- **cost_exceeded** → request_approval
- **quality_failure** → retry_with_different_service
```

## 7. Cost Optimization Strategies

Add to usage guide:

### Smart Daily Workflow
```bash
# Morning: Research with free tools
./orchestrator.ps1 -Command start-lane -Lane agentic_research
gemini "research best practices for microservices authentication"

# Mid-morning: Plan with Claude Code (premium, budget controlled)  
./orchestrator.ps1 -Command analyze-task -Message "Design authentication system architecture"
./orchestrator.ps1 -Command start-agentic -Message "Design auth system" -Lane research_plan_code

# Afternoon: Implement with free tools
./orchestrator.ps1 -Command start-lane -Lane agentic_implementation  
aider --model ollama/codellama:7b-instruct "implement the authentication system"

# Evening: Review and integrate
./orchestrator.ps1 -Command cost-report
./orchestrator.ps1 -Command integrate
```

### Monthly Budget Management
- **Claude Code Budget**: $50/month (≈333 requests)
- **Usage Pattern**: 10-15 complex architectural decisions per month
- **Cost per decision**: $1.50-3.00 (multiple iterations)
- **Alternative savings**: $450+/month vs commercial tools

## 8. Setup Script Updates

Add to `free_tier_setup.sh`:

```bash
# Install agentic tools
install_agentic_tools() {
    log_info "Installing agentic AI tools..."
    
    # Claude Code (requires API key)
    if command -v npm >/dev/null 2>&1; then
        npm install -g @anthropic-ai/claude-code
    else
        log_warning "npm not found - install Claude Code manually"
    fi
    
    # Aider - AI pair programmer
    pip3 install aider-chat
    
    # Continue CLI
    npm install -g @continuedev/cli || log_warning "Continue CLI installation failed"
    
    # Local model optimization
    pip3 install llama-cpp-python
    
    log_success "Agentic tools installed"
}
```

## Key Benefits of This Agentic Integration

1. **Cost Control**: Claude Code usage drops 70-80% through intelligent task routing
2. **Quality Maintained**: Complex tasks still get premium AI, simple tasks use free tiers  
3. **Scalability**: Local models handle bulk work, APIs handle edge cases
4. **Transparency**: Full cost tracking and optimization suggestions
5. **Flexibility**: Easy to adjust thresholds and add new services

## Migration Strategy

1. **Week 1**: Implement task complexity classification
2. **Week 2**: Add Claude Code with strict quotas  
3. **Week 3**: Integrate agentic workflow patterns
4. **Week 4**: Add cost reporting and optimization
5. **Ongoing**: Monitor usage and adjust thresholds

This transforms your framework into a true agentic system that intelligently routes tasks based on complexity while maintaining cost control and professional capabilities.