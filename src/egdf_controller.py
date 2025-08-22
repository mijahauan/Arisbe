#!/usr/bin/env python3
"""
EGDF Controller - Platform Communication and Interactive Constraints

This controller supports both static rendering and interactive graph composition:

Static Mode (Platform Independence):
- Load complete EGDF documents
- Render spatial primitives to any platform
- Validate platform output against EGDF specifications

Interactive Mode (Ergasterion Integration):
- Real-time constraint enforcement for graph composition
- Support for practice mode, endoporeutic game, and Organon
- Incremental updates and validation during editing
- Live feedback for interactive graph manipulation

Key Responsibilities:
1. Load and validate EGDF documents
2. Communicate spatial primitives to platform adapters
3. Validate platform output against EGDF specifications
4. Enforce interactive constraints for graph composition
5. Provide real-time feedback for Ergasterion tools
"""

from typing import Dict, List, Tuple, Any, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import yaml

from egdf_parser import EGDFDocument, LayoutElement
from egi_core_dau import RelationalGraphWithCuts
from canonical.contracts import enforce_canonical_contract, CanonicalContractValidator


class PlatformAdapter(Protocol):
    """Protocol for platform-specific rendering adapters."""
    
    def render_spatial_primitive(self, primitive: Dict[str, Any]) -> bool:
        """Render a single spatial primitive. Returns success status."""
        ...
    
    def get_rendered_bounds(self, element_id: str) -> Optional[Tuple[float, float, float, float]]:
        """Get actual rendered bounds for validation."""
        ...
    
    def clear_canvas(self) -> None:
        """Clear the rendering canvas."""
        ...


@dataclass
class ValidationResult:
    """Result of EGDF validation against platform output."""
    is_valid: bool
    violations: List[str]
    element_count: int
    validated_elements: List[str]


class EGDFController:
    """Controller for EGDF document management and platform rendering with interactive constraints."""
    
    def __init__(self):
        self.platform_adapters: Dict[str, PlatformAdapter] = {}
        self.current_egdf: Optional[EGDFDocument] = None
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        self.spatial_primitives: List[Dict[str, Any]] = []
        
        # Interactive constraint support
        self.constraint_system = None
        self.interactive_mode = False
        self.real_time_feedback_enabled = False
        
    @enforce_canonical_contract(
        input_types={"egdf_doc": EGDFDocument},
        contract_name="EGDF Controller Load"
    )
    def load_egdf_document(self, egdf_doc: EGDFDocument) -> bool:
        """Load and validate EGDF document with canonical contracts."""
        try:
            # Validate EGDF document structure
            CanonicalContractValidator.validate_egdf_document(egdf_doc, "EGDF Controller Load")
            
            # Extract EGI from EGDF for validation
            from egdf_parser import EGDFParser
            parser = EGDFParser()
            self.current_egi = parser.extract_egi_from_egdf(egdf_doc)
            
            # Store EGDF document
            self.current_egdf = egdf_doc
            
            # Extract spatial primitives
            self.spatial_primitives = egdf_doc.visual_layout.get('spatial_primitives', [])
            if not self.spatial_primitives:
                # Try elements format
                elements = egdf_doc.visual_layout.get('elements', [])
                self.spatial_primitives = [self._layout_element_to_primitive(elem) for elem in elements]
            
            print(f"✅ EGDF Controller: Loaded document with {len(self.spatial_primitives)} spatial primitives")
            return True
            
        except Exception as e:
            print(f"❌ EGDF Controller: Failed to load document - {e}")
            return False
    
    def register_platform_adapter(self, platform_name: str, adapter: PlatformAdapter) -> None:
        """Register a platform adapter (Qt, LaTeX, etc.)."""
        self.platform_adapters[platform_name] = adapter
        print(f"✅ EGDF Controller: Registered {platform_name} adapter")
    
    def render_to_platform(self, platform_name: str) -> bool:
        """Render EGDF to specified platform with validation."""
        if platform_name not in self.platform_adapters:
            print(f"❌ EGDF Controller: Platform {platform_name} not registered")
            return False
        
        if not self.current_egdf or not self.spatial_primitives:
            print(f"❌ EGDF Controller: No EGDF document loaded")
            return False
        
        adapter = self.platform_adapters[platform_name]
        
        try:
            # Clear platform canvas
            adapter.clear_canvas()
            
            # Render each spatial primitive
            rendered_count = 0
            for primitive in self.spatial_primitives:
                if adapter.render_spatial_primitive(primitive):
                    rendered_count += 1
                else:
                    print(f"⚠️ EGDF Controller: Failed to render primitive {primitive.get('element_id', 'unknown')}")
            
            print(f"✅ EGDF Controller: Rendered {rendered_count}/{len(self.spatial_primitives)} primitives to {platform_name}")
            return rendered_count == len(self.spatial_primitives)
            
        except Exception as e:
            print(f"❌ EGDF Controller: Rendering to {platform_name} failed - {e}")
            return False
    
    def validate_platform_output(self, platform_name: str, tolerance: float = 1.0) -> ValidationResult:
        """Validate that platform output accords with EGDF specifications."""
        if platform_name not in self.platform_adapters:
            return ValidationResult(False, [f"Platform {platform_name} not registered"], 0, [])
        
        if not self.spatial_primitives:
            return ValidationResult(False, ["No EGDF spatial primitives loaded"], 0, [])
        
        adapter = self.platform_adapters[platform_name]
        violations = []
        validated_elements = []
        
        try:
            for primitive in self.spatial_primitives:
                element_id = primitive.get('element_id')
                expected_bounds = primitive.get('bounds')
                
                if not element_id or not expected_bounds:
                    violations.append(f"Primitive missing element_id or bounds: {primitive}")
                    continue
                
                # Get actual rendered bounds from platform
                actual_bounds = adapter.get_rendered_bounds(element_id)
                
                if actual_bounds is None:
                    violations.append(f"Element {element_id} not found in platform output")
                    continue
                
                # Validate bounds within tolerance
                if not self._bounds_match(expected_bounds, actual_bounds, tolerance):
                    violations.append(
                        f"Element {element_id} bounds mismatch: "
                        f"expected {expected_bounds}, got {actual_bounds}"
                    )
                    continue
                
                validated_elements.append(element_id)
            
            is_valid = len(violations) == 0
            print(f"{'✅' if is_valid else '❌'} EGDF Controller: Validation {'passed' if is_valid else 'failed'} "
                  f"({len(validated_elements)}/{len(self.spatial_primitives)} elements valid)")
            
            return ValidationResult(is_valid, violations, len(self.spatial_primitives), validated_elements)
            
        except Exception as e:
            return ValidationResult(False, [f"Validation error: {e}"], 0, [])
    
    def export_egdf_yaml(self, filepath: str) -> bool:
        """Export current EGDF document to YAML."""
        if not self.current_egdf:
            return False
        
        try:
            egdf_dict = {
                'metadata': {
                    'title': self.current_egdf.metadata.title,
                    'description': self.current_egdf.metadata.description,
                    'generator': self.current_egdf.metadata.generator
                },
                'canonical_egi': self.current_egdf.canonical_egi,
                'visual_layout': self.current_egdf.visual_layout
            }
            
            with open(filepath, 'w') as f:
                yaml.dump(egdf_dict, f, default_flow_style=False, indent=2)
            
            print(f"✅ EGDF Controller: Exported YAML to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ EGDF Controller: YAML export failed - {e}")
            return True
    
    def export_egdf_json(self, filepath: str) -> bool:
        """Export current EGDF document to JSON."""
        if not self.current_egdf:
            return False
        
        try:
            egdf_dict = {
                'metadata': {
                    'title': self.current_egdf.metadata.title,
                    'description': self.current_egdf.metadata.description,
                    'generator': self.current_egdf.metadata.generator
                },
                'canonical_egi': self.current_egdf.canonical_egi,
                'visual_layout': self.current_egdf.visual_layout
            }
            
            with open(filepath, 'w') as f:
                json.dump(egdf_dict, f, indent=2)
            
            print(f"✅ EGDF Controller: Exported JSON to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ EGDF Controller: JSON export failed - {e}")
            return False
    
    def _layout_element_to_primitive(self, element: LayoutElement) -> Dict[str, Any]:
        """Convert LayoutElement to spatial primitive dictionary."""
        return {
            'element_id': element.element_id,
            'element_type': element.element_type,
            'position': element.position,
            'bounds': element.bounds,
            'metadata': element.metadata or {}
        }
    
    def _bounds_match(self, expected: Tuple[float, float, float, float], 
                     actual: Tuple[float, float, float, float], 
                     tolerance: float) -> bool:
        """Check if bounds match within tolerance."""
        return all(abs(e - a) <= tolerance for e, a in zip(expected, actual))
    
    # Interactive Constraint Methods for Ergasterion Integration
    
    def enable_interactive_mode(self, constraint_system=None):
        """Enable interactive mode for graph composition and real-time editing."""
        self.interactive_mode = True
        self.constraint_system = constraint_system
        self.real_time_feedback_enabled = True
        
    def disable_interactive_mode(self):
        """Disable interactive mode, return to static rendering only."""
        self.interactive_mode = False
        self.constraint_system = None
        self.real_time_feedback_enabled = False
    
    def validate_graph_operation(self, operation_type: str, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a proposed graph operation against constraints."""
        if not self.interactive_mode or not self.constraint_system:
            return {"valid": True, "message": "Interactive mode disabled"}
        
        # Delegate to constraint system for validation
        return self.constraint_system.validate_operation(operation_type, element_data)
    
    def apply_graph_operation(self, operation_type: str, element_data: Dict[str, Any]) -> bool:
        """Apply a validated graph operation and update rendering."""
        if not self.interactive_mode:
            return False
            
        # Apply operation and trigger incremental update
        success = self._apply_operation_to_egi(operation_type, element_data)
        if success and self.real_time_feedback_enabled:
            self._trigger_incremental_render()
        
        return success
    
    def get_real_time_feedback(self, cursor_position: Tuple[float, float]) -> Dict[str, Any]:
        """Get real-time feedback for cursor position during interactive editing."""
        if not self.interactive_mode or not self.constraint_system:
            return {}
            
        return self.constraint_system.get_cursor_feedback(cursor_position, self.current_egi)
    
    def _apply_operation_to_egi(self, operation_type: str, element_data: Dict[str, Any]) -> bool:
        """Apply operation to current EGI structure."""
        # Implementation depends on operation type
        # This would modify self.current_egi and regenerate spatial primitives
        return True
    
    def _trigger_incremental_render(self):
        """Trigger incremental rendering update for all registered platforms."""
        for platform_name in self.platform_adapters:
            self.render_to_platform(platform_name)


# Factory function for clean instantiation
def create_egdf_controller() -> EGDFController:
    """Create a new EGDF controller instance."""
    return EGDFController()
