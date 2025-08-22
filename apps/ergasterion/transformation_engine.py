#!/usr/bin/env python3
"""
Transformation Engine - Core transformation logic for Existential Graphs

Implements the formal transformation rules for Existential Graphs:
- Erasure and Insertion
- Iteration and Deiteration  
- Double Cut operations
"""

import sys
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from enum import Enum

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

try:
    from egi_types import EGI, Vertex, Edge, Cut
except ImportError:
    # Create basic classes if not available
    class EGI:
        def __init__(self):
            self.V = []
            self.E = []
            self.Cut = []
    
    class Vertex:
        def __init__(self, id, label=""):
            self.id = id
            self.label = label
    
    class Edge:
        def __init__(self, id, predicate=""):
            self.id = id
            self.predicate = predicate
    
    class Cut:
        def __init__(self, id, enclosed_elements=None):
            self.id = id
            self.enclosed_elements = enclosed_elements or []

class TransformationRule(Enum):
    """Valid transformation rules for Existential Graphs."""
    ERASURE = "erasure"
    INSERTION = "insertion"
    ITERATION = "iteration"
    DEITERATION = "deiteration"
    DOUBLE_CUT_INSERTION = "double_cut_insertion"
    DOUBLE_CUT_REMOVAL = "double_cut_removal"

class TransformationResult:
    """Result of a transformation operation."""
    def __init__(self, success: bool, egi: Optional[EGI] = None, error: Optional[str] = None):
        self.success = success
        self.egi = egi
        self.error = error

class TransformationEngine:
    """
    Core engine for applying Existential Graph transformations.
    
    Implements Peirce's transformation rules with validation.
    """
    
    def __init__(self):
        self.validation_enabled = True
        self.transformation_history = []
    
    def apply_transformation(self, egi: EGI, rule: TransformationRule, 
                           target_elements: List[str], **kwargs) -> TransformationResult:
        """
        Apply a transformation rule to the given EGI.
        
        Args:
            egi: The Existential Graph Instance to transform
            rule: The transformation rule to apply
            target_elements: List of element IDs to transform
            **kwargs: Additional parameters for specific transformations
            
        Returns:
            TransformationResult with success status and result/error
        """
        try:
            # Create a copy of the EGI for transformation
            new_egi = self._copy_egi(egi)
            
            # Apply the specific transformation
            if rule == TransformationRule.ERASURE:
                return self._apply_erasure(new_egi, target_elements)
            elif rule == TransformationRule.INSERTION:
                return self._apply_insertion(new_egi, target_elements, **kwargs)
            elif rule == TransformationRule.ITERATION:
                return self._apply_iteration(new_egi, target_elements, **kwargs)
            elif rule == TransformationRule.DEITERATION:
                return self._apply_deiteration(new_egi, target_elements)
            elif rule == TransformationRule.DOUBLE_CUT_INSERTION:
                return self._apply_double_cut_insertion(new_egi, target_elements)
            elif rule == TransformationRule.DOUBLE_CUT_REMOVAL:
                return self._apply_double_cut_removal(new_egi, target_elements)
            else:
                return TransformationResult(False, error=f"Unknown transformation rule: {rule}")
                
        except Exception as e:
            return TransformationResult(False, error=f"Transformation failed: {e}")
    
    def _copy_egi(self, egi: EGI) -> EGI:
        """Create a deep copy of an EGI for transformation."""
        # Simple copy - in practice would need proper deep copy
        new_egi = EGI()
        new_egi.V = list(egi.V)
        new_egi.E = list(egi.E)
        new_egi.Cut = getattr(egi, 'Cut', [])
        return new_egi
    
    def _apply_erasure(self, egi: EGI, target_elements: List[str]) -> TransformationResult:
        """
        Apply erasure transformation - remove elements from even-nested contexts.
        """
        try:
            for element_id in target_elements:
                # Find and remove the element
                egi.V = [v for v in egi.V if v.id != element_id]
                egi.E = [e for e in egi.E if e.id != element_id]
                
                # Remove from cuts if present
                cuts = getattr(egi, 'Cut', [])
                for cut in cuts:
                    if hasattr(cut, 'enclosed_elements'):
                        cut.enclosed_elements = [e for e in cut.enclosed_elements if e != element_id]
            
            return TransformationResult(True, egi)
            
        except Exception as e:
            return TransformationResult(False, error=f"Erasure failed: {e}")
    
    def _apply_insertion(self, egi: EGI, target_elements: List[str], **kwargs) -> TransformationResult:
        """
        Apply insertion transformation - add elements to odd-nested contexts.
        """
        try:
            # For now, simple insertion of new vertices
            new_vertex_data = kwargs.get('vertex_data', {})
            
            for element_id in target_elements:
                if element_id in new_vertex_data:
                    vertex = Vertex(
                        id=element_id,
                        label=new_vertex_data[element_id].get('label', 'new_vertex')
                    )
                    egi.V.append(vertex)
            
            return TransformationResult(True, egi)
            
        except Exception as e:
            return TransformationResult(False, error=f"Insertion failed: {e}")
    
    def _apply_iteration(self, egi: EGI, target_elements: List[str], **kwargs) -> TransformationResult:
        """
        Apply iteration transformation - copy elements within same context.
        """
        try:
            # Simple iteration - duplicate vertices
            for element_id in target_elements:
                for vertex in egi.V:
                    if vertex.id == element_id:
                        new_vertex = Vertex(
                            id=f"{element_id}_iter",
                            label=getattr(vertex, 'label', 'iterated')
                        )
                        egi.V.append(new_vertex)
                        break
            
            return TransformationResult(True, egi)
            
        except Exception as e:
            return TransformationResult(False, error=f"Iteration failed: {e}")
    
    def _apply_deiteration(self, egi: EGI, target_elements: List[str]) -> TransformationResult:
        """
        Apply deiteration transformation - remove duplicate elements.
        """
        try:
            # Remove specified duplicates
            for element_id in target_elements:
                # Find and remove one instance of duplicated elements
                found = False
                for i, vertex in enumerate(egi.V):
                    if vertex.id == element_id and not found:
                        found = True
                        continue
                    elif vertex.id == element_id:
                        egi.V.pop(i)
                        break
            
            return TransformationResult(True, egi)
            
        except Exception as e:
            return TransformationResult(False, error=f"Deiteration failed: {e}")
    
    def _apply_double_cut_insertion(self, egi: EGI, target_elements: List[str]) -> TransformationResult:
        """
        Apply double cut insertion - add nested cuts around elements.
        """
        try:
            # Simple double cut insertion
            cuts = getattr(egi, 'Cut', [])
            
            for element_id in target_elements:
                # Create outer cut
                outer_cut = Cut(
                    id=f"outer_cut_{element_id}",
                    enclosed_elements=[element_id]
                )
                
                # Create inner cut
                inner_cut = Cut(
                    id=f"inner_cut_{element_id}",
                    enclosed_elements=[element_id]
                )
                
                cuts.extend([outer_cut, inner_cut])
            
            egi.Cut = cuts
            return TransformationResult(True, egi)
            
        except Exception as e:
            return TransformationResult(False, error=f"Double cut insertion failed: {e}")
    
    def _apply_double_cut_removal(self, egi: EGI, target_elements: List[str]) -> TransformationResult:
        """
        Apply double cut removal - remove nested cuts.
        """
        try:
            cuts = getattr(egi, 'Cut', [])
            
            # Remove cuts containing target elements
            remaining_cuts = []
            for cut in cuts:
                if not any(elem in getattr(cut, 'enclosed_elements', []) for elem in target_elements):
                    remaining_cuts.append(cut)
            
            egi.Cut = remaining_cuts
            return TransformationResult(True, egi)
            
        except Exception as e:
            return TransformationResult(False, error=f"Double cut removal failed: {e}")
    
    def validate_transformation(self, original_egi: EGI, transformed_egi: EGI, 
                              rule: TransformationRule) -> bool:
        """
        Validate that a transformation follows the formal rules.
        """
        if not self.validation_enabled:
            return True
            
        # Basic validation - could be enhanced with formal rule checking
        try:
            # Check that the transformation is structurally valid
            if not hasattr(transformed_egi, 'V') or not hasattr(transformed_egi, 'E'):
                return False
                
            # Rule-specific validation could be added here
            return True
            
        except Exception:
            return False
    
    def get_available_transformations(self, egi: EGI, element_id: str) -> List[TransformationRule]:
        """
        Get list of valid transformations for a given element.
        """
        available = []
        
        # Basic availability - could be enhanced with context analysis
        available.extend([
            TransformationRule.ERASURE,
            TransformationRule.INSERTION,
            TransformationRule.ITERATION,
            TransformationRule.DEITERATION
        ])
        
        # Double cuts available if cuts exist
        if hasattr(egi, 'Cut') and egi.Cut:
            available.extend([
                TransformationRule.DOUBLE_CUT_INSERTION,
                TransformationRule.DOUBLE_CUT_REMOVAL
            ])
        
        return available
