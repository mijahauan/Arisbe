"""
Visualization system for rule-governed graph building.
Integrates with existing rendering infrastructure to show transformation sequences.
"""

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from immutable_transformation_architecture import TransformationStep
from reusable_rendering_core import BoundaryAnchor, RenderingStyle
from rule_governed_composition import RuleGovernedComposer
from simple_graph_builder import GraphUtterance, SimpleGraphBuilder

from egi_core_dau import ElementID, RelationalGraphWithCuts


@dataclass
class VisualizationFrame:
    """Single frame in a graph building visualization."""

    frame_id: str
    step_number: int
    egi_id: str
    egi_state: RelationalGraphWithCuts
    transformation_step: Optional[TransformationStep]
    description: str
    svg_content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class GraphBuildingVisualizer:
    """Visualizer for rule-governed graph building sequences."""

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.builder = SimpleGraphBuilder()
        self.composer = RuleGovernedComposer()

        # Rendering components
        self.boundary_anchor = BoundaryAnchor()
        self.rendering_style = RenderingStyle()

        # Visualization state
        self.visualization_sessions: Dict[str, List[VisualizationFrame]] = {}
        self.current_session: Optional[str] = None

    def start_visualization_session(self, session_title: str) -> str:
        """Start a new visualization session."""
        session_id = str(uuid.uuid4())
        self.visualization_sessions[session_id] = []
        self.current_session = session_id

        # Create initial empty frame
        empty_egi_id = self.builder.create_empty_context()
        empty_egi = self.builder.pipeline.get_egi_state(empty_egi_id)

        initial_frame = VisualizationFrame(
            frame_id=str(uuid.uuid4()),
            step_number=0,
            egi_id=empty_egi_id,
            egi_state=empty_egi,
            transformation_step=None,
            description=f"Initial empty context for {session_title}",
            svg_content=self._render_egi_to_svg(empty_egi, "Empty Context"),
        )

        self.visualization_sessions[session_id].append(initial_frame)
        return session_id

    def visualize_utterance_building(self, utterance_id: str) -> str:
        """Visualize the building of a graph utterance."""
        utterance = self.builder.get_utterance_details(utterance_id)
        if not utterance:
            raise ValueError(f"Utterance {utterance_id} not found")

        session_id = self.start_visualization_session(f"Building: {utterance['title']}")

        # Get transformation sequence
        transformation_history = self.builder.pipeline.get_transformation_history(
            utterance_id
        )

        for i, step in enumerate(transformation_history):
            egi_state = self.builder.pipeline.get_egi_state(step.result_egi_id)
            if egi_state:
                frame = VisualizationFrame(
                    frame_id=str(uuid.uuid4()),
                    step_number=i + 1,
                    egi_id=step.result_egi_id,
                    egi_state=egi_state,
                    transformation_step=step,
                    description=f"Step {i+1}: {step.logical_justification}",
                    svg_content=self._render_egi_to_svg(egi_state, f"Step {i+1}"),
                )
                self.visualization_sessions[session_id].append(frame)

        return session_id

    def visualize_composition_sequence(
        self,
        composition_steps: List[Dict[str, Any]],
        title: str = "Composition Sequence",
    ) -> str:
        """Visualize a composition sequence step by step."""
        session_id = self.start_visualization_session(title)

        # Execute steps and capture each state
        current_egi_id = self.builder.create_empty_context()

        for i, step in enumerate(composition_steps):
            try:
                new_egi_id = self.builder.pipeline.apply_transformation(
                    source_egi_id=current_egi_id,
                    rule_type=step["rule_type"],
                    transformation_data=step["transformation_data"],
                    logical_justification=step.get("justification", f"Step {i+1}"),
                )

                egi_state = self.builder.pipeline.get_egi_state(new_egi_id)
                if egi_state:
                    frame = VisualizationFrame(
                        frame_id=str(uuid.uuid4()),
                        step_number=i + 1,
                        egi_id=new_egi_id,
                        egi_state=egi_state,
                        transformation_step=None,
                        description=step.get("justification", f"Step {i+1}"),
                        svg_content=self._render_egi_to_svg(egi_state, f"Step {i+1}"),
                    )
                    self.visualization_sessions[session_id].append(frame)

                current_egi_id = new_egi_id

            except Exception as e:
                print(f"Warning: Step {i+1} failed: {e}")
                continue

        return session_id

    def _render_egi_to_svg(self, egi: RelationalGraphWithCuts, title: str) -> str:
        """Render an EGI to SVG format."""
        # Create SVG root
        svg = ET.Element(
            "svg",
            {
                "width": str(self.width),
                "height": str(self.height),
                "xmlns": "http://www.w3.org/2000/svg",
                "viewBox": f"0 0 {self.width} {self.height}",
            },
        )

        # Add title
        title_elem = ET.SubElement(
            svg,
            "text",
            {
                "x": str(self.width // 2),
                "y": "30",
                "text-anchor": "middle",
                "font-family": "Arial, sans-serif",
                "font-size": "16",
                "font-weight": "bold",
            },
        )
        title_elem.text = title

        # Add background
        bg = ET.SubElement(
            svg,
            "rect",
            {
                "width": str(self.width),
                "height": str(self.height),
                "fill": "#f8f9fa",
                "stroke": "#dee2e6",
                "stroke-width": "1",
            },
        )

        # Calculate layout
        layout = self._calculate_layout(egi)

        # Render cuts first (background)
        for cut_id in egi.Cut:
            cut_elements = egi.area.get(cut_id.element_id, frozenset())
            if cut_elements:
                self._render_cut(svg, cut_id, cut_elements, layout)

        # Render edges
        for edge in egi.E:
            vertex_sequence = egi.nu.get(edge.element_id, ())
            if vertex_sequence:
                self._render_edge(svg, edge, vertex_sequence, layout)

        # Render vertices (foreground)
        for vertex in egi.V:
            self._render_vertex(svg, vertex, layout)

        # Add element count info
        info_y = self.height - 60
        info_elem = ET.SubElement(
            svg,
            "text",
            {
                "x": "20",
                "y": str(info_y),
                "font-family": "Arial, sans-serif",
                "font-size": "12",
                "fill": "#6c757d",
            },
        )
        info_elem.text = f"Elements: {len(egi.V)}V, {len(egi.E)}E, {len(egi.Cut)}C"

        return ET.tostring(svg, encoding="unicode")

    def _calculate_layout(
        self, egi: RelationalGraphWithCuts
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate positions for graph elements."""
        layout = {}

        # Simple grid layout for vertices
        vertices = list(egi.V)
        if vertices:
            cols = max(1, int(len(vertices) ** 0.5))
            rows = (len(vertices) + cols - 1) // cols

            start_x = self.width * 0.2
            start_y = self.height * 0.2
            width_span = self.width * 0.6
            height_span = self.height * 0.6

            for i, vertex in enumerate(vertices):
                row = i // cols
                col = i % cols
                x = (
                    start_x + (col * width_span / max(1, cols - 1))
                    if cols > 1
                    else self.width / 2
                )
                y = (
                    start_y + (row * height_span / max(1, rows - 1))
                    if rows > 1
                    else self.height / 2
                )
                layout[vertex.element_id] = (x, y)

        return layout

    def _render_vertex(
        self, svg: ET.Element, vertex, layout: Dict[str, Tuple[float, float]]
    ):
        """Render a vertex."""
        pos = layout.get(vertex.element_id, (self.width / 2, self.height / 2))

        # Vertex circle
        circle = ET.SubElement(
            svg,
            "circle",
            {
                "cx": str(pos[0]),
                "cy": str(pos[1]),
                "r": "20",
                "fill": "#007bff",
                "stroke": "#0056b3",
                "stroke-width": "2",
            },
        )

        # Vertex label
        label = ET.SubElement(
            svg,
            "text",
            {
                "x": str(pos[0]),
                "y": str(pos[1] + 5),
                "text-anchor": "middle",
                "font-family": "Arial, sans-serif",
                "font-size": "12",
                "fill": "white",
                "font-weight": "bold",
            },
        )
        label.text = vertex.element_id[:3]  # Show first 3 chars

    def _render_edge(
        self,
        svg: ET.Element,
        edge,
        vertex_sequence: Tuple,
        layout: Dict[str, Tuple[float, float]],
    ):
        """Render an edge connecting vertices."""
        if len(vertex_sequence) < 2:
            return

        # Get positions
        positions = []
        for vertex_id in vertex_sequence:
            pos = layout.get(vertex_id, (self.width / 2, self.height / 2))
            positions.append(pos)

        # Draw lines between consecutive vertices
        for i in range(len(positions) - 1):
            x1, y1 = positions[i]
            x2, y2 = positions[i + 1]

            line = ET.SubElement(
                svg,
                "line",
                {
                    "x1": str(x1),
                    "y1": str(y1),
                    "x2": str(x2),
                    "y2": str(y2),
                    "stroke": "#28a745",
                    "stroke-width": "3",
                    "marker-end": "url(#arrowhead)",
                },
            )

        # Add relation name at midpoint
        if len(positions) >= 2:
            mid_x = sum(pos[0] for pos in positions) / len(positions)
            mid_y = sum(pos[1] for pos in positions) / len(positions) - 10

            relation_name = getattr(edge, "relation_name", edge.element_id)
            label = ET.SubElement(
                svg,
                "text",
                {
                    "x": str(mid_x),
                    "y": str(mid_y),
                    "text-anchor": "middle",
                    "font-family": "Arial, sans-serif",
                    "font-size": "10",
                    "fill": "#28a745",
                    "font-weight": "bold",
                },
            )
            label.text = str(relation_name)

    def _render_cut(
        self,
        svg: ET.Element,
        cut,
        enclosed_elements: frozenset,
        layout: Dict[str, Tuple[float, float]],
    ):
        """Render a cut around enclosed elements."""
        if not enclosed_elements:
            return

        # Find bounding box of enclosed elements
        positions = []
        for element_id in enclosed_elements:
            pos = layout.get(element_id, (self.width / 2, self.height / 2))
            positions.append(pos)

        if not positions:
            return

        # Calculate bounding rectangle with padding
        min_x = min(pos[0] for pos in positions) - 40
        max_x = max(pos[0] for pos in positions) + 40
        min_y = min(pos[1] for pos in positions) - 40
        max_y = max(pos[1] for pos in positions) + 40

        # Draw cut as rounded rectangle
        cut_rect = ET.SubElement(
            svg,
            "rect",
            {
                "x": str(min_x),
                "y": str(min_y),
                "width": str(max_x - min_x),
                "height": str(max_y - min_y),
                "fill": "none",
                "stroke": "#dc3545",
                "stroke-width": "3",
                "stroke-dasharray": "10,5",
                "rx": "15",
                "ry": "15",
            },
        )

    def generate_animation_html(self, session_id: str) -> str:
        """Generate HTML with animation controls for a visualization session."""
        frames = self.visualization_sessions.get(session_id, [])
        if not frames:
            return "<html><body>No frames found</body></html>"

        # Prepare frame data for JavaScript
        frame_data = []
        for frame in frames:
            svg_content = frame.svg_content.replace("`", "\\`").replace("\n", "\\n")
            frame_data.append(
                f'{{"svg": `{svg_content}`, "description": "{frame.description}"}}'
            )

        frames_js = "[" + ",\n            ".join(frame_data) + "]"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Graph Building Animation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .controls {{ margin: 20px 0; text-align: center; }}
        .controls button {{ margin: 0 10px; padding: 10px 20px; font-size: 16px; }}
        .frame-info {{ text-align: center; margin: 10px 0; }}
        .svg-container {{ text-align: center; border: 1px solid #ccc; }}
        #frame-slider {{ width: 80%; margin: 10px; }}
    </style>
</head>
<body>
    <h1>Graph Building Animation</h1>
    
    <div class="controls">
        <button onclick="previousFrame()">⏮ Previous</button>
        <button onclick="playPause()" id="playBtn">▶ Play</button>
        <button onclick="nextFrame()">⏭ Next</button>
        <button onclick="resetAnimation()">🔄 Reset</button>
    </div>
    
    <div class="frame-info">
        <span id="frame-counter">Frame 1 of {len(frames)}</span>
        <br>
        <input type="range" id="frame-slider" min="0" max="{len(frames)-1}" value="0" 
               oninput="goToFrame(this.value)">
    </div>
    
    <div class="frame-info">
        <strong id="frame-description">{frames[0].description}</strong>
    </div>
    
    <div class="svg-container" id="svg-container">
        {frames[0].svg_content}
    </div>
    
    <script>
        let currentFrame = 0;
        let isPlaying = false;
        let animationInterval;
        
        const frames = {frames_js};
        
        function updateDisplay() {{
            document.getElementById('svg-container').innerHTML = frames[currentFrame].svg;
            document.getElementById('frame-description').textContent = frames[currentFrame].description;
            document.getElementById('frame-counter').textContent = `Frame ${{currentFrame + 1}} of {len(frames)}`;
            document.getElementById('frame-slider').value = currentFrame;
        }}
        
        function nextFrame() {{
            if (currentFrame < {len(frames) - 1}) {{
                currentFrame++;
                updateDisplay();
            }}
        }}
        
        function previousFrame() {{
            if (currentFrame > 0) {{
                currentFrame--;
                updateDisplay();
            }}
        }}
        
        function goToFrame(frameIndex) {{
            currentFrame = parseInt(frameIndex);
            updateDisplay();
        }}
        
        function playPause() {{
            if (isPlaying) {{
                clearInterval(animationInterval);
                document.getElementById('playBtn').textContent = '▶ Play';
                isPlaying = false;
            }} else {{
                animationInterval = setInterval(() => {{
                    if (currentFrame < {len(frames) - 1}) {{
                        nextFrame();
                    }} else {{
                        playPause(); // Stop at end
                    }}
                }}, 1500);
                document.getElementById('playBtn').textContent = '⏸ Pause';
                isPlaying = true;
            }}
        }}
        
        function resetAnimation() {{
            currentFrame = 0;
            updateDisplay();
            if (isPlaying) playPause();
        }}
    </script>
</body>
</html>"""

        return html

    def save_visualization_html(self, session_id: str, filename: str) -> str:
        """Save visualization as HTML file."""
        html_content = self.generate_animation_html(session_id)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        return filename

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a visualization session."""
        frames = self.visualization_sessions.get(session_id, [])

        if not frames:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "total_frames": len(frames),
            "duration_steps": len(frames) - 1,  # Exclude initial empty frame
            "first_frame": {
                "description": frames[0].description,
                "timestamp": frames[0].timestamp.isoformat(),
            },
            "last_frame": (
                {
                    "description": frames[-1].description,
                    "timestamp": frames[-1].timestamp.isoformat(),
                }
                if len(frames) > 1
                else None
            ),
            "final_state": {
                "vertices": len(frames[-1].egi_state.V),
                "edges": len(frames[-1].egi_state.E),
                "cuts": len(frames[-1].egi_state.Cut),
            },
        }


def demonstrate_visualization():
    """Demonstrate the graph building visualization system."""

    print("🎬 Graph Building Visualization System")
    print("=" * 40)

    visualizer = GraphBuildingVisualizer()

    # Create some test composition sequences
    test_sequences = [
        {
            "title": "Simple Conjunction A ∧ B",
            "steps": [
                {
                    "rule_type": "insertion",
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "A",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex A",
                },
                {
                    "rule_type": "insertion",
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "B",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex B for conjunction",
                },
            ],
        },
        {
            "title": "Negation ¬P",
            "steps": [
                {
                    "rule_type": "insertion",
                    "transformation_data": {
                        "element_type": "vertex",
                        "element_id": "P",
                        "target_area": "sheet",
                    },
                    "justification": "Insert vertex P",
                },
                {
                    "rule_type": "insertion",
                    "transformation_data": {
                        "element_type": "cut",
                        "element_id": "neg_P",
                        "target_area": "sheet",
                        "enclosed_elements": frozenset(["P"]),
                    },
                    "justification": "Apply negation with cut",
                },
            ],
        },
    ]

    created_sessions = []

    for sequence in test_sequences:
        print(f"\n🎯 Creating visualization: {sequence['title']}")

        try:
            # Note: We need to convert string rule types to enum values
            from immutable_transformation_architecture import TransformationRuleType

            converted_steps = []
            for step in sequence["steps"]:
                converted_step = step.copy()
                if step["rule_type"] == "insertion":
                    converted_step["rule_type"] = TransformationRuleType.INSERTION
                converted_steps.append(converted_step)

            session_id = visualizer.visualize_composition_sequence(
                converted_steps, sequence["title"]
            )

            summary = visualizer.get_session_summary(session_id)
            print(f"   Session ID: {session_id[:8]}...")
            print(f"   Frames: {summary['total_frames']}")
            print(f"   Final state: {summary['final_state']}")

            created_sessions.append(session_id)

        except Exception as e:
            print(f"   Error: {e}")

    print(f"\n📊 Visualization Summary:")
    print(f"   Sessions created: {len(created_sessions)}")
    print(f"   Total visualizations: {len(visualizer.visualization_sessions)}")

    # Save first session as HTML example
    if created_sessions:
        html_file = "graph_building_animation.html"
        visualizer.save_visualization_html(created_sessions[0], html_file)
        print(f"   Saved example HTML: {html_file}")

    return visualizer, created_sessions


if __name__ == "__main__":
    demonstrate_visualization()
