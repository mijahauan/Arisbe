#!/bin/bash
# Arisbe Coherence Framework Shell Aliases
# Add these to your ~/.bashrc or ~/.zshrc to get automatic reminders

# Core coherence framework commands
alias arisbe-status='python tools/daily_quality_dashboard.py'
alias arisbe-api='echo "📚 Opening API reference..." && open ARISBE_CORE_API_REFERENCE.md'
alias arisbe-guide='echo "🚀 Opening usage guide..." && open CORE_API_USAGE_GUIDE.md'
alias arisbe-protect='python tools/core_protection_system.py --report'
alias arisbe-remind='python tools/coherence_reminder_system.py'

# Enhanced development commands with reminders
alias arisbe-test='python tools/coherence_reminder_system.py testing && python -m pytest'
alias arisbe-commit='python tools/coherence_reminder_system.py commit && git commit'
alias arisbe-push='python tools/coherence_reminder_system.py push && git push'

# Quick API lookup
arisbe-find() {
    if [ -z "$1" ]; then
        echo "Usage: arisbe-find <function_name>"
        echo "Example: arisbe-find create_vertex"
        return 1
    fi
    echo "🔍 Searching for '$1' in API documentation..."
    grep -n -i "$1" ARISBE_CORE_API_REFERENCE.md | head -10
}

# Quick coherence check
arisbe-check() {
    echo "🔒 ARISBE COHERENCE FRAMEWORK STATUS"
    echo "=================================="
    python tools/core_protection_system.py --report | head -15
    echo ""
    echo "📊 QUALITY STATUS:"
    python tools/daily_quality_dashboard.py | grep -E "(Overall Status|Total Tests|Passed|Failed)"
}

# Installation instructions
arisbe-install-aliases() {
    echo "To install these aliases permanently:"
    echo "1. Add this to your ~/.bashrc or ~/.zshrc:"
    echo "   source $(pwd)/COHERENCE_SHELL_ALIASES.sh"
    echo "2. Reload your shell: source ~/.bashrc (or ~/.zshrc)"
    echo ""
    echo "Available commands after installation:"
    echo "  arisbe-status    - Show quality dashboard"
    echo "  arisbe-api       - Open API reference"
    echo "  arisbe-guide     - Open usage guide"
    echo "  arisbe-protect   - Show protection status"
    echo "  arisbe-remind    - Show framework reminder"
    echo "  arisbe-test      - Run tests with reminder"
    echo "  arisbe-commit    - Commit with reminder"
    echo "  arisbe-find      - Find function in API docs"
    echo "  arisbe-check     - Quick coherence status"
}

# Show installation instructions when sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    arisbe-install-aliases
fi
