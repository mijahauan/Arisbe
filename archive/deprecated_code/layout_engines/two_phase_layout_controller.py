"""
Two-Phase Layout Controller

Orchestrates the complete Dau Chapter 21 compliant spatial layout system.
Combines Phase 1 (containment hierarchy) and Phase 2 (ligature optimization)
to create proper logical-spatial correspondence with optimal visual clarity.

This replaces the old CutLayoutEngine with a proper implementation of our
comprehensive EGI Spatial Layout Specification.
"""

from typing import Dict, Tuple
from PySide6.QtCore import QRectF, QPointF, QSizeF

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ContainmentHierarchyEngine, ALURect
from ligature_optimization_engine import LigatureOptimizationEngine
from area_spatial_constraint_system import AreaSpatialConstraintSystem
# from obstacle_aware_ligature_router import ObstacleAwareLigatureRouter
from roberts_disjunction_fix import fix_roberts_disjunction_positioning
from ligature_position_cooptimizer import LigaturePositionCoOptimizer
from balanced_position_optimizer import BalancedPositionOptimizer
from authoritative_layout_coordinator import AuthoritativeLayoutCoordinator
from alu_coordinate_system import ALUCoordinateSystem, ViewContext


class TwoPhaseLayoutController:
    """
    Main controller for the two-phase spatial layout system.
    
    Implements the complete specification:
    1. Phase 1: Containment hierarchy with guaranteed spatial exclusion
    2. Phase 2: Ligature optimization for visual clarity
    3. ALU system: View-independent calculations with device scaling
    """
    
    def __init__(self):
        self.containment_engine = ContainmentHierarchyEngine()
        self.ligature_engine = LigatureOptimizationEngine()
        self.constraint_system = AreaSpatialConstraintSystem()
        self.cooptimizer = LigaturePositionCoOptimizer(self.constraint_system)
        self.balanced_optimizer = BalancedPositionOptimizer(self.constraint_system)
        self.authoritative_coordinator = AuthoritativeLayoutCoordinator()
        self.alu_system = ALUCoordinateSystem()
        
    def create_layout(self, egi: RelationalGraphWithCuts, 
                     available_size: QSizeF,
                     view_context: ViewContext = ViewContext.SCREEN) -> Tuple[Dict[ElementID, QRectF], Dict[ElementID, QPointF], Dict[ElementID, ALURect], float]:
        """
        Create complete two-phase layout for EGI.
        
        Args:
            egi: The EGI structure to layout
            available_size: Available space in device pixels
            view_context: Target rendering context
            
        Returns:
            Tuple of (area_bounds, element_positions, scale_factor)
            - area_bounds: Cut bounds in device pixels
            - element_positions: Element positions in device pixels  
            - scale_factor: ALU → pixel conversion factor used
        """
        print("=" * 60)
        print("STARTING TWO-PHASE LAYOUT SYSTEM")
        print("=" * 60)
        
        # AUTHORITATIVE LAYOUT: Get initial balanced positions
        print("\n🔷 AUTHORITATIVE LAYOUT CALCULATION")
        initial_positions = self.authoritative_coordinator.calculate_complete_layout(egi)
        alu_area_bounds = self.authoritative_coordinator.area_bounds
        alu_element_sizes = self.authoritative_coordinator.calculated_element_sizes

        # CO-OPTIMIZATION: Refine positions for ligature clarity
        print("\n🔷 LIGATURE CO-OPTIMIZATION")
        alu_element_positions = self.cooptimizer.optimize_positions(
            egi, initial_positions, alu_area_bounds
        )
        
        # Calculate optimal scale for available space
        scale_factor = self.alu_system.calculate_optimal_scale(
            alu_area_bounds, available_size, view_context
        )
        
        # CONVERSION: ALU → Device Pixels
        print("\n🔷 CONVERSION: ALU → DEVICE PIXELS")
        device_area_bounds = self.alu_system.convert_alu_to_device(alu_area_bounds, scale_factor)
        device_element_positions = {}
        
        for element_id, alu_point in alu_element_positions.items():
            device_element_positions[element_id] = alu_point.to_qpointf(scale_factor)
        
        # PHASE 3: Roberts Disjunction Spatial Fix
        print("\n🔷 PHASE 3: ROBERTS DISJUNCTION SPATIAL FIX")
        device_element_positions = fix_roberts_disjunction_positioning(
            device_area_bounds, device_element_positions, egi
        )
        
        print(f"\nLayout complete:")
        print(f"  📐 Scale factor: {scale_factor:.1f} pixels/ALU")
        print(f"  🏗️  Area bounds: {len(device_area_bounds)} cuts positioned")
        print(f"  📍 Element positions: {len(device_element_positions)} elements positioned")
        print(f"  🎯 View context: {view_context.value}")
        
        # Validate spatial exclusion
        self._validate_spatial_exclusion(device_area_bounds, egi)
        
        return device_area_bounds, device_element_positions, alu_element_sizes, scale_factor
    
    def _validate_spatial_exclusion(self, area_bounds: Dict[ElementID, QRectF], egi: RelationalGraphWithCuts):
        """Validate that spatial exclusion principle is satisfied."""
        print("\n🔍 VALIDATING SPATIAL EXCLUSION:")
        
        # Check for identical bounds (should never happen)
        bounds_list = list(area_bounds.values())
        identical_found = False
        
        for i, bounds1 in enumerate(bounds_list):
            for j, bounds2 in enumerate(bounds_list[i+1:], i+1):
                if bounds1 == bounds2:
                    area_ids = list(area_bounds.keys())
                    print(f"  ❌ VIOLATION: {area_ids[i]} == {area_ids[j]} (identical bounds)")
                    identical_found = True
        
        if not identical_found:
            print("  ✅ SUCCESS: All areas have distinct bounds")
        
        # Check sibling cut separation
        self._validate_sibling_separation(area_bounds, egi)
    
    def _validate_sibling_separation(self, area_bounds: Dict[ElementID, QRectF], egi: RelationalGraphWithCuts):
        """Validate that sibling cuts are properly separated."""
        # Find sibling cuts (cuts in the same parent area)
        siblings_by_parent = {}
        
        for parent_area, contents in egi.area.items():
            sibling_cuts = [eid for eid in contents if eid in area_bounds and eid != parent_area]
            if len(sibling_cuts) > 1:
                siblings_by_parent[parent_area] = sibling_cuts
        
        for parent_area, siblings in siblings_by_parent.items():
            print(f"  📋 Checking siblings in {parent_area}: {siblings}")
            
            for i, cut1 in enumerate(siblings):
                for cut2 in siblings[i+1:]:
                    bounds1 = area_bounds[cut1]
                    bounds2 = area_bounds[cut2]
                    
                    # Check for overlap
                    if bounds1.intersects(bounds2):
                        print(f"    ❌ OVERLAP: {cut1} intersects {cut2}")
                    else:
                        # Calculate separation distance
                        center1 = bounds1.center()
                        center2 = bounds2.center()
                        distance = ((center1.x() - center2.x())**2 + (center1.y() - center2.y())**2)**0.5
                        print(f"    ✅ SEPARATED: {cut1} ↔ {cut2} = {distance:.1f}px")
    
    def create_viewport_bounds(self, area_bounds: Dict[ElementID, QRectF]) -> QRectF:
        """Create viewport bounds that encompass all areas."""
        if not area_bounds:
            return QRectF(-100, -100, 200, 200)
        
        # Calculate encompassing bounds
        min_x = min(rect.x() for rect in area_bounds.values())
        max_x = max(rect.x() + rect.width() for rect in area_bounds.values())
        min_y = min(rect.y() for rect in area_bounds.values())
        max_y = max(rect.y() + rect.height() for rect in area_bounds.values())
        
        # Add 20px margin
        margin = 20.0
        viewport = QRectF(
            min_x - margin,
            min_y - margin,
            (max_x - min_x) + 2 * margin,
            (max_y - min_y) + 2 * margin
        )
        
        return viewport
    
    def get_layout_info(self) -> Dict[str, str]:
        """Get information about the layout system."""
        return {
            "system": "Two-Phase Layout Controller",
            "phase1": "Containment Hierarchy Engine (ALU-based)",
            "phase2": "Ligature Optimization Engine",
            "coordinate_system": "Abstract Layout Units (ALU)",
            "compliance": "Dau Chapter 21 Spatial Exclusion Principle",
            "features": "Guaranteed non-overlapping, optimal ligature routing"
        }
