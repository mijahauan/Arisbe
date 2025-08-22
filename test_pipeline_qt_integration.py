#!/usr/bin/env python3
"""
Test integration of accurate 9-phase pipeline output with Qt constraint system.
Uses the same pipeline that generates accurate PNGs, but renders with Qt and applies constraints.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QSplitter
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

class PipelineQtWidget(QWidget):
    """Qt widget that uses actual 9-phase pipeline output for rendering."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        
        # Pipeline data
        self.egi = None
        self.context = {}
        self.layout_data = {}
        self.constraint_system = None
        
        # Visual settings
        self.vertex_radius = 8
        self.cut_line_width = 2
        self.predicate_padding = 20
        
        # Mouse interaction
        self.dragging = False
        self.drag_element = None
        self.drag_offset = QPoint(0, 0)
        
    def load_egif(self, egif_text):
        """Load EGIF using the same pipeline that generates accurate PNGs."""
        from egif_parser_dau import EGIFParser
        from layout_phase_implementations import (
            ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
            PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
            RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
            PhaseStatus
        )
        from spatial_awareness_system import SpatialAwarenessSystem
        from spatial_constraint_system import SpatialConstraintSystem
        
        self.current_egif = egif_text  # Store for display
        print(f"Loading EGIF: {egif_text}")
        
        # Step 1: Parse EGIF to EGI
        try:
            parser = EGIFParser(egif_text)
            self.egi = parser.parse()
        except Exception as e:
            print(f"Failed to parse EGIF: {e}")
            return False
        
        print(f"EGI: {len(self.egi.V)} vertices, {len(self.egi.E)} edges, {len(self.egi.Cut)} cuts")
        
        # Step 2: Execute same 9-phase pipeline as PNG generation
        spatial_system = SpatialAwarenessSystem()
        phases = [
            ElementSizingPhase(),
            ContainerSizingPhase(spatial_system),
            CollisionDetectionPhase(spatial_system),
            PredicatePositioningPhase(spatial_system),
            VertexPositioningPhase(spatial_system),
            HookAssignmentPhase(),
            RectilinearLigaturePhase(),
            BranchOptimizationPhase(),
            AreaCompactionPhase()
        ]
        
        self.context = {}
        for i, phase in enumerate(phases):
            result = phase.execute(self.egi, self.context)
            if result.status != PhaseStatus.COMPLETED:
                print(f"Phase {i+1} failed: {result.error_message}")
                return False
        
        print("9-phase pipeline completed")
        
        # Step 3: Extract layout data from pipeline context
        self._extract_layout_from_pipeline()
        
        # Step 4: Initialize constraint system
        self.constraint_system = SpatialConstraintSystem()
        self.constraint_system.set_egi_reference(self.egi)
        
        print(f"\n=== EGIF INPUT ===")
        print(f"EGIF: {egif_text}")
        
        print(f"\n=== EGI STRUCTURE ===")
        if self.egi:
            print(f"Vertices ({len(self.egi.V)}):")
            for v in self.egi.V:
                print(f"  {v.id}: label='{v.label}', is_generic={v.is_generic}")
            print(f"Edges ({len(self.egi.E)}):")
            for e in self.egi.E:
                print(f"  {e.id}")
            if hasattr(self.egi, 'rel'):
                print(f"Relations: {dict(self.egi.rel)}")
        
        print(f"\n=== EGDF/PIPELINE OUTPUT ===")
        print(f"Context keys: {list(self.context.keys())}")
        print(f"Relative bounds: {self.context.get('relative_bounds', {})}")
        print(f"Element tracking: {self.context.get('element_tracking', {})}")
        print(f"Vertex elements: {self.context.get('vertex_elements', {})}")
        print(f"Predicate elements: {self.context.get('predicate_elements', {})}")
        
        print(f"\n=== EGI AREA MAPPING (EXPECTED CUTS) ===")
        if self.egi and hasattr(self.egi, 'area'):
            print(f"EGI area mapping: {dict(self.egi.area)}")
            cut_count = len([k for k in self.egi.area.keys() if k != self.egi.sheet])
            print(f"Expected cuts from EGI: {cut_count}")
            print(f"EGI.Cut objects: {[c.id for c in self.egi.Cut]}")
            
            # DEBUG: Show which elements should be in which cuts
            print(f"\n=== ELEMENT CONTAINMENT ANALYSIS ===")
            for area_id, elements in self.egi.area.items():
                if area_id != self.egi.sheet:
                    print(f"Cut {area_id} should contain: {list(elements)}")
                    for element_id in elements:
                        containing_cut = self._find_containing_cut(element_id)
                        print(f"  Element {element_id} -> innermost cut: {containing_cut}")
        
        pipeline_cuts = len([k for k in self.context.get('relative_bounds', {}).keys() if k != 'sheet'])
        print(f"Pipeline cuts generated: {pipeline_cuts}")
        
        # DEBUG: Check if GraphvizClusterSizer is seeing all cuts
        print(f"\n=== GRAPHVIZ CLUSTER SIZER DEBUG ===")
        from src.graphviz_utilities import GraphvizClusterSizer
        sizer = GraphvizClusterSizer()
        element_dimensions = self.context.get('element_dimensions', {})
        print(f"Element dimensions passed to sizer: {element_dimensions}")
        
        # Generate the DOT that GraphvizClusterSizer would create
        if self.egi:
            try:
                dot_content = sizer._generate_cluster_sizing_dot(self.egi, element_dimensions)
                print(f"GraphvizClusterSizer DOT content:")
                print(dot_content)
                
                # Run Graphviz and see the xdot output
                xdot_output = sizer._run_graphviz(dot_content)
                print(f"\nGraphviz xdot output:")
                print(xdot_output[:1000] + "..." if len(xdot_output) > 1000 else xdot_output)
                
                # Test the parsing
                parsed_bounds = sizer._parse_cluster_bounds(xdot_output)
                print(f"\nParsed cluster bounds: {parsed_bounds}")
                print(f"Parsed bounds keys: {list(parsed_bounds.keys())}")
            except Exception as e:
                print(f"Failed to generate DOT: {e}")
        
        print(f"\n=== QT CANVAS COORDINATES ===")
        canvas_width, canvas_height = self.width() - 20, self.height() - 20
        print(f"Canvas size: {canvas_width} x {canvas_height}")
        for element_id, data in self.layout_data.items():
            rel_pos = "unknown"
            if element_id in self.context.get('vertex_elements', {}):
                vertex_element = self.context['vertex_elements'][element_id]
                rel_pos = vertex_element.position if hasattr(vertex_element, 'position') else 'unknown'
            elif element_id in self.context.get('predicate_elements', {}):
                predicate_element = self.context['predicate_elements'][element_id]
                rel_pos = predicate_element.position if hasattr(predicate_element, 'position') else 'unknown'
            print(f"{element_id}: {data['element_type']} - relative: {rel_pos} -> canvas: {data['position']} - label: '{data.get('label', 'no label')}'")
        
        print(f"\nLoaded {len(self.layout_data)} elements total")
        self.update()
        return True
    
    def _scale_coordinates_to_canvas(self):
        """Scale relative positions with level 0 canvas boundary and annulus around outermost cuts."""
        if not self.layout_data:
            return
        
        # Level 0 = canvas boundary with annulus around outermost cuts
        # Pipeline (0,0,1,1) represents the drawing space, but level 0 needs visual boundary
        canvas_width = self.width() - 20
        canvas_height = self.height() - 20
        
        # Create annulus (ring) around outermost cuts - level 0 boundary
        annulus_width = 30  # Space between outermost cuts and canvas edge
        
        # Available space for drawing is canvas minus annulus
        drawing_width = canvas_width - 2 * annulus_width
        drawing_height = canvas_height - 2 * annulus_width
        
        # Scale all elements from relative [0,1] space to drawing space (inside annulus)
        for data in self.layout_data.values():
            if data['element_type'] == 'cut':
                # Scale cut bounds from relative to absolute coordinates within drawing area
                rel_bounds = data['bounds']
                abs_bounds = (
                    annulus_width + rel_bounds[0] * drawing_width,   # left
                    annulus_width + rel_bounds[1] * drawing_height,  # top
                    annulus_width + rel_bounds[2] * drawing_width,   # right
                    annulus_width + rel_bounds[3] * drawing_height   # bottom
                )
                data['bounds'] = abs_bounds
                data['position'] = ((abs_bounds[0] + abs_bounds[2]) / 2,
                                  (abs_bounds[1] + abs_bounds[3]) / 2)
            else:
                # Scale element positions - handle sheet-level elements
                rel_pos = data['position']
                
                # Elements not enclosed by cuts belong to sheet level (level 0)
                # They should be positioned in the full canvas space, not restricted to drawing area
                if rel_pos == (0.5, 0.5):  # Default fallback position indicates sheet-level
                    # Position sheet-level elements in canvas margins/annulus area
                    abs_pos = (
                        annulus_width // 2,  # Left margin area
                        annulus_width + drawing_height // 2  # Middle of drawing area vertically
                    )
                else:
                    # Normal positioned elements go in drawing area
                    abs_pos = (
                        annulus_width + rel_pos[0] * drawing_width,
                        annulus_width + rel_pos[1] * drawing_height
                    )
                data['position'] = abs_pos
        
        # Store level 0 boundary for rendering
        self.level_0_boundary = (10, 10, canvas_width + 10, canvas_height + 10)
    
    def _extract_layout_from_pipeline_old(self):
        """Extract layout data from pipeline context for Qt rendering."""
        print(f"\n=== PIPELINE CONTEXT DEBUG ===")
        print(f"Context keys: {list(self.context.keys())}")
        
        # Use the 9-phase pipeline output instead of generating new Graphviz DOT
        self.layout_data = {}
        
        # Extract cuts from pipeline cluster_bounds
        cluster_bounds = self.context.get('cluster_bounds', {})
        relative_bounds = self.context.get('relative_bounds', {})
        
        print(f"\n=== PIPELINE BOUNDS EXTRACTION ===")
        print(f"Pipeline cluster bounds: {cluster_bounds}")
        print(f"Pipeline relative bounds: {relative_bounds}")
        print(f"Total relative bounds entries: {len(relative_bounds)}")
        
        # Extract cuts from pipeline output - leaf-to-root area accumulation
        # Pipeline builds from leaf cuts (innermost) up to level 0 (sheet = 100% space)
        # Parent cuts accumulate space requirements of their children
        cut_data = []
        for area_id, rel_bounds in relative_bounds.items():
            if area_id != 'sheet' and area_id.startswith(('0_', '0_0_')):
                # Extract the actual cut ID from the prefixed area_id
                cut_id = area_id.split('_', 2)[-1] if '_' in area_id else area_id
                
                # Pipeline relative bounds are (left, top, right, bottom) in [0,1] space
                left, top, right, bottom = rel_bounds
                
                print(f"DEBUG: Cut {cut_id} relative bounds: {rel_bounds}")
                
                # Determine nesting level based on EGI logical hierarchy
                nesting_level = self._get_cut_nesting_level(cut_id)
                bounds_area = (right - left) * (bottom - top)
                
                cut_data.append({
                    'cut_id': cut_id,
                    'area_id': area_id,
                    'bounds': (left, top, right, bottom),
                    'nesting_level': nesting_level,
                    'bounds_area': bounds_area
                })
        
        # Sort by nesting level (deeper cuts first) to establish containment hierarchy
        cut_data.sort(key=lambda x: x['nesting_level'], reverse=True)
        
        for cut_info in cut_data:
            cut_id = cut_info['cut_id']
            left, top, right, bottom = cut_info['bounds']
            
            self.layout_data[cut_id] = {
                'element_id': cut_id,
                'element_type': 'cut',
                'position': ((left + right) / 2, (top + bottom) / 2),
                'bounds': (left, top, right, bottom),
                'label': f"Cut {cut_id[-8:]}",
                'nesting_level': cut_info['nesting_level'],
                'bounds_area': cut_info['bounds_area']
            }
            
            print(f"Cut {cut_id}: level {cut_info['nesting_level']}, area {cut_info['bounds_area']:.3f}, bounds {cut_info['bounds']}")
        
        # Extract vertices from pipeline output
        vertex_elements = self.context.get('vertex_elements', {})
        for vertex_id, vertex_data in vertex_elements.items():
            rel_pos = vertex_data.get('relative_position', (0, 0))
            self.layout_data[vertex_id] = {
                'element_id': vertex_id,
                'element_type': 'vertex',
                'position': rel_pos,
                'label': vertex_data.get('label', f"*{vertex_id[-8:]}")
            }
        
        # Extract predicates from EGI.E (edges) since they represent predicates
        if self.egi and hasattr(self.egi, 'E'):
            for edge in self.egi.E:
                edge_id = edge.id
                # Get predicate label from EGI relations
                predicate_label = "Unknown"
                if hasattr(self.egi, 'rel') and edge_id in self.egi.rel:
                    predicate_label = self.egi.rel[edge_id]
                
                # Find predicate position - check element_tracking first
                predicate_pos = (0.5, 0.5)  # Default fallback
                element_tracking = self.context.get('element_tracking', {})
                for area_id, elements in element_tracking.items():
                    for element in elements:
                        if element.get('element_id') == edge_id and element.get('element_type') == 'predicate':
                            predicate_pos = element.get('relative_position', predicate_pos)
                            break
                
                self.layout_data[edge_id] = {
                    'element_id': edge_id,
                    'element_type': 'predicate',
                    'position': predicate_pos,
                    'label': predicate_label
                }
        
        # Also extract from predicate_elements if available
        predicate_elements = self.context.get('predicate_elements', {})
        for predicate_id, predicate_data in predicate_elements.items():
            rel_pos = predicate_data.get('relative_position', (0.5, 0.5))
            self.layout_data[predicate_id] = {
                'element_id': predicate_id,
                'element_type': 'predicate',
                'position': rel_pos,
                'label': predicate_data.get('label', predicate_id)
            }
        
        # Scale coordinates to Qt canvas
        self._scale_coordinates_to_canvas()
        
        print(f"\n=== QT CANVAS COORDINATES ===")
        canvas_width, canvas_height = self.width() - 20, self.height() - 20
        print(f"Canvas size: {canvas_width} x {canvas_height}")
        for element_id, data in self.layout_data.items():
            print(f"{element_id}: {data['element_type']} at {data['position']} - label: '{data.get('label', 'no label')}'")
        
        print(f"\nLoaded {len(self.layout_data)} elements from pipeline")
        self.update()
        return True
    
    def _get_cut_nesting_level(self, cut_id):
        """Determine nesting level of a cut based on EGI area hierarchy."""
        if not self.egi or not hasattr(self.egi, 'area'):
            return 0
        
        level = 0
        # Count how many cuts contain this cut
        for area_id, contents in self.egi.area.items():
            if cut_id in contents and area_id != self.egi.sheet:
                level += 1
        
        return level
    
    def _generate_graphviz_dot(self):
        """Generate DOT content from EGI like PNG generation does."""
        if not self.egi:
            return ""
        
        dot_lines = [
            "digraph EG {",
            "  rankdir=TB;",
            "  node [shape=box, style=rounded];",
            "  edge [style=solid];",
            ""
        ]
        
        # Add predicates as nodes
        for edge in self.egi.E:
            if hasattr(edge, 'relation') and edge.relation != '=':
                relation_name = edge.relation
                dot_lines.append(f'  "{edge.id}" [label="{relation_name}"];')
        
        # Add vertices as small circles
        for vertex in self.egi.V:
            if hasattr(vertex, 'name') and vertex.name:
                dot_lines.append(f'  "{vertex.id}" [label="{vertex.name}", shape=circle, width=0.3];')
            else:
                # Generic vertex
                dot_lines.append(f'  "{vertex.id}" [label="*{vertex.id[-8:]}", shape=circle, width=0.3];')
        
        # Add cuts as clusters (like PNG generation)
        for i, cut in enumerate(self.egi.Cut):
            dot_lines.append(f"  subgraph cluster_{i} {{")
            dot_lines.append(f'    label="";')
            dot_lines.append(f'    style=rounded;')
            
            # Add elements in this cut
            if cut.id in self.egi.area:
                for element_id in self.egi.area[cut.id]:
                    dot_lines.append(f'    "{element_id}";')
            
            dot_lines.append("  }")
        
        # Add identity lines as edges
        for edge in self.egi.E:
            if hasattr(edge, 'relation') and edge.relation == '=':
                vertices = self.egi.nu.get(edge.id, [])
                if len(vertices) >= 2:
                    dot_lines.append(f'  "{vertices[0]}" -- "{vertices[1]}" [style=bold];')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    def _parse_xdot_output(self, xdot_content):
        """Parse Graphviz xdot output to extract positioned elements."""
        import re
        
        layout_data = {}
        
        # Parse node positions
        node_pattern = r'_draw_.*?(\w+)\s+([0-9.]+)\s+([0-9.]+)'
        for match in re.finditer(node_pattern, xdot_content):
            node_id = match.group(1)
            x = float(match.group(2))
            y = float(match.group(3))
            
            # Determine element type
            if node_id in [v.id for v in self.egi.V]:
                element_type = 'vertex'
                label = f"*{node_id[-8:]}"
                for vertex in self.egi.V:
                    if vertex.id == node_id and hasattr(vertex, 'name') and vertex.name:
                        label = vertex.name
                        break
            elif node_id in [e.id for e in self.egi.E]:
                element_type = 'predicate'
                label = self.egi.rel.get(node_id, node_id)
            else:
                continue
            
            layout_data[node_id] = {
                'element_id': node_id,
                'element_type': element_type,
                'position': (x, y),
                'bounds': (x-20, y-10, x+20, y+10),
                'label': label
            }
        
        # Parse cluster bounds
        cluster_pattern = r'subgraph cluster_(\d+).*?bb="([0-9.]+),([0-9.]+),([0-9.]+),([0-9.]+)"'
        for match in re.finditer(cluster_pattern, xdot_content, re.DOTALL):
            cluster_idx = int(match.group(1))
            x1, y1, x2, y2 = map(float, match.groups()[1:])
            
            # Map cluster index to cut ID
            if cluster_idx < len(self.egi.Cut):
                cut = list(self.egi.Cut)[cluster_idx]
                cut_id = cut.id
                
                layout_data[cut_id] = {
                    'element_id': cut_id,
                    'element_type': 'cut',
                    'position': ((x1 + x2) / 2, (y1 + y2) / 2),
                    'bounds': (x1, y1, x2, y2),
                    'label': f"Cut {cut_id[-8:]}"
                }
        
        return layout_data
    
    def _extract_layout_from_pipeline(self):
        """Extract layout data directly from EGI structure and vertex labels."""
        print(f"\n=== DIRECT EGI EXTRACTION ===")
        self.layout_data = {}
        
        if not self.egi:
            print("No EGI available")
            return False
        
        # Extract vertices with proper labels
        print(f"Extracting {len(self.egi.V)} vertices:")
        for i, vertex in enumerate(self.egi.V):
            vertex_id = vertex.id
            # Use actual vertex label, not ID
            vertex_label = vertex.label if vertex.label else f"*{vertex_id[-8:]}"
            
            # Position vertices in a simple layout for now
            x_pos = 0.2 + (i * 0.3)
            y_pos = 0.3
            
            self.layout_data[vertex_id] = {
                'element_id': vertex_id,
                'element_type': 'vertex',
                'position': (x_pos, y_pos),
                'label': vertex_label
            }
            print(f"  {vertex_id}: '{vertex_label}' at ({x_pos}, {y_pos})")
        
        # Extract predicates from edges with proper labels
        print(f"Extracting {len(self.egi.E)} predicates:")
        for i, edge in enumerate(self.egi.E):
            edge_id = edge.id
            # Get predicate label from relations
            predicate_label = "Unknown"
            if hasattr(self.egi, 'rel') and edge_id in self.egi.rel:
                predicate_label = self.egi.rel[edge_id]
            
            # Position predicates in a simple layout
            x_pos = 0.2 + (i * 0.3)
            y_pos = 0.6
            
            self.layout_data[edge_id] = {
                'element_id': edge_id,
                'element_type': 'predicate',
                'position': (x_pos, y_pos),
                'label': predicate_label
            }
            print(f"  {edge_id}: '{predicate_label}' at ({x_pos}, {y_pos})")
        
        # Extract cuts with proper nesting - process outer cuts first
        print(f"Extracting {len(self.egi.Cut)} cuts:")
        
        # Calculate nesting levels for all cuts first
        cut_levels = {}
        for cut in self.egi.Cut:
            cut_levels[cut.id] = self._get_cut_nesting_level(cut.id)
        
        # Sort cuts by nesting level (outer cuts first - lower level numbers)
        sorted_cuts = sorted(self.egi.Cut, key=lambda c: cut_levels[c.id])
        
        for cut in sorted_cuts:
            cut_id = cut.id
            nesting_level = cut_levels[cut_id]
            
            # Create properly nested rectangles - outer cuts have less padding
            # Level 1 (outermost) gets 0.1 padding, level 2 gets 0.2 padding, etc.
            padding = 0.05 + (nesting_level * 0.1)
            left = padding
            top = padding
            right = 1.0 - padding
            bottom = 1.0 - padding
            
            self.layout_data[cut_id] = {
                'element_id': cut_id,
                'element_type': 'cut',
                'position': ((left + right) / 2, (top + bottom) / 2),
                'bounds': (left, top, right, bottom),
                'label': f"Cut {cut_id[-8:]}",
                'nesting_level': nesting_level
            }
            print(f"  {cut_id}: level {nesting_level}, bounds ({left:.2f}, {top:.2f}, {right:.2f}, {bottom:.2f})")
        
        # Scale coordinates to Qt canvas
        self._scale_coordinates_to_canvas()
        
        print(f"\n=== FINAL LAYOUT ===")
        for element_id, data in self.layout_data.items():
            print(f"{element_id}: {data['element_type']} at {data['position']} - '{data.get('label')}'")
        
        print(f"\nLoaded {len(self.layout_data)} elements from EGI")
        self.update()
        return True
    
    def _extract_layout_from_pipeline_graphviz(self):
        """Extract layout data using Graphviz like PNG generation."""
        import subprocess
        import tempfile
        import os
        
        print(f"\n=== USING GRAPHVIZ LAYOUT (like PNG) ===")
        
        # Generate DOT content like PNG generation
        dot_content = self._generate_graphviz_dot()
        print(f"Generated DOT content ({len(dot_content)} chars)")
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as dot_file:
            dot_file.write(dot_content)
            dot_path = dot_file.name
        
        xdot_path = dot_path.replace('.dot', '.xdot')
        
        try:
            # Generate xdot output like PNG generation
            subprocess.run(['dot', '-Txdot', dot_path, '-o', xdot_path], check=True)
            
            # Read xdot output
            with open(xdot_path, 'r') as f:
                xdot_content = f.read()
            
            print(f"Generated xdot output ({len(xdot_content)} chars)")
            
            # Parse xdot to extract positioned elements
            self.layout_data = self._parse_xdot_output(xdot_content)
            
            print(f"Extracted {len(self.layout_data)} positioned elements from Graphviz")
            for elem_id, data in self.layout_data.items():
                print(f"  {elem_id}: {data['element_type']} at {data['position']}")
            
        except subprocess.CalledProcessError as e:
            print(f"Graphviz failed: {e}")
            self.layout_data = {}
        finally:
            # Clean up temporary files
            try:
                os.unlink(dot_path)
                os.unlink(xdot_path)
            except:
                pass
        
        # Get canvas dimensions for final positioning
        canvas_width = self.width()
        canvas_height = self.height()
        
        # Scale Graphviz coordinates to canvas
        if self.layout_data:
            # Find bounds of all elements
            all_x = [pos[0] for data in self.layout_data.values() if 'position' in data for pos in [data['position']]]
            all_y = [pos[1] for data in self.layout_data.values() if 'position' in data for pos in [data['position']]]
            
            if all_x and all_y:
                min_x, max_x = min(all_x), max(all_x)
                min_y, max_y = min(all_y), max(all_y)
                
                # Scale to fit canvas with padding
                padding = 50
                scale_x = (canvas_width - 2*padding) / (max_x - min_x) if max_x > min_x else 1
                scale_y = (canvas_height - 2*padding) / (max_y - min_y) if max_y > min_y else 1
                scale = min(scale_x, scale_y)
                
                # Apply scaling and translation
                for data in self.layout_data.values():
                    if 'position' in data:
                        x, y = data['position']
                        new_x = padding + (x - min_x) * scale
                        new_y = padding + (y - min_y) * scale
                        data['position'] = (new_x, new_y)
                        
                        # Update bounds
                        if data['element_type'] == 'cut':
                            x1, y1, x2, y2 = data['bounds']
                            new_x1 = padding + (x1 - min_x) * scale
                            new_y1 = padding + (y1 - min_y) * scale
                            new_x2 = padding + (x2 - min_x) * scale
                            new_y2 = padding + (y2 - min_y) * scale
                            data['bounds'] = (new_x1, new_y1, new_x2, new_y2)
                        else:
                            # Update element bounds around new position
                            if data['element_type'] == 'vertex':
                                r = self.vertex_radius
                                data['bounds'] = (new_x-r, new_y-r, new_x+r, new_y+r)
                            else:  # predicate
                                p = self.predicate_padding
                                data['bounds'] = (new_x-p, new_y-10, new_x+p, new_y+10)
    
    def _get_cut_nesting_level(self, cut_id):
        """Determine nesting level of cut from EGI area mapping."""
        if not self.egi or not hasattr(self.egi, 'area'):
            return 1
        
        # Count how many other cuts contain this cut (indicating nesting depth)
        nesting_level = 1
        
        # Find elements in this cut
        cut_elements = self.egi.area.get(cut_id, frozenset())
        
        # Count how many other cuts also contain these elements (indicating nesting)
        for other_cut_id, other_elements in self.egi.area.items():
            if other_cut_id != cut_id and other_cut_id != self.egi.sheet:
                # If this cut's elements are subset of another cut, we're nested deeper
                if cut_elements.issubset(other_elements):
                    nesting_level += 1
        
        return nesting_level
    
    def _extract_cuts_from_egi_structure(self, canvas_width, canvas_height):
        """Extract cuts directly from EGI structure like PNG generation does."""
        if not self.egi or not hasattr(self.egi, 'area'):
            return
        
        print(f"\n=== EXTRACTING CUTS FROM EGI STRUCTURE (like PNG) ===")
        
        # Build containment hierarchy from EGI area mapping
        cut_hierarchy = {}
        for area_id, elements in self.egi.area.items():
            if area_id != self.egi.sheet:
                cut_hierarchy[area_id] = {
                    'elements': elements,
                    'contains_cuts': [],
                    'contained_by': None,
                    'level': 1
                }
        
        # Find which cuts contain other cuts
        for cut_id, cut_info in cut_hierarchy.items():
            for element in cut_info['elements']:
                if element in cut_hierarchy:
                    # This cut contains another cut
                    cut_info['contains_cuts'].append(element)
                    cut_hierarchy[element]['contained_by'] = cut_id
                    cut_hierarchy[element]['level'] = cut_info['level'] + 1
        
        print(f"Cut hierarchy: {cut_hierarchy}")
        
        # Create nested layout based on containment - process outer cuts first
        base_padding = 30  # Base padding in pixels
        
        # Sort cuts by level (outer cuts first)
        sorted_cuts = sorted(cut_hierarchy.items(), key=lambda x: x[1]['level'])
        
        for cut_id, cut_info in sorted_cuts:
            level = cut_info['level']
            container = cut_info['contained_by']
            
            if container is None:
                # Outermost cut - use most of canvas
                padding = base_padding
                abs_bounds = (
                    padding,
                    padding,
                    canvas_width - padding,
                    canvas_height - padding
                )
            else:
                # Inner cut - position inside container (container must already exist)
                if container in self.layout_data:
                    container_bounds = self.layout_data[container]['bounds']
                    inner_padding = 40  # Fixed inner padding
                    
                    abs_bounds = (
                        container_bounds[0] + inner_padding,
                        container_bounds[1] + inner_padding,
                        container_bounds[2] - inner_padding,
                        container_bounds[3] - inner_padding
                    )
                else:
                    # Fallback if container not found
                    abs_bounds = (50, 50, canvas_width - 50, canvas_height - 50)
            
            center_x = (abs_bounds[0] + abs_bounds[2]) / 2
            center_y = (abs_bounds[1] + abs_bounds[3]) / 2
            area = (abs_bounds[2] - abs_bounds[0]) * (abs_bounds[3] - abs_bounds[1])
            
            print(f"Cut {cut_id}: level={level}, container={container}, bounds={abs_bounds}")
            
            self.layout_data[cut_id] = {
                'element_id': cut_id,
                'element_type': 'cut',
                'position': (center_x, center_y),
                'bounds': abs_bounds,
                'area': area,
                'nesting_level': level,
                'contains_cuts': cut_info['contains_cuts'],
                'contained_by': container
            }
    
    def _find_containing_cut(self, element_id):
        """Find which cut contains the given element from EGI area mapping."""
        if not self.egi or not hasattr(self.egi, 'area'):
            return None
        
        # Find the innermost cut containing this element
        containing_cuts = []
        for area_id, elements in self.egi.area.items():
            if area_id != self.egi.sheet and element_id in elements:
                containing_cuts.append(area_id)
        
        # Return the innermost (highest level) cut
        if containing_cuts and hasattr(self, 'layout_data'):
            innermost_cut = None
            highest_level = 0
            for cut_id in containing_cuts:
                if cut_id in self.layout_data:
                    level = self.layout_data[cut_id].get('nesting_level', 1)
                    if level > highest_level:
                        highest_level = level
                        innermost_cut = cut_id
            return innermost_cut
        
        return containing_cuts[0] if containing_cuts else None
    
    def paintEvent(self, event):
        """Render the EG diagram using Qt painting."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Canvas extent is the level 0 boundary - no need to draw it
        
        if not self.layout_data:
            painter.drawText(50, 50, "No layout data available")
            return
        
        print(f"PAINT: Rendering {len(self.layout_data)} elements")
        for element_id, data in self.layout_data.items():
            print(f"  {element_id}: {data['element_type']} at {data['position']}")
        
        # Render cuts as simple rectangles with proper nesting
        cut_data = [(data, data.get('nesting_level', 0)) for data in self.layout_data.values() if data['element_type'] == 'cut']
        cut_data.sort(key=lambda x: x[1])  # Outermost cuts first
        
        for data, nesting_level in cut_data:
            bounds = data.get('bounds')
            if bounds:
                left, top, right, bottom = bounds
                
                # Draw cut as simple black rectangle outline
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                painter.setBrush(QBrush(QColor(255, 255, 255, 0)))  # Transparent fill
                painter.drawRect(left, top, right - left, bottom - top)
                
                # Draw cut label
                painter.setPen(QPen(QColor(100, 100, 100)))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(left + 5, top + 15, data.get('label', 'Cut'))
        
        # Render predicates - account for actual text size
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        for data in self.layout_data.values():
            if data['element_type'] == 'predicate':
                pos = data['position']
                label = data.get('label', data['element_id'])
                
                # Calculate actual text dimensions
                font_metrics = painter.fontMetrics()
                text_width = font_metrics.horizontalAdvance(str(label)) + 8  # padding
                text_height = font_metrics.height() + 4  # padding
                
                # Yellow background for predicates
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.setBrush(QBrush(QColor(255, 255, 0)))
                painter.drawRect(pos[0] - text_width//2, pos[1] - text_height//2,
                               text_width, text_height)
                
                # Black text
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(pos[0] - text_width//2 + 4, pos[1] + font_metrics.ascent()//2, str(label))
        
        # Render vertices - account for actual vertex names and sizes
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        for data in self.layout_data.values():
            if data['element_type'] == 'vertex':
                pos = data['position']
                radius = self.vertex_radius
                
                # Blue circle for vertices
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                painter.setBrush(QBrush(QColor(100, 150, 255)))
                painter.drawEllipse(pos[0] - radius, pos[1] - radius,
                                  radius * 2, radius * 2)
                
                # Draw vertex label with proper sizing
                label = data.get('label', f"*{data['element_id'][-8:]}")
                painter.setPen(QPen(QColor(0, 0, 0)))
                
                # Calculate actual text dimensions for vertex names
                font_metrics = painter.fontMetrics()
                text_width = font_metrics.horizontalAdvance(str(label))
                text_height = font_metrics.height()
                
                # Position text below vertex with proper spacing for ligatures
                text_y = pos[1] + radius + text_height + 5  # 5px padding for ligatures
                painter.drawText(pos[0] - text_width//2, text_y, str(label))
        
        # Render ligatures (edges) - account for element sizes and add padding
        if self.egi and hasattr(self.egi, 'E'):
            painter.setPen(QPen(QColor(50, 50, 50), 2))  # Thinner lines for better visibility
            
            # Handle both dict and frozenset cases for EGI.E
            if isinstance(self.egi.E, dict):
                edges_items = self.egi.E.items()
            else:
                edges_items = [(getattr(edge, 'id', str(edge)), edge) for edge in self.egi.E]
            
            for edge_id, edge in edges_items:
                edge_id_str = str(edge_id)
                if edge_id_str in self.layout_data:
                    edge_data = self.layout_data[edge_id_str]
                    edge_pos = edge_data['position']
                    
                    # Draw ligatures using ν mapping from EGI with proper spacing
                    if self.egi and hasattr(self.egi, 'nu') and edge_id_str in self.egi.nu:
                        vertex_sequence = self.egi.nu[edge_id_str]
                        for vertex_id in vertex_sequence:
                            if vertex_id in self.layout_data:
                                vertex_pos = self.layout_data[vertex_id]['position']
                                
                                # Calculate connection points accounting for element sizes
                                # Connect from edge of predicate box to edge of vertex circle
                                dx = vertex_pos[0] - edge_pos[0]
                                dy = vertex_pos[1] - edge_pos[1]
                                distance = (dx*dx + dy*dy) ** 0.5
                                
                                if distance > 0:
                                    # Normalize direction
                                    dx_norm = dx / distance
                                    dy_norm = dy / distance
                                    
                                    # Offset from predicate edge (accounting for text box size)
                                    predicate_offset = 15  # Approximate half-width of predicate box
                                    start_x = edge_pos[0] + dx_norm * predicate_offset
                                    start_y = edge_pos[1] + dy_norm * predicate_offset
                                    
                                    # Offset from vertex edge (accounting for circle radius)
                                    vertex_offset = self.vertex_radius + 2  # Small padding
                                    end_x = vertex_pos[0] - dx_norm * vertex_offset
                                    end_y = vertex_pos[1] - dy_norm * vertex_offset
                                    
                                    painter.drawLine(start_x, start_y, end_x, end_y)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging elements."""
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            
            # Find element under mouse
            for element_id, data in self.layout_data.items():
                element_pos = data['position']
                if (abs(pos.x() - element_pos[0]) < 20 and 
                    abs(pos.y() - element_pos[1]) < 20):
                    self.dragging = True
                    self.drag_element = element_id
                    self.drag_offset = QPoint(pos.x() - element_pos[0], pos.y() - element_pos[1])
                    break
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging elements."""
        if self.dragging and self.drag_element:
            pos = event.position().toPoint()
            new_x = pos.x() - self.drag_offset.x()
            new_y = pos.y() - self.drag_offset.y()
            
            # Update element position
            self.layout_data[self.drag_element]['position'] = (new_x, new_y)
            
            # Update bounds for vertices
            if self.layout_data[self.drag_element]['element_type'] == 'vertex':
                self.layout_data[self.drag_element]['bounds'] = (
                    new_x - self.vertex_radius, new_y - self.vertex_radius,
                    new_x + self.vertex_radius, new_y + self.vertex_radius
                )
            
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - apply constraints."""
        if self.dragging and self.constraint_system:
            # Apply constraint validation and fixes
            violations = self.constraint_system.validate_spatial_constraints(self.layout_data)
            if violations:
                print(f"Constraint violations detected: {len(violations)}")
                for violation in violations:
                    print(f"  - {violation}")
                
                # Apply fixes
                fixed_layout = self.constraint_system.apply_constraint_fixes(self.layout_data)
                if fixed_layout:
                    self.layout_data = fixed_layout
                    print("Applied constraint fixes")
                    self.update()
        
        self.dragging = False
        self.drag_element = None


class PipelineQtMainWindow(QWidget):
    """Main window for pipeline Qt integration test."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("9-Phase Pipeline + Qt Constraint Integration")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create layout
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Create drawing widget
        self.drawing_widget = PipelineQtWidget()
        splitter.addWidget(self.drawing_widget)
        
        # Create control panel
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        splitter.setSizes([700, 300])
        
        # Load default example
        self._load_default_example()
    
    def _create_control_panel(self):
        """Create control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # EGIF input
        layout.addWidget(QLabel("EGIF Input:"))
        self.egif_input = QTextEdit()
        self.egif_input.setMaximumHeight(100)
        self.egif_input.setPlainText('*x ~[ ~[ (P x) ] ]')
        layout.addWidget(self.egif_input)
        
        # Load button
        load_button = QPushButton("Load EGIF")
        load_button.clicked.connect(self._load_egif)
        layout.addWidget(load_button)
        
        # Status display
        layout.addWidget(QLabel("Status:"))
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        layout.addWidget(self.status_display)
        
        # Example buttons
        layout.addWidget(QLabel("Examples:"))
        examples = [
            ("Simple Predicate", '*x (Human x)'),
            ("Binary Relation", '*x *y (Loves x y)'),
            ("Socrates Example", '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'),
            ("Double Cut", '*x ~[ ~[ (P x) ] ]'),
        ]
        
        for name, egif in examples:
            button = QPushButton(name)
            button.clicked.connect(lambda checked, e=egif: self._load_example(e))
            layout.addWidget(button)
        
        layout.addStretch()
        return panel
    
    def _load_egif(self):
        """Load EGIF from input."""
        egif_text = self.egif_input.toPlainText().strip()
        if egif_text:
            success = self.drawing_widget.load_egif(egif_text)
            if success:
                self.status_display.setPlainText(f"✅ Loaded: {egif_text}")
            else:
                self.status_display.setPlainText(f"❌ Failed to load: {egif_text}")
    
    def _load_example(self, egif_text):
        """Load example EGIF."""
        self.egif_input.setPlainText(egif_text)
        self._load_egif()
    
    def _load_default_example(self):
        """Load default example."""
        self._load_egif()


def main():
    """Run the pipeline Qt integration test."""
    app = QApplication(sys.argv)
    
    window = PipelineQtMainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    result = main()
    print(f"\n✅ Pipeline Qt integration test completed (exit code: {result})")
