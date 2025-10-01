"""
Shared style fixtures for testing.

Provides pre-built StyleSpecification instances for various test scenarios.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from style_specification import StyleSpecification, load_default_dau_style
from typing import Dict, Any
import copy


def create_default_style() -> StyleSpecification:
    """Load default DAU style."""
    return load_default_dau_style()


def create_large_padding_style() -> StyleSpecification:
    """Create style with large padding values."""
    style = load_default_dau_style()
    # Increase padding values
    style['layout']['padding']['cut_padding'] = 50.0
    style['layout']['padding']['element_padding'] = 30.0
    style['layout']['padding']['min_cut_size'] = 120.0
    return style


def create_small_padding_style() -> StyleSpecification:
    """Create style with minimal padding values."""
    style = load_default_dau_style()
    # Decrease padding values
    style['layout']['padding']['cut_padding'] = 10.0
    style['layout']['padding']['element_padding'] = 5.0
    style['layout']['padding']['min_cut_size'] = 40.0
    return style


def create_high_contrast_style() -> StyleSpecification:
    """Create style with high contrast colors."""
    style = load_default_dau_style()
    style['cuts']['even_cuts']['fill'] = '#FFFFFF'
    style['cuts']['odd_cuts']['fill'] = '#000000'
    style['cuts']['even_cuts']['stroke'] = '#000000'
    style['cuts']['odd_cuts']['stroke'] = '#FFFFFF'
    return style


def create_no_shading_style() -> StyleSpecification:
    """Create style with no polarity shading."""
    style = load_default_dau_style()
    style['cuts']['even_cuts']['opacity'] = 0.0
    style['cuts']['odd_cuts']['opacity'] = 0.0
    return style


# Test style catalog
TEST_STYLES = {
    'default': create_default_style,
    'large_padding': create_large_padding_style,
    'small_padding': create_small_padding_style,
    'high_contrast': create_high_contrast_style,
    'no_shading': create_no_shading_style,
}


def get_test_style(name: str) -> StyleSpecification:
    """
    Get a test style by name.
    
    Args:
        name: One of the keys in TEST_STYLES
        
    Returns:
        StyleSpecification instance
    """
    if name not in TEST_STYLES:
        raise ValueError(f"Unknown test style: {name}. Available: {list(TEST_STYLES.keys())}")
    return TEST_STYLES[name]()
