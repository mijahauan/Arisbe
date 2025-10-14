#!/usr/bin/env python3
"""
Check Plan Staleness - Warn if plan hasn't been reviewed recently

Checks CURRENT_PLAN.md for last review date and warns if stale (>14 days).

USAGE:
    python tools/check_plan_staleness.py
    
Called by git pre-commit hook to remind about plan reviews.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


class PlanStalenessChecker:
    """Checks if development plan needs review."""
    
    def __init__(self, project_root: Path = None, warning_days: int = 14):
        self.project_root = project_root or Path.cwd()
        self.plan_file = self.project_root / "CURRENT_PLAN.md"
        self.warning_days = warning_days
    
    def extract_last_review_date(self) -> datetime:
        """Extract last review date from CURRENT_PLAN.md."""
        if not self.plan_file.exists():
            print(f"⚠️  {self.plan_file} not found")
            return None
        
        with open(self.plan_file, 'r') as f:
            content = f.read()
        
        # Look for patterns like:
        # **Last Updated**: 2025-10-13
        # **Next Review**: 2025-10-20
        # "last_reviewed": "2025-10-13"
        
        patterns = [
            r'\*\*Last Updated\*\*:\s*(\d{4}-\d{2}-\d{2})',
            r'\*\*Next Review\*\*:\s*(\d{4}-\d{2}-\d{2})',
            r'"last_reviewed":\s*"(\d{4}-\d{2}-\d{2})"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                date_str = match.group(1)
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    continue
        
        return None
    
    def check_staleness(self) -> bool:
        """Check if plan is stale. Returns True if OK, False if stale."""
        last_review = self.extract_last_review_date()
        
        if last_review is None:
            print("⚠️  Could not determine plan review date")
            print("   Please update CURRENT_PLAN.md with **Last Updated** date")
            return True  # Don't fail commit, just warn
        
        days_since_review = (datetime.now() - last_review).days
        
        if days_since_review > self.warning_days:
            print("")
            print("⚠️" + "=" * 58)
            print("⚠️  PLAN REVIEW REMINDER")
            print("⚠️" + "=" * 58)
            print(f"⚠️  Last review: {last_review.strftime('%Y-%m-%d')} ({days_since_review} days ago)")
            print(f"⚠️  Recommended review interval: {self.warning_days} days")
            print("⚠️")
            print("⚠️  Please review CURRENT_PLAN.md:")
            print("⚠️  - Are active tasks still relevant?")
            print("⚠️  - Should any tasks be removed?")
            print("⚠️  - Is the plan aligned with current reality?")
            print("⚠️")
            print("⚠️  Update 'Last Updated' date after review")
            print("⚠️" + "=" * 58)
            print("")
            
            # Don't fail commit, just warn
            return True
        
        # Plan is current
        return True
    
    def run(self) -> bool:
        """Run staleness check."""
        return self.check_staleness()


def main():
    """Main entry point."""
    checker = PlanStalenessChecker()
    success = checker.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
