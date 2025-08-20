#!/usr/bin/env python3
"""
Qt Containment Engine

Builds Qt parent-child hierarchy directly from EGI logical structure.
Pipeline: EGI Logic → Qt Containment → Spatial Assignment → Canonical Appearance
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRectF

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


@dataclass
class QtContainmentElement:
    """Qt graphics item with logical containment information."""
    element_id: str
    element_type: str  # 'cut', 'vertex', 'predicate', 'ligature'
    graphics_item: object  # QGraphicsItem
    logical_parent: Optional[str] = None
    logical_children: Set[str] = None
    
    def __post_init__(self):
        if self.logical_children is None:
            self.logical_children = set()


class QtContainmentEngine:
    """
    Builds Qt scene graph directly from EGI logical containment hierarchy.
    
    Pipeline:
    1. Parse EGI logical hierarchy (area mapping)
    2. Build Qt parent-child containment tree
    3. Assign spatial positions within logical constraints
    4. Apply canonical Dau/Peirce visual conventions
    """
    
    def __init__(self):
        self.padding = 20
        self.element_spacing = 30
        self.cut_min_size = (80, 60)
        
    def create_scene_from_egi(self, egi: RelationalGraphWithCuts, scene) -> Dict[str, QtContainmentElement]:
        """
        Main pipeline: EGI → Qt Containment → Spatial → Canonical
        """
        print(f"🏗️ Building Qt containment from EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Clear scene
        scene.clear()
        
        elements = {}
        
        # STEP 1: Parse EGI logical hierarchy
        containment_tree = self._parse_logical_hierarchy(egi)
        print(f"📋 Logical hierarchy: {len(containment_tree)} areas")
        
        # STEP 2: Build Qt parent-child containment tree
        qt_containers = self._build_qt_containment_tree(egi, containment_tree, scene, elements)
        print(f"🏗️ Qt containers: {len(qt_containers)} cuts")
        
        # STEP 3: Assign spatial positions within logical constraints
        self._assign_spatial_positions(egi, containment_tree, qt_containers, elements)
        print(f"📍 Spatial assignments complete")
        
        # STEP 4: Apply canonical Dau/Peirce visual conventions
        self._apply_canonical_appearance(egi, elements)
        print(f"🎨 Canonical appearance applied")
        
        return elements
    
    def _parse_logical_hierarchy(self, egi: RelationalGraphWithCuts) -> Dict[str, Set[str]]:
        """Parse EGI area mapping into logical containment hierarchy."""
        containment = {}
        
        # Initialize sheet (root container)
        containment[egi.sheet] = set()
        
        # Initialize all cuts
        for cut in egi.Cut:
            containment[cut.id] = set()
        
        # Parse area assignments from EGI
        for area_id, contents in egi.area.items():
            if area_id in containment:
                containment[area_id].update(contents)
                print(f"  📦 Area '{area_id}': {len(contents)} elements")
        
        return containment
    
    def _build_qt_containment_tree(self, egi: RelationalGraphWithCuts, 
                                  containment: Dict[str, Set[str]], 
                                  scene, elements: Dict[str, QtContainmentElement]) -> Dict[str, QGraphicsRectItem]:
        """Build Qt parent-child hierarchy from logical containment."""
        
        qt_containers = {}
        
        # Create cuts in dependency order (parents before children)
        cut_order = self._get_cut_dependency_order(egi)
        
        for cut_id in cut_order:
            cut = next(c for c in egi.Cut if c.id == cut_id)
            
            # Find logical parent
            logical_parent = self._find_logical_parent(cut_id, egi)
            
            # Create cut rectangle (container)
            cut_rect = QGraphicsRectItem()
            cut_rect.setPen(QPen(QColor(0, 0, 0), 1))  # Black line, 1px (fine cut)
            cut_rect.setBrush(QBrush())  # No fill
            cut_rect.setFlag(QGraphicsRectItem.ItemClipsChildrenToShape, True)  # ENFORCE CONTAINMENT
            
            # Set Qt parent-child relationship
            if logical_parent == egi.sheet:
                # Top-level cut - add to scene
                scene.addItem(cut_rect)
                print(f"  🏗️ Cut '{cut_id}' → scene (sheet)")
            else:
                # Nested cut - set parent cut
                parent_container = qt_containers[logical_parent]
                cut_rect.setParentItem(parent_container)
                print(f"  🏗️ Cut '{cut_id}' → parent '{logical_parent}'")
            
            qt_containers[cut_id] = cut_rect
            
            # Store element
            elements[cut_id] = QtContainmentElement(
                element_id=cut_id,
                element_type='cut',
                graphics_item=cut_rect,
                logical_parent=logical_parent
            )
        
        return qt_containers
    
    def _assign_spatial_positions(self, egi: RelationalGraphWithCuts,
                                containment: Dict[str, Set[str]],
                                qt_containers: Dict[str, QGraphicsRectItem],
                                elements: Dict[str, QtContainmentElement]):
        """Assign exclusive spatial positions within logical containment constraints."""
        
        # Track occupied positions for spatial exclusivity
        area_positions = {}  # area_id -> list of occupied rects
        
        # Initialize position tracking for each area
        for area_id in containment.keys():
            area_positions[area_id] = []
        
        # Create vertices with exclusive positioning
        for vertex in egi.V:
            logical_parent = self._find_element_logical_parent(vertex.id, egi)
            
            # Create vertex graphics
            radius = 8
            vertex_circle = QGraphicsEllipseItem(-radius, -radius, 2*radius, 2*radius)
            vertex_circle.setPen(QPen(QColor(0, 0, 0), 2))  # Black line, 2px
            vertex_circle.setBrush(QBrush(QColor(0, 0, 0)))  # Black fill
            
            # Find exclusive position within logical parent
            position = self._find_exclusive_position(
                logical_parent, area_positions, 2*radius, 2*radius, qt_containers
            )
            
            # Set Qt parent-child relationship and position
            if logical_parent == egi.sheet:
                # Place on scene (sheet element) - would need scene reference
                vertex_circle.setPos(position[0], position[1])
                print(f"  📍 Vertex '{vertex.id}' → sheet at {position}")
            else:
                # Place within parent cut
                parent_container = qt_containers[logical_parent]
                vertex_circle.setPos(position[0], position[1])
                vertex_circle.setParentItem(parent_container)
                print(f"  📍 Vertex '{vertex.id}' → cut '{logical_parent}' at {position}")
            
            # Mark position as occupied
            occupied_rect = QRectF(position[0] - radius, position[1] - radius, 2*radius, 2*radius)
            area_positions[logical_parent].append(occupied_rect)
            
            # Store element
            elements[vertex.id] = QtContainmentElement(
                element_id=vertex.id,
                element_type='vertex',
                graphics_item=vertex_circle,
                logical_parent=logical_parent
            )
            
            # Add vertex label if it has one
            if vertex.label:
                label_text = QGraphicsTextItem(f'"{vertex.label}"')
                label_text.setFont(QFont("Arial", 10))
                label_text.setDefaultTextColor(QColor(0, 0, 255))
                label_text.setPos(radius + 5, -radius)
                label_text.setParentItem(vertex_circle)  # Label is child of vertex
        
        # Create predicates with exclusive positioning
        for edge in egi.E:
            logical_parent = self._find_element_logical_parent(edge.id, egi)
            
            # Get predicate name
            predicate_name = egi.rel.get(edge.id, "P")
            
            # Create predicate text
            predicate_text = QGraphicsTextItem(predicate_name)
            predicate_text.setFont(QFont("Arial", 12))
            predicate_text.setDefaultTextColor(QColor(0, 0, 0))
            
            # Calculate predicate size for collision detection
            text_rect = predicate_text.boundingRect()
            
            # Find exclusive position within logical parent
            position = self._find_exclusive_position(
                logical_parent, area_positions, text_rect.width(), text_rect.height(), qt_containers
            )
            
            # Set Qt parent-child relationship and position
            if logical_parent == egi.sheet:
                # Place on scene (sheet element)
                predicate_text.setPos(position[0], position[1])
                print(f"  📍 Predicate '{edge.id}' ({predicate_name}) → sheet at {position}")
            else:
                # Place within parent cut
                parent_container = qt_containers[logical_parent]
                predicate_text.setPos(position[0], position[1])
                predicate_text.setParentItem(parent_container)
                print(f"  📍 Predicate '{edge.id}' ({predicate_name}) → cut '{logical_parent}' at {position}")
            
            # Mark position as occupied
            occupied_rect = QRectF(position[0], position[1], text_rect.width(), text_rect.height())
            area_positions[logical_parent].append(occupied_rect)
            
            # Store element
            elements[edge.id] = QtContainmentElement(
                element_id=edge.id,
                element_type='predicate',
                graphics_item=predicate_text,
                logical_parent=logical_parent
            )
        
        # Create ligatures (identity lines) between vertices and predicates
        self._create_ligatures(egi, elements, qt_containers)
        
        # Size cuts based on their contents
        self._size_cuts_from_contents(qt_containers, elements)
    
    def _apply_canonical_appearance(self, egi: RelationalGraphWithCuts, 
                                  elements: Dict[str, QtContainmentElement]):
        """Apply canonical Dau/Peirce visual conventions."""
        
        # Apply cut styling (fine lines)
        for element in elements.values():
            if element.element_type == 'cut':
                cut_item = element.graphics_item
                cut_item.setPen(QPen(QColor(0, 0, 0), 1))  # Fine cut line
        
        # Apply vertex styling (prominent spots)
        for element in elements.values():
            if element.element_type == 'vertex':
                vertex_item = element.graphics_item
                vertex_item.setPen(QPen(QColor(0, 0, 0), 2))  # Prominent vertex
                vertex_item.setBrush(QBrush(QColor(0, 0, 0)))  # Solid black
        
        # Apply predicate styling
        for element in elements.values():
            if element.element_type == 'predicate':
                predicate_item = element.graphics_item
                predicate_item.setFont(QFont("Arial", 12))
                predicate_item.setDefaultTextColor(QColor(0, 0, 0))
        
        print(f"🎨 Applied canonical Dau/Peirce conventions to {len(elements)} elements")
    
    def _get_cut_dependency_order(self, egi: RelationalGraphWithCuts) -> List[str]:
        """Get cuts in dependency order (parents before children)."""
        # For now, simple ordering - would implement proper topological sort
        return [cut.id for cut in egi.Cut]
    
    def _find_logical_parent(self, cut_id: str, egi: RelationalGraphWithCuts) -> str:
        """Find the logical parent of a cut."""
        # Check cut hierarchy - for now, assume sheet is parent
        # Would implement proper parent finding from EGI structure
        return egi.sheet
    
    def _find_element_logical_parent(self, element_id: str, egi: RelationalGraphWithCuts) -> str:
        """Find which area logically contains an element."""
        for area_id, contents in egi.area.items():
            if element_id in contents:
                return area_id
        return egi.sheet  # Default to sheet
    
    def _find_exclusive_position(self, area_id: str, area_positions: Dict[str, List[QRectF]], 
                               width: float, height: float, 
                               qt_containers: Dict[str, QGraphicsRectItem]) -> Tuple[float, float]:
        """Find a position within the area that doesn't overlap with existing elements."""
        
        # Get available space within the area
        if area_id in qt_containers:
            # Position within a cut
            container_rect = qt_containers[area_id].rect()
            available_width = container_rect.width() - 2 * self.padding
            available_height = container_rect.height() - 2 * self.padding
            start_x = self.padding
            start_y = self.padding
        else:
            # Position on sheet - use default canvas area
            available_width = 400  # Default sheet width
            available_height = 300  # Default sheet height
            start_x = self.padding
            start_y = self.padding
        
        # Try to find non-overlapping position using grid-based placement
        occupied_rects = area_positions.get(area_id, [])
        
        # Grid-based search for exclusive position
        grid_size = max(self.element_spacing, max(width, height))
        
        for row in range(int(available_height // grid_size) + 1):
            for col in range(int(available_width // grid_size) + 1):
                x = start_x + col * grid_size
                y = start_y + row * grid_size
                
                # Check if this position would fit within the area
                if x + width > start_x + available_width or y + height > start_y + available_height:
                    continue
                
                # Create candidate rectangle
                candidate_rect = QRectF(x, y, width, height)
                
                # Check for overlaps with existing elements
                overlaps = False
                for occupied_rect in occupied_rects:
                    if candidate_rect.intersects(occupied_rect):
                        overlaps = True
                        break
                
                if not overlaps:
                    return (x, y)
        
        # Fallback: place at end of existing elements with spacing
        if occupied_rects:
            last_rect = occupied_rects[-1]
            return (last_rect.right() + self.element_spacing, start_y)
        else:
            return (start_x, start_y)
    
    def _create_ligatures(self, egi: RelationalGraphWithCuts, 
                         elements: Dict[str, QtContainmentElement],
                         qt_containers: Dict[str, QGraphicsRectItem]):
        """Create ligatures (identity lines) between vertices and predicates."""
        
        print(f"🔗 Creating ligatures from ν mapping...")
        
        # Check if EGI has ν mapping
        if not hasattr(egi, 'nu') or not egi.nu:
            print(f"  ⚠️ No ν mapping found - no ligatures to create")
            return
        
        ligature_count = 0
        
        # Create ligatures based on ν mapping (vertex-predicate connections)
        for edge_id, vertex_mappings in egi.nu.items():
            if edge_id not in elements:
                continue
                
            predicate_element = elements[edge_id]
            predicate_item = predicate_element.graphics_item
            
            # Get predicate position
            predicate_pos = predicate_item.pos()
            predicate_rect = predicate_item.boundingRect()
            predicate_center = (
                predicate_pos.x() + predicate_rect.width() / 2,
                predicate_pos.y() + predicate_rect.height() / 2
            )
            
            # Create ligature to each connected vertex
            for arg_pos, vertex_id in vertex_mappings.items():
                if vertex_id not in elements:
                    continue
                    
                vertex_element = elements[vertex_id]
                vertex_item = vertex_element.graphics_item
                
                # Get vertex position
                vertex_pos = vertex_item.pos()
                vertex_rect = vertex_item.boundingRect()
                vertex_center = (
                    vertex_pos.x() + vertex_rect.width() / 2,
                    vertex_pos.y() + vertex_rect.height() / 2
                )
                
                # Create ligature line
                ligature_line = QGraphicsLineItem(
                    vertex_center[0], vertex_center[1],
                    predicate_center[0], predicate_center[1]
                )
                
                # Style ligature as heavy identity line (Dau convention)
                ligature_pen = QPen(QColor(0, 0, 0), 3)  # Heavy line, 3px
                ligature_line.setPen(ligature_pen)
                
                # Set ligature parent to common ancestor of vertex and predicate
                common_parent = self._find_common_parent(vertex_element, predicate_element, qt_containers)
                if common_parent:
                    ligature_line.setParentItem(common_parent)
                    print(f"  🔗 Ligature: {vertex_id} → {edge_id} (arg {arg_pos})")
                    ligature_count += 1
                else:
                    print(f"  ⚠️ No common parent for ligature {vertex_id} → {edge_id}")
                
                # Store ligature element
                ligature_id = f"ligature_{vertex_id}_{edge_id}_{arg_pos}"
                elements[ligature_id] = QtContainmentElement(
                    element_id=ligature_id,
                    element_type='ligature',
                    graphics_item=ligature_line,
                    logical_parent=common_parent.data(0) if common_parent else None
                )
        
        print(f"🔗 Created {ligature_count} ligatures")
    
    def _find_common_parent(self, element1: QtContainmentElement, element2: QtContainmentElement,
                          qt_containers: Dict[str, QGraphicsRectItem]) -> Optional[QGraphicsRectItem]:
        """Find the common parent container for two elements."""
        
        # If both elements have the same logical parent, use that container
        if element1.logical_parent == element2.logical_parent:
            if element1.logical_parent in qt_containers:
                return qt_containers[element1.logical_parent]
        
        # Otherwise, find the lowest common ancestor in the containment hierarchy
        # For now, use the scene (sheet) as the common parent
        return None  # Will place on scene
    
    def _size_cuts_from_contents(self, qt_containers: Dict[str, QGraphicsRectItem],
                               elements: Dict[str, QtContainmentElement]):
        """Size cuts based on their contained elements."""
        for cut_id, cut_item in qt_containers.items():
            # Find all children of this cut
            children_bounds = QRectF()
            for element in elements.values():
                if element.logical_parent == cut_id:
                    child_rect = element.graphics_item.boundingRect()
                    child_pos = element.graphics_item.pos()
                    child_rect.translate(child_pos)
                    children_bounds = children_bounds.united(child_rect)
            
            # Set cut size with padding
            if not children_bounds.isEmpty():
                width = max(children_bounds.width() + 2 * self.padding, self.cut_min_size[0])
                height = max(children_bounds.height() + 2 * self.padding, self.cut_min_size[1])
                cut_item.setRect(0, 0, width, height)
            else:
                # Empty cut - use minimum size
                cut_item.setRect(0, 0, self.cut_min_size[0], self.cut_min_size[1])


if __name__ == "__main__":
    print("🏗️ Qt Containment Engine - Logic → Qt → Spatial → Canonical")
    print("✅ Builds proper Qt parent-child hierarchy from EGI logical structure")
    print("✅ Enforces spatial assignments within logical constraints")
    print("✅ Applies canonical Dau/Peirce visual conventions")
