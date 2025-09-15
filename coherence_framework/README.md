# AI Coherence Framework

**A standalone framework for maintaining codebase coherence when projects exceed AI assistant context windows.**

## The Problem

Large codebases inevitably exceed AI context limits, leading to:
- **Reinventing existing solutions** - AI forgets previously implemented code
- **Architectural drift** - Inconsistent patterns and interfaces  
- **Development excursions** - Getting lost in unproductive paths
- **Quality regression** - No systematic quality maintenance
- **Lost work** - Difficulty recovering from failed experiments

## The Solution

The AI Coherence Framework provides:
- **Context awareness system** - Prevents reinventing solved problems
- **Quality gate automation** - Continuous quality monitoring
- **Smart git workflow** - Graceful recovery from excursions
- **Living documentation** - Always-current system knowledge
- **Integration interfaces** - Standardized patterns for consistency

## Quick Start

### Install the Framework
```bash
pip install ai-coherence-framework
```

### Initialize New Project
```bash
cd your-project
coherence-init
```

### Daily Workflow
```bash
# Start development session
coherence-session start

# Check for existing solutions before coding
coherence-check "polarity calculation for nested structures"

# Auto-commit with smart timing
coherence-commit --auto

# End session cleanly
coherence-session end
```

## Core Components

### 1. Context Awareness System
**Prevents reinventing existing solutions:**
```bash
coherence-check "transformation validation logic"
# 🚨 STOP: Transformation interfaces standardized! Use TransformationContext
# • Check src/integration_interfaces.py for TransformationValidator protocol
# • Use TransformationContext dataclass for parameters
```

### 2. Quality Gate System
**Automated quality monitoring:**
```bash
coherence-check --quality
# 📊 Coverage: 85% ✅
# 🧹 Dead Code: 2% ✅  
# 🔍 Type Coverage: 78% ✅
# 📈 Complexity: 4.2 ✅
# 🔒 Security: 0 issues ✅
# Overall Score: 89/100 ✅
```

### 3. Smart Git Workflow
**Graceful recovery from excursions:**
```bash
# Create checkpoint before risky changes
coherence-commit --checkpoint "trying new architecture"

# Auto-commit every 15 minutes
coherence-commit --auto

# Recovery options when stuck
coherence-commit --recovery
```

### 4. Living Documentation
**Always-current system knowledge:**
- Architecture maps auto-update from code
- Function indexes track all implementations
- Integration patterns documented automatically
- Quality metrics tracked over time

## Installation & Setup

### Prerequisites
- Python 3.8+
- Git repository
- Basic development tools (pip, etc.)

### Install Framework
```bash
# Install from PyPI (when published)
pip install ai-coherence-framework

# Or install from source
git clone https://github.com/ai-coherence/framework.git
cd framework
pip install -e .
```

### Initialize Project
```bash
cd your-project-directory
coherence-init

# This creates:
# - .coherence/ - Framework configuration
# - tools/ - Quality and analysis tools  
# - .git/hooks/ - Pre-commit quality gates
# - .vscode/ - IDE integration
# - Documentation templates
```

## Configuration

### Project-Specific Settings
Edit `.coherence/config.yaml`:
```yaml
project:
  name: "YourProject"
  source_dirs: ["src", "lib"]
  test_dirs: ["tests", "test"]
  
quality:
  coverage_threshold: 80
  complexity_threshold: 10
  dead_code_threshold: 5
  
git:
  auto_commit_interval: 900  # 15 minutes
  branch_prefix: "feature/"
  
context:
  keywords:
    - "your_domain_specific_terms"
    - "important_patterns"
```

### Custom Integration Rules
Add to `.coherence/integration_rules.yaml`:
```yaml
rules:
  - name: "database_access"
    description: "All database access should use Repository pattern"
    trigger_keywords: ["database", "query", "sql"]
    existing_solution: "src/repositories/base_repository.py"
    
  - name: "api_endpoints"
    description: "API endpoints should use FastAPI decorators"
    trigger_keywords: ["endpoint", "route", "api"]
    existing_solution: "src/api/base_router.py"
```

## Usage Examples

### Starting a New Feature
```bash
# 1. Start development session
coherence-session start --feature "user-authentication"

# 2. Check for existing solutions
coherence-check "user authentication and session management"

# 3. Work with automatic safety net
# ... make changes ...
coherence-commit --auto  # Runs every 15 minutes

# 4. Create checkpoint before risky experiment
coherence-commit --checkpoint "trying OAuth integration"

# 5. End session
coherence-session end
```

### Recovering from Failed Experiment
```bash
# See recovery options
coherence-commit --recovery

# Go back to last checkpoint
git reset --hard HEAD~1

# Or branch the failed attempt for later
git checkout -b experiment/failed-oauth
git add -A && git commit -m "🚫 EXCURSION: OAuth attempt"
git checkout feature/user-authentication
```

### Quality Monitoring
```bash
# Full quality report
coherence-check --quality --report

# Fix formatting issues
coherence-check --fix

# Check for dead code
coherence-check --dead-code

# Generate architecture documentation
coherence-check --docs
```

## IDE Integration

### VS Code
The framework automatically creates VS Code tasks:
- **Ctrl+Shift+P** → "Tasks: Run Task" → "Coherence: Context Check"
- **Ctrl+Shift+P** → "Tasks: Run Task" → "Coherence: Quality Check"
- **Ctrl+Shift+P** → "Tasks: Run Task" → "Coherence: Smart Commit"

### Other IDEs
Integration files created for:
- PyCharm (`.idea/` configurations)
- Vim/Neovim (plugin configurations)
- Emacs (package configurations)

## Framework Architecture

### Core Modules
```
coherence_framework/
├── core/
│   ├── context_awareness.py    # Prevents reinvention
│   ├── quality_gates.py        # Automated quality checks
│   ├── smart_git.py            # Intelligent git workflow
│   └── living_docs.py          # Auto-updating documentation
├── analyzers/
│   ├── function_indexer.py     # Catalog all functions
│   ├── coherence_analyzer.py   # Detect disconnected code
│   └── semantic_analyzer.py    # Build knowledge graphs
├── templates/
│   ├── project_structure/      # Standard project layouts
│   ├── git_hooks/             # Pre-commit hooks
│   └── documentation/         # Doc templates
└── cli/
    └── commands.py            # Command-line interface
```

### Extension Points
```python
# Custom analyzers
from coherence_framework import BaseAnalyzer

class CustomDomainAnalyzer(BaseAnalyzer):
    def analyze(self, codebase):
        # Your domain-specific analysis
        pass

# Custom quality gates
from coherence_framework import QualityGate

class CustomQualityGate(QualityGate):
    def check(self, code_changes):
        # Your quality requirements
        pass
```

## Benefits

### For Individual Developers
- **Confidence in experimentation** - Easy recovery from failed attempts
- **Consistent quality** - Automated quality maintenance
- **Efficient development** - Reuse existing solutions instead of reinventing
- **Clear progress tracking** - Living documentation of what's been built

### For Teams
- **Architectural consistency** - Standardized patterns and interfaces
- **Knowledge preservation** - Solutions don't get lost or forgotten
- **Onboarding efficiency** - New developers can quickly understand the system
- **Quality assurance** - Continuous monitoring prevents regression

### For AI-Assisted Development
- **Context preservation** - AI assistants remember existing solutions
- **Pattern enforcement** - Consistent interfaces prevent integration issues
- **Recovery assistance** - Clear paths back to working states
- **Documentation currency** - Always up-to-date system knowledge

## Advanced Features

### Custom Context Rules
Define project-specific patterns:
```python
# .coherence/custom_rules.py
from coherence_framework import ContextRule

class DatabaseAccessRule(ContextRule):
    keywords = ["database", "query", "orm"]
    
    def check(self, task_description):
        return {
            "message": "🚨 Database access should use Repository pattern",
            "existing_solutions": ["src/repositories/"],
            "required_checks": [
                "Check BaseRepository for CRUD operations",
                "Use dependency injection for repository instances"
            ]
        }
```

### Quality Metrics Dashboard
```bash
# Generate web dashboard
coherence-check --dashboard

# Exports to coherence-dashboard.html with:
# - Quality trends over time
# - Architecture evolution
# - Dead code hotspots
# - Integration opportunities
```

### CI/CD Integration
```yaml
# .github/workflows/coherence.yml
name: Coherence Check
on: [push, pull_request]
jobs:
  coherence:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install coherence framework
      run: pip install ai-coherence-framework
    - name: Run coherence checks
      run: coherence-check --ci --threshold 80
```

## Contributing

### Development Setup
```bash
git clone https://github.com/ai-coherence/framework.git
cd framework
pip install -e ".[dev]"
pre-commit install
```

### Running Tests
```bash
pytest tests/
coverage run -m pytest
coverage report
```

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-analyzer`
2. Add tests: `tests/test_new_analyzer.py`
3. Implement feature: `coherence_framework/analyzers/new_analyzer.py`
4. Update documentation: `README.md`, `docs/`
5. Submit pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: https://ai-coherence-framework.readthedocs.io
- **Issues**: https://github.com/ai-coherence/framework/issues
- **Discussions**: https://github.com/ai-coherence/framework/discussions
- **Email**: support@ai-coherence.dev

## Roadmap

### Version 1.1
- [ ] Web dashboard for quality metrics
- [ ] Integration with more IDEs (IntelliJ, Sublime)
- [ ] Custom analyzer plugin system
- [ ] Team collaboration features

### Version 1.2
- [ ] Machine learning for pattern detection
- [ ] Automated refactoring suggestions
- [ ] Integration with project management tools
- [ ] Multi-language support (JavaScript, TypeScript, Java)

### Version 2.0
- [ ] Distributed team coherence
- [ ] Real-time collaboration features
- [ ] Advanced semantic analysis
- [ ] AI-powered architecture recommendations
