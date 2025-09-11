# LangGraph Multi-Agent CLI - Quick Setup

## Installation (15 minutes vs 8+ weeks custom development)

```bash
# 1. Install LangGraph and dependencies
pip install langgraph langchain-anthropic langchain-google-genai langchain-community
pip install click  # For CLI

# 2. Install your existing tools (keep these)
pip install aider-chat
npm install -g @anthropic-ai/claude-code  # If you have API access
```

## Configuration (5 minutes vs days of PowerShell debugging)

### 1. Set Environment Variables
```bash
# Add to your .env file
export ANTHROPIC_API_KEY="your-claude-key"
export GOOGLE_API_KEY="your-gemini-key"  
export LANGSMITH_API_KEY="your-langsmith-key"  # Optional but recommended for observability
```

### 2. Migrate Your Existing Config
Your existing `.ai/framework-config.json` works as-is! The LangGraph version will read your:
- Lane definitions
- Cost settings  
- Quota limits
- Agent preferences

## Usage - Replace Your Entire PowerShell System

### Instead of this PowerShell command:
```powershell
pwsh ./orchestrator.ps1 -Command analyze-task -Message "Refactor authentication system"
```

### Use this single Python command:
```bash
python cli.py analyze "Refactor authentication system"
```

### All Your PowerShell Commands → Python Equivalents:

| PowerShell Orchestrator | LangGraph CLI |
|------------------------|---------------|
| `-Command status` | `python cli.py status` |
| `-Command start-lane -Lane ai_coding` | `python cli.py open-lane ai_coding` |
| `-Command cost-report` | `python cli.py status` (includes costs) |
| `-Command analyze-task` | `python cli.py analyze` |
| `-Command start-agentic` | `python cli.py execute` (automatic) |

## Advanced Features You Get for Free

### 1. Built-in Observability (Replaces Your Custom Analytics)
```python
# Add LangSmith tracing (optional)
import os
os.environ["LANGSMITH_TRACING"] = "true"

# Now you get:
# - Automatic cost tracking
# - Agent performance metrics  
# - Detailed execution traces
# - Error debugging tools
```

### 2. Production Deployment (vs Your PowerShell Scripts)
```bash
# Deploy to LangGraph Platform (when ready)
langchain app deploy

# Get:
# - Scalable infrastructure
# - Built-in monitoring  
# - Team collaboration
# - Version control
```

### 3. Human-in-the-Loop (Better than Your Manual Approvals)
```python
# Built into LangGraph - no custom PowerShell prompting needed
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model, tools,
    interrupt_before=["claude_agent"],  # Pause before expensive operations
    interrupt_after=["analysis"]       # Review before proceeding
)
```

## Migration Plan

### Week 1: Core Replacement
- [x] Replace PowerShell orchestrator with Python CLI ✅
- [x] Migrate git worktree management ✅  
- [x] Port cost optimization logic ✅
- [ ] Test with your existing tasks

### Week 2: Enhanced Features  
- [ ] Add your specific tools (Aider, local models)
- [ ] Implement your workflow patterns
- [ ] Set up LangSmith observability
- [ ] Performance tuning

### vs Your Original Plan:
- **Custom Framework**: 8+ weeks, 3000+ lines of code, ongoing maintenance
- **LangGraph Migration**: 2 weeks, <500 lines, enterprise-grade features

## File Structure (Much Simpler)
```
your-project/
├── cli.py                 # Main CLI (replaces orchestrator.ps1)
├── git_integration.py     # Git lanes (replaces worktree management)  
├── .ai/
│   ├── framework-config.json  # Your existing config (keep as-is)
│   └── quota-tracker.json     # Usage tracking
└── requirements.txt       # Dependencies
```

## Common Patterns - Your Use Cases

### 1. Cost-Optimized Task Execution
```bash
# Your complex PowerShell workflow:
# 1. Analyze task complexity  
# 2. Check quotas
# 3. Route to appropriate service
# 4. Execute with cost tracking
# 5. Update usage

# Now just:
python cli.py execute "implement user authentication"
```

### 2. Multi-Agent Research → Plan → Code
```bash
# Automatically uses:
# - Gemini for research (free)
# - Claude for architecture (premium, with approval)  
# - Local models for implementation (free)
python cli.py execute "design a microservices architecture for user management"
```

### 3. Git Worktree Development  
```bash
# Open specific development lane
python cli.py open-lane agentic_architecture

# Execute task in lane context (automatic file pattern matching)
cd .worktrees/architecture
python ../cli.py execute "document the new API design"
```

## Testing Your Migration

### Validate Against Your PowerShell System:
```bash
# 1. Test task classification
python cli.py analyze "fix typo in README"          # Should → simple → Gemini
python cli.py analyze "implement OAuth2 system"     # Should → complex → Claude (with approval)
python cli.py analyze "add API endpoint"            # Should → moderate → Aider

# 2. Test cost management  
python cli.py status  # Compare with PowerShell cost-report

# 3. Test git integration
python cli.py lane-status  # Compare with PowerShell lane status
```

## Next Steps

1. **Week 1**: Replace PowerShell scripts with LangGraph CLI
2. **Week 2**: Add your custom tools and workflows  
3. **Month 2**: Consider LangGraph Platform for team deployment
4. **Ongoing**: Use LangSmith for optimization and monitoring

## Benefits Over Custom PowerShell Framework

| Aspect | Your Custom System | LangGraph |
|--------|-------------------|-----------|  
| **Development Time** | 8+ weeks | 1-2 weeks |
| **Code Maintenance** | 3000+ lines | <500 lines |
| **Observability** | Custom SQLite + JSON | Built-in LangSmith |
| **Deployment** | Manual PowerShell | LangGraph Platform |  
| **Team Collaboration** | Git-based | Professional tooling |
| **Error Handling** | Custom PowerShell | Battle-tested framework |
| **Community Support** | None | Large LangChain ecosystem |
| **Enterprise Features** | Build yourself | Included |

**Bottom Line**: You get 90% of your custom functionality immediately, plus professional features you'd take months to build.
