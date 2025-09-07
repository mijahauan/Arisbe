#!/usr/bin/env python3
"""
Simple execution tracing system to understand what actually runs.
Use TRACE_EXECUTION=1 environment variable to enable.
"""
import os
import functools
from typing import Any, Callable

# Global flag - can be toggled via environment variable
TRACE_ENABLED = os.environ.get('TRACE_EXECUTION', '0') == '1'

def trace_calls(func: Callable) -> Callable:
    """Decorator to trace function calls when TRACE_ENABLED is True."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if TRACE_ENABLED:
            # Get class name if this is a method
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
                print(f"[TRACE] {class_name}.{func.__name__}()")
            else:
                print(f"[TRACE] {func.__name__}()")
        
        return func(*args, **kwargs)
    
    return wrapper

def trace_step(step_name: str):
    """Simple step tracer for inline use."""
    if TRACE_ENABLED:
        print(f"[TRACE] {step_name}")

# Usage examples:
# @trace_calls
# def my_function():
#     pass
#
# def some_method(self):
#     trace_step("Creating graphics item")
#     # ... code ...
