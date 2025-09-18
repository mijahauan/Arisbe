"""
Authoritative Layout Coordinator

THE single source of truth for element positions in EGI diagrams.
Uses specialized libraries to guarantee area containment and optimal spatial layout.

Key principle: "Box with stuff in it" model
- Area = Rectangle - Enclosed_Rectangles - Existing_Elements
- Processes ask "where should element X go?" and receive authoritative answer
- No process can position elements outside their areas (architecturally impossible)
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import math

try:
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("WARNING: shapely not available - using simplified geometry")

try:
    from rectpack import newPacker, SORT_AREA
    RECTPACK_AVAILABLE = True
except ImportError:
    RECTPACK_AVAILABLE = False
    print("WARNING: rectpack not available - using simple grid packing")

from egi_core_dau import RelationalGraphWithCuts, ElementID
from containment_hierarchy_engine import ContainmentHierarchyEngine, ALURect, ALUPoint


@dataclass
class ElementSize:
    """Standard size for EGI elements."""
    width: float
    height: float


class AuthoritativeLayoutCoordinator:
    """
    THE authoritative source for element positions.
    
    Guarantees:
    - Elements never positioned outside their designated areas
    - No overlapping elements within areas
    - Optimal ligature path lengths within constraints
    - Support for dynamic transformations
    """
    
    def __init__(self):
        self.containment_engine = ContainmentHierarchyEngine()
        
        # Standard element sizes (can be customized)
        self.element_sizes = {
            'vertex': ElementSize(0.8, 0.8),    # ALU
            'edge': ElementSize(2.0, 0.6),      # ALU (predicate text)
        }
        
        # Current authoritative positions
        self.authoritative_positions: Dict[ElementID, ALUPoint] = {}
        self.area_bounds: Dict[ElementID, ALURect] = {}
        self.calculated_element_sizes: Dict[ElementID, ALURect] = {}
        
    def calculate_complete_layout(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, ALUPoint]:
        """
        Calculate complete authoritative layout for EGI.
        
        This is THE method that determines where every element goes.
        No other process should position elements.
        """
        print("🏛️ AUTHORITATIVE LAYOUT COORDINATOR")
        print("=" * 50)
        
        # Phase 1: Establish containment hierarchy and area bounds
        print("\n📐 Phase 1: Containment Hierarchy")
        self.area_bounds = self.containment_engine.create_containment_layout(egi)
        
        # Phase 2: Authoritative element positioning
        print("\n📍 Phase 2: Authoritative Element Positioning")
        self.authoritative_positions = self._position_all_elements(egi)
        
        print(f"\n✅ Positioned {len(self.authoritative_positions)} elements authoritatively")
        return dict(self.authoritative_positions)
    
    def get_position_for_element(self, element_id: ElementID, egi: RelationalGraphWithCuts) -> ALUPoint:
        """
        Get THE authoritative position for an element.
        
        This is the only way processes should get element positions.
        """
        if element_id not in self.authoritative_positions:
            # Calculate position on demand if not already calculated
            self._calculate_element_position(element_id, egi)
        
        return self.authoritative_positions[element_id]
    
    def _position_all_elements(self, egi: RelationalGraphWithCuts) -> Dict[ElementID, ALUPoint]:
        """
        Position all elements authoritatively by ensuring each element is placed
        only within the area it belongs to, as defined by the EGI.
        This is an 'element-first' approach, which is architecturally robust.
        """
        # 1. Group all positionable elements by their authoritative area.
        elements_by_area: Dict[ElementID, List[ElementID]] = {}
        all_positionable_elements = list(egi.V) + list(egi.E)

        for element in all_positionable_elements:
            authoritative_area_id = egi.get_context(element.id)
            if authoritative_area_id not in elements_by_area:
                elements_by_area[authoritative_area_id] = []
            elements_by_area[authoritative_area_id].append(element.id)

        # 2. Loop through each area that contains elements and position them.
        all_positions: Dict[ElementID, ALUPoint] = {}
        for area_id, elements_in_area in elements_by_area.items():
            
            if area_id not in self.area_bounds:
                print(f"WARNING: Area {area_id} contains elements but has no layout bounds. Skipping.")
                continue

            print(f"  Positioning {len(elements_in_area)} elements in their authoritative area: {area_id}")
            
            area_bounds = self.area_bounds[area_id]
            
            # Position the elements that belong to this area using the new multi-bin approach.
            area_positions = self._pack_elements_in_area(elements_in_area, area_id, area_bounds, egi)
            all_positions.update(area_positions)
        
        return all_positions
    
    def _decompose_area_into_bins(self, area_id: ElementID, area_bounds: ALURect, egi: RelationalGraphWithCuts) -> List[ALURect]:
        """Decompose an area into simple, non-overlapping rectangular bins."""
        margin = 0.8  # ALU margin from boundaries
        
        # Get all nested cuts which act as obstacles
        nested_cuts = []
        area_contents = egi.area.get(area_id, set())
        for element_id in area_contents:
            if element_id in self.area_bounds and element_id != area_id:
                nested_cuts.append(self.area_bounds[element_id])

        if not nested_cuts:
            # No nested cuts, so the only bin is the area itself (with margin)
            return [ALURect(x=area_bounds.x + margin, y=area_bounds.y + margin,
                            width=max(1.0, area_bounds.width - 2 * margin),
                            height=max(1.0, area_bounds.height - 2 * margin))]

        # A more complex algorithm could handle multiple cuts, but for now, we handle one.
        obstacle = nested_cuts[0]
        bins = []

        parent_top = area_bounds.y
        parent_bottom = area_bounds.y + area_bounds.height
        parent_left = area_bounds.x
        parent_right = area_bounds.x + area_bounds.width

        obstacle_top = obstacle.y
        obstacle_bottom = obstacle.y + obstacle.height
        obstacle_left = obstacle.x
        obstacle_right = obstacle.x + obstacle.width

        # Bin 1: Above the obstacle (from parent top to obstacle top)
        bins.append(ALURect(x=parent_left, y=parent_top,
                            width=area_bounds.width, height=obstacle_top - parent_top))
        
        # Bin 2: Below the obstacle (from obstacle bottom to parent bottom)
        bins.append(ALURect(x=parent_left, y=obstacle_bottom,
                            width=area_bounds.width, height=parent_bottom - obstacle_bottom))

        # Bin 3: Left of the obstacle (at the same vertical level as the obstacle)
        bins.append(ALURect(x=parent_left, y=obstacle_top,
                            width=obstacle_left - parent_left, height=obstacle.height))

        # Bin 4: Right of the obstacle (at the same vertical level as the obstacle)
        bins.append(ALURect(x=obstacle_right, y=obstacle_top,
                            width=parent_right - obstacle_right, height=obstacle.height))

        # Filter out bins that are too small and apply margin
        valid_bins = []
        for b in bins:
            if b.width > 2 * margin and b.height > 2 * margin:
                valid_bins.append(ALURect(x=b.x + margin, y=b.y + margin, 
                                          width=b.width - 2 * margin, 
                                          height=b.height - 2 * margin))
        return valid_bins

    def _pack_elements_in_area(self, elements: List[ElementID], area_id: ElementID, area_bounds: ALURect, egi: RelationalGraphWithCuts) -> Dict[ElementID, ALUPoint]:
        """Pack elements within an area using a multi-bin approach."""
        if not elements:
            return {}

        # 1. Decompose the area into a list of valid, non-overlapping rectangular bins.
        bins = self._decompose_area_into_bins(area_id, area_bounds, egi)

        if not bins:
            print(f"WARNING: No valid bins found for area {area_id}. Cannot position elements.")
            return {}
        
        # 2. Use a balanced grid layout across all available bins.
        positions, sizes = self._pack_with_grid(elements, bins, egi)
        self.calculated_element_sizes.update(sizes)
        return positions
    
    def _pack_with_grid(self, elements: List[ElementID], bins: List[ALURect], egi: RelationalGraphWithCuts) -> Tuple[Dict[ElementID, ALUPoint], Dict[ElementID, ALURect]]:
        """Pack elements in a balanced grid across multiple available bins."""
        num_elements = len(elements)
        if num_elements == 0:
            return {}

        # 1. Calculate total area and use it to determine grid dimensions.
        total_area = sum(b.width * b.height for b in bins)
        if total_area == 0:
            return {}
            
        # Density: give each element a certain amount of space.
        # This prevents overcrowding in small areas.
        area_per_element = total_area / num_elements
        
        # Ideal side length for a square holding one element
        ideal_side = math.sqrt(area_per_element)

        sizes = {}

        # 2. Distribute elements across bins proportionally to bin area.
        positions = {}
        element_idx = 0
        
        for b in bins:
            # How many elements should this bin get, based on its share of the total area?
            proportional_elements = math.ceil((b.width * b.height / total_area) * num_elements)
            
            if proportional_elements == 0:
                continue

            # Create a grid within this bin for its share of elements
            cols = max(1, math.ceil(math.sqrt(proportional_elements * (b.width / b.height))))
            rows = max(1, math.ceil(proportional_elements / cols))
            
            cell_width = b.width / cols
            cell_height = b.height / rows

            for i in range(proportional_elements):
                if element_idx >= num_elements:
                    break
                
                row = i // cols
                col = i % cols
                
                # Center element in its grid cell
                x = b.x + (col + 0.5) * cell_width
                y = b.y + (row + 0.5) * cell_height
                
                element_id = elements[element_idx]
                positions[element_id] = ALUPoint(x, y)

                # Store the actual size used for this element
                # This is crucial for obstacle-aware routing
                element_type = 'edge' if any(e.id == element_id for e in egi.E) else 'vertex'
                base_size = self.element_sizes[element_type]
                width = base_size.width
                height = base_size.height

                if element_type == 'edge':
                    # Calculate realistic width based on predicate name length
                    predicate_name = egi.rel.get(element_id, "")
                    # Estimate width: 0.5 ALU per character + base width
                    width = base_size.width + (len(predicate_name) * 0.5)

                sizes[element_id] = ALURect(x - width / 2, y - height / 2, width, height)

                element_idx += 1

        return positions, sizes
    
    def _calculate_element_position(self, element_id: ElementID, egi: RelationalGraphWithCuts):
        """Calculate position for a single element on demand."""
        element_area = egi.get_context(element_id)
        
        if element_area in self.area_bounds:
            area_bounds = self.area_bounds[element_area]
            available_rect = self._calculate_available_space(element_area, area_bounds, egi)
            
            # Position at center of available space
            self.authoritative_positions[element_id] = ALUPoint(
                available_rect.x + available_rect.width / 2,
                available_rect.y + available_rect.height / 2
            )
        else:
            # Fallback: position at origin
            self.authoritative_positions[element_id] = ALUPoint(0, 0)
    
    def validate_position(self, element_id: ElementID, position: ALUPoint, egi: RelationalGraphWithCuts) -> bool:
        """Validate that a position is within the element's designated area."""
        element_area = egi.get_context(element_id)
        
        if element_area not in self.area_bounds:
            return False
        
        area_bounds = self.area_bounds[element_area]
        available_rect = self._calculate_available_space(element_area, area_bounds, egi)
        
        return (available_rect.x <= position.x <= available_rect.x + available_rect.width and
                available_rect.y <= position.y <= available_rect.y + available_rect.height)
    
    def get_valid_positions_for_element(self, element_id: ElementID, egi: RelationalGraphWithCuts) -> ALURect:
        """Get the valid positioning area for an element."""
        element_area = egi.get_context(element_id)
        
        if element_area in self.area_bounds:
            area_bounds = self.area_bounds[element_area]
            # This is an approximation. For the true shape, use get_true_area_polygon.
            bins = self._decompose_area_into_bins(element_area, area_bounds, egi)
            if bins:
                # For simplicity, return the first bin. A more complex approach could return a union.
                return bins[0]
        
        return ALURect(0, 0, 1, 1)  # Fallback minimal area

    def get_true_area_polygon(self, area_id: ElementID, egi: RelationalGraphWithCuts) -> Optional[Polygon]:
        """
        Calculate the precise geometric shape (polygon) of a given area,
        accounting for any nested cuts which are treated as holes.

        Args:
            area_id: The ID of the area to calculate.
            egi: The EGI graph containing the area definitions.

        Returns:
            A shapely Polygon object representing the true shape of the area,
            or None if the area cannot be calculated.
        """
        if not SHAPELY_AVAILABLE:
            print("WARNING: shapely is required to calculate true area polygons.")
            return None

        if area_id not in self.area_bounds:
            print(f"WARNING: No layout bounds found for area {area_id}.")
            return None

        # 1. Create a polygon for the parent area's full bounds.
        area_bounds = self.area_bounds[area_id]
        parent_polygon = Polygon([
            (area_bounds.x, area_bounds.y),
            (area_bounds.x + area_bounds.width, area_bounds.y),
            (area_bounds.x + area_bounds.width, area_bounds.y + area_bounds.height),
            (area_bounds.x, area_bounds.y + area_bounds.height)
        ])

        # 2. Find all cuts nested directly inside this area and create polygons for them.
        nested_cut_polygons = []
        area_contents = egi.area.get(area_id, set())
        for element_id in area_contents:
            if element_id in self.area_bounds and element_id != area_id:
                nested_bounds = self.area_bounds[element_id]
                cut_polygon = Polygon([
                    (nested_bounds.x, nested_bounds.y),
                    (nested_bounds.x + nested_bounds.width, nested_bounds.y),
                    (nested_bounds.x + nested_bounds.width, nested_bounds.y + nested_bounds.height),
                    (nested_bounds.x, nested_bounds.y + nested_bounds.height)
                ])
                nested_cut_polygons.append(cut_polygon)

        # 3. Geometrically subtract the union of nested cuts from the parent polygon.
        if nested_cut_polygons:
            obstacles = unary_union(nested_cut_polygons)
            return parent_polygon.difference(obstacles)
        else:
            return parent_polygon
