#!/usr/bin/env python3
"""
Coherence Framework Reminder System

This system automatically reminds developers about the coherence framework
when they perform common development tasks, helping prevent "framework amnesia".
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

class CoherenceReminderSystem:
    """Reminds developers about coherence framework capabilities."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.reminder_file = self.project_root / ".coherence_reminder_state"
        self.last_reminder_threshold = timedelta(hours=4)  # Remind every 4 hours
        
    def should_show_reminder(self) -> bool:
        """Check if we should show a reminder based on time elapsed."""
        if not self.reminder_file.exists():
            return True
            
        try:
            with open(self.reminder_file, 'r') as f:
                state = json.load(f)
            
            last_reminder = datetime.fromisoformat(state.get('last_reminder', '2000-01-01'))
            return datetime.now() - last_reminder > self.last_reminder_threshold
            
        except Exception:
            return True
    
    def update_reminder_state(self):
        """Update the last reminder timestamp."""
        state = {
            'last_reminder': datetime.now().isoformat(),
            'reminder_count': self.get_reminder_count() + 1
        }
        
        try:
            with open(self.reminder_file, 'w') as f:
                json.dump(state, f)
        except Exception:
            pass  # Fail silently
    
    def get_reminder_count(self) -> int:
        """Get the number of times reminders have been shown."""
        if not self.reminder_file.exists():
            return 0
            
        try:
            with open(self.reminder_file, 'r') as f:
                state = json.load(f)
            return state.get('reminder_count', 0)
        except Exception:
            return 0
    
    def show_coherence_reminder(self, context: str = "development"):
        """Show a coherence framework reminder."""
        if not self.should_show_reminder():
            return
        
        print("\n" + "="*60)
        print("🧠 COHERENCE FRAMEWORK REMINDER")
        print("="*60)
        print("📚 FORGOT THE API? Check: ARISBE_CORE_API_REFERENCE.md")
        print("🔍 NEED USAGE EXAMPLES? See: CORE_API_USAGE_GUIDE.md")
        print("🛡️ CORE PROTECTION ACTIVE: 16 modules, 87 tests validated")
        print("📊 SYSTEM STATUS: python tools/daily_quality_dashboard.py")
        print("="*60)
        print(f"Context: {context} | Reminder #{self.get_reminder_count() + 1}")
        print("="*60 + "\n")
        
        self.update_reminder_state()
    
    def show_api_discovery_hint(self, error_context: str = None):
        """Show specific API discovery hints."""
        print("\n🔍 API DISCOVERY HINT:")
        print("Instead of guessing function signatures, check:")
        print("  📖 ARISBE_CORE_API_REFERENCE.md - Complete API documentation")
        print("  🚀 CORE_API_USAGE_GUIDE.md - Usage patterns and examples")
        
        if error_context:
            print(f"  💡 Context: {error_context}")
        print()
    
    def show_testing_reminder(self):
        """Show testing-related reminders."""
        print("\n🧪 TESTING REMINDER:")
        print("  ✅ 87 core tests are validated and must pass")
        print("  🔧 Run core tests: python -m pytest tests/test_*_comprehensive.py")
        print("  📊 Quality check: python tools/quality_gate_system.py")
        print()
    
    def show_protection_reminder(self):
        """Show core protection reminders."""
        print("\n🛡️ CORE PROTECTION REMINDER:")
        print("  🔒 16 core modules are protected from unauthorized changes")
        print("  📋 Check status: python tools/core_protection_system.py --report")
        print("  ⚠️  Core changes require explicit authorization")
        print()

def main():
    """Main entry point for reminder system."""
    reminder_system = CoherenceReminderSystem()
    
    # Determine context from command line args
    context = "general"
    if len(sys.argv) > 1:
        context = sys.argv[1]
    
    # Show appropriate reminder based on context
    if context == "api":
        reminder_system.show_api_discovery_hint()
    elif context == "testing":
        reminder_system.show_testing_reminder()
    elif context == "protection":
        reminder_system.show_protection_reminder()
    else:
        reminder_system.show_coherence_reminder(context)

if __name__ == "__main__":
    main()
