#!/usr/bin/env python3
"""
Canvas API Contracts and Validation

This module defines and enforces the exact API contracts for all canvas operations
to prevent internal component API mismatches like the 'line_width' vs 'width' issue.

CRITICAL: Every canvas drawing call must be validated through these contracts.
"""

from typing import Dict, Any, List
from pipeline_contracts import ContractViolationError

# Canvas API Specification
CANVAS_API_SPEC = {
    'draw_line': {
        'required_params': ['start', 'end'],
        'optional_params': ['style'],
        'style_keys': {
            'required': [],
            'optional': ['color', 'width', 'line_style'],
            'forbidden': ['line_width']  # Common API mistake
        }
    },
    'draw_circle': {
        'required_params': ['center', 'radius'],
        'optional_params': ['style'],
        'style_keys': {
            'required': [],
            'optional': ['color', 'width', 'fill_color'],
            'forbidden': ['line_width']
        }
    },
    'draw_oval': {
        'required_params': ['x1', 'y1', 'x2', 'y2'],
        'optional_params': ['style'],
        'style_keys': {
            'required': [],
            'optional': ['color', 'width', 'fill_color'],
            'forbidden': ['line_width']
        }
    },
    'draw_text': {
        'required_params': ['text', 'position'],
        'optional_params': ['style'],
        'style_keys': {
            'required': [],
            'optional': ['color', 'font_size', 'bold', 'font_family'],
            'forbidden': []
        }
    }
}

def validate_canvas_call(method_name: str, args: tuple, kwargs: dict) -> None:
    """
    Validate a canvas method call against the API specification.
    
    This catches API mismatches BEFORE they cause silent rendering failures.
    """
    if method_name not in CANVAS_API_SPEC:
        raise ContractViolationError(f"Unknown canvas method: {method_name}")
    
    spec = CANVAS_API_SPEC[method_name]
    
    # Validate style dictionary if present
    style = None
    if 'style' in kwargs:
        style = kwargs['style']
    elif len(args) > len(spec['required_params']) and isinstance(args[-1], dict):
        style = args[-1]
    
    if style is not None:
        validate_canvas_style(method_name, style, spec['style_keys'])

def validate_canvas_style(method_name: str, style: dict, style_spec: dict) -> None:
    """Validate canvas style dictionary against API specification."""
    
    # Check for forbidden keys (common API mistakes)
    forbidden_keys = set(style.keys()) & set(style_spec['forbidden'])
    if forbidden_keys:
        suggestions = {
            'line_width': 'width'  # Common mistake mapping
        }
        suggestion_text = ""
        for key in forbidden_keys:
            if key in suggestions:
                suggestion_text += f" Use '{suggestions[key]}' instead of '{key}'."
        
        raise ContractViolationError(
            f"Canvas {method_name}() API mismatch: forbidden style keys {forbidden_keys}.{suggestion_text} "
            f"Style: {style}"
        )
    
    # Check for unknown keys
    valid_keys = set(style_spec['required'] + style_spec['optional'])
    unknown_keys = set(style.keys()) - valid_keys
    if unknown_keys:
        raise ContractViolationError(
            f"Canvas {method_name}() unknown style keys: {unknown_keys}. "
            f"Valid keys: {valid_keys}. Style: {style}"
        )
    
    # Check for missing required keys
    missing_keys = set(style_spec['required']) - set(style.keys())
    if missing_keys:
        raise ContractViolationError(
            f"Canvas {method_name}() missing required style keys: {missing_keys}. "
            f"Style: {style}"
        )

# Decorator for automatic canvas API validation
def validate_canvas_api(func):
    """Decorator to automatically validate canvas API calls."""
    def wrapper(*args, **kwargs):
        method_name = func.__name__
        try:
            validate_canvas_call(method_name, args, kwargs)
        except ContractViolationError as e:
            raise ContractViolationError(f"Canvas API validation failed in {method_name}(): {e}")
        
        return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

# Canvas API compliance checker
def check_canvas_compliance(canvas_class) -> List[str]:
    """Check if a canvas class complies with the API specification."""
    issues = []
    
    for method_name in CANVAS_API_SPEC.keys():
        if not hasattr(canvas_class, method_name):
            issues.append(f"Missing method: {method_name}")
        elif not callable(getattr(canvas_class, method_name)):
            issues.append(f"Method {method_name} is not callable")
    
    return issues

if __name__ == "__main__":
    print("Canvas API Contracts and Validation")
    print("=" * 40)
    
    # Test the validation system
    print("Testing API validation...")
    
    # Test valid style
    try:
        validate_canvas_style('draw_line', {'color': 'black', 'width': 2.0}, CANVAS_API_SPEC['draw_line']['style_keys'])
        print("✅ Valid style accepted")
    except ContractViolationError as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test invalid style (the exact issue we had)
    try:
        validate_canvas_style('draw_line', {'color': 'black', 'line_width': 2.0}, CANVAS_API_SPEC['draw_line']['style_keys'])
        print("❌ Invalid style was incorrectly accepted")
    except ContractViolationError as e:
        print(f"✅ Invalid style correctly rejected: {e}")
    
    print("\n🎯 Canvas API validation system ready!")
    print("Use this to prevent internal component API mismatches.")
