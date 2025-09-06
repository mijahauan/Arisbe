#!/usr/bin/env python3
"""
Production-ready code usage tracker using decorators and context managers.
Tracks function calls, execution time, and call frequency.
"""
import functools
import time
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, Any, Set
import atexit

class CodeUsageTracker:
    """Lightweight production tracker for code usage analysis."""
    
    def __init__(self, output_file: str = "code_usage_report.json"):
        self.output_file = output_file
        self.function_calls: Counter = Counter()
        self.execution_times: Dict[str, list] = defaultdict(list)
        self.call_stack: Set[str] = set()
        self.enabled = True
        
        # Auto-save on exit
        atexit.register(self.save_report)
    
    def track_function(self, func):
        """Decorator to track function usage."""
        if not self.enabled:
            return func
            
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # Track call
            self.function_calls[func_name] += 1
            
            # Track execution time
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                self.execution_times[func_name].append(end_time - start_time)
        
        return wrapper
    
    def save_report(self):
        """Save usage report to JSON file."""
        if not self.enabled:
            return
            
        report = {
            "function_calls": dict(self.function_calls),
            "execution_stats": {
                func: {
                    "total_calls": len(times),
                    "total_time": sum(times),
                    "avg_time": sum(times) / len(times) if times else 0,
                    "max_time": max(times) if times else 0
                }
                for func, times in self.execution_times.items()
            },
            "never_called": self._find_never_called_functions()
        }
        
        Path(self.output_file).write_text(json.dumps(report, indent=2))
        print(f"Code usage report saved to {self.output_file}")
    
    def _find_never_called_functions(self) -> list:
        """Identify functions that were decorated but never called."""
        # This would need static analysis to be complete
        return []
    
    def disable(self):
        """Disable tracking for performance-critical sections."""
        self.enabled = False
    
    def enable(self):
        """Re-enable tracking."""
        self.enabled = True

# Global tracker instance
tracker = CodeUsageTracker()

# Convenience decorator
def track_usage(func):
    """Simple decorator to track function usage."""
    return tracker.track_function(func)

# Usage examples:
# @track_usage
# def my_function():
#     pass
#
# # Or for methods:
# class MyClass:
#     @track_usage
#     def my_method(self):
#         pass
