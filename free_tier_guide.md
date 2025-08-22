# Free-Tier Multi-Agent Framework Usage Guide

## 🎯 Overview

This framework combines **generous free tiers** with **local-first tools** to create a cost-effective, unlimited-usage development environment. You'll save $200-500+ monthly compared to paid alternatives while maintaining professional-grade capabilities.

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Clone or set up your repository
git clone <your-repo>
cd <your-repo>

# Run the setup script
chmod +x setup-free-tier.sh
./setup-free-tier.sh

# Initialize the framework
pwsh ./orchestrator.ps1 -Command init

# Check status
pwsh ./orchestrator.ps1 -Command status
```

### 2. Start Your First Lane
```bash
# Start AI coding lane
pwsh ./orchestrator.ps1 -Command start-lane -Lane ai_coding

# This opens VS Code in the lane's worktree
# Work on your code, then submit changes
pwsh ./orchestrator.ps1 -Command submit -Lane ai_coding -Message "Add new feature"
```

## 💰 Cost Optimization Strategy

### Free Tier Maximization

**Primary Free Services (Daily Limits):**
- **Gemini CLI**: 1,000 requests/day (industry's largest free allowance)
- **Codeium**: Unlimited code completion and chat
- **GitHub Actions**: 2,000 minutes/month
- **Amazon Q Developer**: 1,000 requests/month

**Local Fallbacks (Unlimited):**
- **Ollama Models**: Code Llama 7B, Gemini 2B (run locally)
- **Open Source Tools**: All quality/security scanning tools

### Intelligent Service Rotation

The framework automatically:
1. **Tracks quotas** in real-time
2. **Rotates services** when limits approach
3. **Falls back to local models** when all quotas exceeded
4. **Resets counters** daily/monthly as appropriate

```bash
# Check current quota status
pwsh ./orchestrator.ps1 -Command quota-check

# Monitor costs
python .ai/scripts/cost-monitor.py
```

## 🛤️ Lane-Based Workflow

### Available Lanes

Each lane operates in its own Git worktree with specialized tools:

| Lane | Purpose | Primary Tools | File Patterns |
|------|---------|---------------|---------------|
| **ai_coding** | AI-assisted development | Aider + Gemini CLI | `src/**`, `lib/**` |
| **quality** | Code quality assurance | ESLint, Ruff, Black | `**/*.js`, `**/*.py` |
| **security** | Security scanning | Trivy, Semgrep, OWASP | `**/*` |
| **infrastructure** | IaC management | OpenTofu, Checkov | `*.tf`, `infrastructure/**` |
| **documentation** | Auto-documentation | OpenAPI Generator | `docs/**`, `*.md` |

### Lane Operations

```bash
# Start working in a lane
pwsh ./orchestrator.ps1 -Command start-lane -Lane quality

# Submit changes (runs pre-commit checks)
pwsh ./orchestrator.ps1 -Command submit -Lane quality -Message "Fix linting issues"

# Integrate all lanes into main
pwsh ./orchestrator.ps1 -Command integrate
```

## 🤖 AI Service Management

### Service Priority Order

1. **Gemini CLI** (1,000/day free) - Primary choice
2. **Codeium** (unlimited free) - Code completion
3. **Local Ollama** (unlimited) - Fallback for everything
4. **Amazon Q** (1,000/month) - Specialized tasks

### Local Model Setup

```bash
# Install essential models
ollama pull codellama:7b-instruct  # Primary coding
ollama pull codegemma:2b          # Fast completions
ollama pull llama3.1:8b           # General purpose

# Configure Aider for local use
aider --model ollama/codellama:7b-instruct
```

### Smart Usage Patterns

**Peak Hours (9 AM - 5 PM):**
- Use local models to preserve API quotas
- Save API calls for complex reasoning tasks

**Off Hours:**
- Use free API services for faster responses
- Batch similar requests together

**Quota Management:**
```bash
# Check remaining quota before big tasks
pwsh ./orchestrator.ps1 -Command quota-check

# Force local model usage
export USE_LOCAL_ONLY=true
aider --model ollama/codellama:7b-instruct
```

## 🔧 Tool Configuration

### Aider Configuration
```yaml
# .aider.conf.yml
model: ollama/codellama:7b-instruct
edit-format: diff
auto-commits: false
gitignore: true
show-model-warnings: false
```

### VS Code Settings
```json
{
  "continue.telemetryEnabled": false,
  "continue.models": [
    {
      "title": "Code Llama Local",
      "provider": "ollama", 
      "model": "codellama:7b-instruct"
    },
    {
      "title": "Fast Local",
      "provider": "ollama",
      "model": "codegemma:2b"
    }
  ]
}
```

## 🔒 Security & Quality Automation

### Free Security Stack

**Static Analysis:**
```bash
# Run comprehensive security scan
semgrep --config=auto .
bandit -r src/
eslint --ext .js,.ts --config security .
```

**Dependency Scanning:**
```bash
# Check for vulnerabilities
trivy fs .
safety check
npm audit
```

**IaC Security:**
```bash
# Scan infrastructure code
checkov -d infrastructure/
tfsec .
```

### Quality Assurance

**Python Stack:**
```bash
# Lint and format
ruff check --fix .
black .
pylint src/
```

**JavaScript Stack:**
```bash
# Quality pipeline
eslint --fix .
prettier --write .
npm test
```

## 📊 Monitoring & Analytics

### Daily Cost Monitoring

```bash
# Check quota usage
python .ai/scripts/cost-monitor.py

# Sample output:
# 🎯 Quota Status:
#   gemini: 45/1000 (4.5%)
#   codeium: 150 requests (unlimited)
# 💰 Estimated savings today: $1.95
```

### Framework Status Dashboard

```bash
pwsh ./orchestrator.ps1 -Command status

# Shows:
# - Service quotas and usage
# - Lane initialization status  
# - Local model availability
# - Git worktree health
```

## 🎛️ Advanced Usage

### Custom Lane Creation

Add to `.ai/framework-config.json`:
```json
{
  "lanes": {
    "testing": {
      "worktreePath": ".worktrees/testing",
      "branch": "lane/testing", 
      "tools": {
        "primary": {
          "tool": "pytest",
          "config": {"coverage": true}
        }
      },
      "allowedPatterns": ["tests/**", "**/*_test.py"],
      "commitPrefix": "test:"
    }
  }
}
```

### Batch Operations

```bash
# Process multiple lanes
for lane in ai_coding quality security; do
  pwsh ./orchestrator.ps1 -Command submit -Lane $lane -Message "Batch update"
done

# Then integrate
pwsh ./orchestrator.ps1 -Command integrate
```

### CI/CD Integration

```yaml
# .github/workflows/free-tier-ci.yml
name: Free-Tier CI
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run quality checks
        run: |
          ruff check .
          eslint .
          
  security:
    runs-on: ubuntu-latest  
    steps:
      - uses: actions/checkout@v4
      - name: Security scan
        run: |
          trivy fs .
          semgrep --config=auto .
```

## 🚨 Troubleshooting

### Common Issues

**Quota Exceeded:**
```bash
# Check status
pwsh ./orchestrator.ps1 -Command quota-check

# Force local fallback
export USE_LOCAL_ONLY=true
```

**Ollama Connection Issues:**
```bash
# Restart Ollama service
ollama serve

# Check model availability
ollama list
```

**Git Worktree Conflicts:**
```bash
# Reset worktrees
git worktree prune
pwsh ./orchestrator.ps1 -Command init
```

### Performance Optimization

**Local Model Performance:**
- Use `codegemma:2b` for quick completions
- Use `codellama:7b-instruct` for complex generation
- Increase RAM allocation: `ollama serve --max-memory 16GB`

**Network Optimization:**
- Batch API requests when possible
- Use local models during peak hours
- Cache responses locally when applicable

## 💡 Best Practices

### Daily Workflow

1. **Morning:** Check quota status, plan API usage
2. **Development:** Use local models for iteration
3. **Review:** Use API services for final polish
4. **Evening:** Submit lanes and integrate

### Cost Management

- **Track usage** with daily monitoring scripts
- **Rotate services** before hitting limits  
- **Prefer local models** for experimentation
- **Save API calls** for production-ready code

### Quality Assurance

- **Run security scans** on every commit
- **Use pre-commit hooks** in each lane
- **Validate IaC** before deployment
- **Generate docs** automatically

## 📈 Scaling Strategy

### Team Usage

- **Shared quotas:** Pool free tier limits across team
- **Role-based lanes:** Assign lanes by team member expertise
- **Local model sharing:** Set up shared Ollama instance

### Enterprise Migration

- **Gradual transition:** Start with free tiers, upgrade selectively
- **ROI measurement:** Track cost savings vs productivity gains
- **Tool evaluation:** Identify which paid tools provide unique value

---

## 🎉 Success Metrics

With this framework, you should achieve:

- **90%+ cost reduction** vs commercial alternatives
- **Unlimited local usage** with Ollama models
- **Professional security scanning** with open source tools
- **Automated quality assurance** across all code changes
- **Zero vendor lock-in** with open standards

**Monthly Savings Estimate:**
- Claude Pro: $20/month → $0 (use Gemini free + local)
- GitHub Copilot: $10/month → $0 (use Codeium)
- Paid SAST tools: $50-200/month → $0 (use Semgrep + others)
- Infrastructure tools: $100+/month → $0 (use OpenTofu)

**Total Savings: $200-500+ per month** 🎯