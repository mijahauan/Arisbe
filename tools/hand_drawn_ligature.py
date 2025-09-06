"""
Hand-drawn ligature path system for drawing_editor.py

This module provides functionality for:
1. Mouse tracking during ligature drawing
2. Path sampling and smoothing
3. Intelligent connection detection (vertex vs existing ligature)
4. Path simplification into straight segments, steps, and curves
"""

from typing import List, Optional, Tuple
from PySide6.QtCore import QPointF, QTimer
from PySide6.QtGui import QPainterPath, QPen, QColor
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
import math


class HandDrawnPath:
    """Represents a hand-drawn path with sampling and smoothing capabilities."""
    
    def __init__(self, sample_distance: float = 5.0):
        self.raw_points: List[QPointF] = []
        self.sample_distance = sample_distance
        self.smoothed_path: Optional[QPainterPath] = None
        
    def add_point(self, point: QPointF) -> None:
        """Add a point to the raw path, sampling at regular intervals."""
        if not self.raw_points:
            self.raw_points.append(point)
            return
            
        last_point = self.raw_points[-1]
        distance = self._distance(last_point, point)
        
        # Sample points at regular intervals along the line
        if distance >= self.sample_distance:
            num_samples = int(distance / self.sample_distance)
            for i in range(1, num_samples + 1):
                t = i / num_samples
                sampled_point = QPointF(
                    last_point.x() + t * (point.x() - last_point.x()),
                    last_point.y() + t * (point.y() - last_point.y())
                )
                self.raw_points.append(sampled_point)
    
    def smooth_path(self, smoothing_factor: float = 0.3) -> QPainterPath:
        """Convert raw points into a smoothed path using Bezier curves."""
        if len(self.raw_points) < 2:
            path = QPainterPath()
            if self.raw_points:
                path.moveTo(self.raw_points[0])
            return path
            
        # Apply simple smoothing filter
        smoothed_points = self._apply_smoothing_filter(self.raw_points, smoothing_factor)
        
        # Create path with curves
        path = QPainterPath()
        path.moveTo(smoothed_points[0])
        
        if len(smoothed_points) == 2:
            path.lineTo(smoothed_points[1])
        else:
            # Use quadratic Bezier curves for smooth connections
            for i in range(1, len(smoothed_points) - 1):
                prev_point = smoothed_points[i - 1]
                curr_point = smoothed_points[i]
                next_point = smoothed_points[i + 1]
                
                # Control point is the current point
                # End point is midway to next point for continuity
                if i == len(smoothed_points) - 2:
                    # Last segment - go to final point
                    path.quadTo(curr_point, next_point)
                else:
                    mid_point = QPointF(
                        (curr_point.x() + next_point.x()) / 2,
                        (curr_point.y() + next_point.y()) / 2
                    )
                    path.quadTo(curr_point, mid_point)
        
        self.smoothed_path = path
        return path
    
    def simplify_to_segments(self, angle_threshold: float = 15.0) -> List[Tuple[str, List[QPointF]]]:
        """
        Simplify the path into segments of different types:
        - 'straight': straight line segments
        - 'step': right-angle steps (horizontal then vertical or vice versa)
        - 'curve': curved segments
        
        Returns list of (segment_type, points) tuples
        """
        if len(self.raw_points) < 2:
            return []
            
        segments = []
        current_segment_points = [self.raw_points[0]]
        current_direction = None
        
        for i in range(1, len(self.raw_points)):
            point = self.raw_points[i]
            prev_point = self.raw_points[i - 1]
            
            # Calculate direction
            dx = point.x() - prev_point.x()
            dy = point.y() - prev_point.y()
            
            if abs(dx) < 1 and abs(dy) < 1:
                continue  # Skip tiny movements
                
            angle = math.degrees(math.atan2(dy, dx))
            
            # Determine if this is a significant direction change
            if current_direction is None:
                current_direction = angle
                current_segment_points.append(point)
            else:
                angle_diff = abs(angle - current_direction)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                    
                if angle_diff > angle_threshold:
                    # Direction change - finish current segment
                    segment_type = self._classify_segment(current_segment_points)
                    segments.append((segment_type, current_segment_points.copy()))
                    
                    # Start new segment
                    current_segment_points = [prev_point, point]
                    current_direction = angle
                else:
                    current_segment_points.append(point)
        
        # Add final segment
        if len(current_segment_points) > 1:
            segment_type = self._classify_segment(current_segment_points)
            segments.append((segment_type, current_segment_points))
            
        return segments
    
    def _distance(self, p1: QPointF, p2: QPointF) -> float:
        """Calculate distance between two points."""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        return math.sqrt(dx * dx + dy * dy)
    
    def _apply_smoothing_filter(self, points: List[QPointF], factor: float) -> List[QPointF]:
        """Apply simple smoothing filter to reduce noise."""
        if len(points) < 3:
            return points
            
        smoothed = [points[0]]  # Keep first point
        
        for i in range(1, len(points) - 1):
            prev_point = points[i - 1]
            curr_point = points[i]
            next_point = points[i + 1]
            
            # Weighted average
            smoothed_x = (1 - factor) * curr_point.x() + factor * (prev_point.x() + next_point.x()) / 2
            smoothed_y = (1 - factor) * curr_point.y() + factor * (prev_point.y() + next_point.y()) / 2
            
            smoothed.append(QPointF(smoothed_x, smoothed_y))
        
        smoothed.append(points[-1])  # Keep last point
        return smoothed
    
    def _classify_segment(self, points: List[QPointF]) -> str:
        """Classify a segment as straight, step, or curve."""
        if len(points) < 2:
            return 'straight'
            
        start = points[0]
        end = points[-1]
        
        # Check if it's mostly horizontal or vertical (step)
        dx = abs(end.x() - start.x())
        dy = abs(end.y() - start.y())
        
        if dx < 10 or dy < 10:  # Mostly one direction
            return 'step'
            
        # Check if points roughly follow a straight line
        total_deviation = 0
        for point in points[1:-1]:
            deviation = self._point_to_line_distance(point, start, end)
            total_deviation += deviation
            
        avg_deviation = total_deviation / max(1, len(points) - 2)
        
        if avg_deviation < 10:  # Threshold for "straight enough"
            return 'straight'
        else:
            return 'curve'
    
    def _point_to_line_distance(self, point: QPointF, line_start: QPointF, line_end: QPointF) -> float:
        """Calculate perpendicular distance from point to line."""
        # Vector from line_start to line_end
        line_dx = line_end.x() - line_start.x()
        line_dy = line_end.y() - line_start.y()
        
        if line_dx == 0 and line_dy == 0:
            return self._distance(point, line_start)
            
        # Project point onto line
        t = ((point.x() - line_start.x()) * line_dx + (point.y() - line_start.y()) * line_dy) / (line_dx * line_dx + line_dy * line_dy)
        t = max(0, min(1, t))  # Clamp to line segment
        
        projection = QPointF(
            line_start.x() + t * line_dx,
            line_start.y() + t * line_dy
        )
        
        return self._distance(point, projection)


class LigaturePathPreview(QGraphicsPathItem):
    """Graphics item for showing the ligature path preview while drawing."""
    
    def __init__(self):
        super().__init__()
        self.setPen(QPen(QColor(100, 150, 255, 180), 2))
        self.setZValue(1000)  # Draw on top
        
    def update_path(self, path: QPainterPath):
        """Update the preview path."""
        self.setPath(path)


class ConnectionDetector:
    """Detects what the user is trying to connect to (vertex or existing ligature)."""
    
    def __init__(self, editor):
        self.editor = editor
        self.connection_tolerance = 15.0
    
    def find_connection_target(self, end_point: QPointF) -> Tuple[str, Optional[str], Optional[QPointF]]:
        """
        Find what the end point should connect to.
        
        Returns:
            (connection_type, target_id, connection_point)
            
        connection_type: 'vertex', 'ligature', or 'none'
        target_id: vertex ID or ligature edge ID
        connection_point: exact point to connect to
        """
        # First check for vertex connections
        vertex_id = self.editor._find_vertex_at_position(end_point, self.connection_tolerance)
        if vertex_id:
            vertex = self.editor.model.vertices[vertex_id]
            return ('vertex', vertex_id, vertex.gfx.scenePos())
        
        # Check for ligature intersections
        ligature_connection = self._find_ligature_intersection(end_point)
        if ligature_connection:
            edge_id, connection_point = ligature_connection
            return ('ligature', edge_id, connection_point)
        
        return ('none', None, end_point)
    
    def _find_ligature_intersection(self, point: QPointF) -> Optional[Tuple[str, QPointF]]:
        """Find the nearest ligature line and return intersection point."""
        best_distance = float('inf')
        best_connection = None
        
        # Check all existing ligature visual items
        for ligature_item in self.editor._ligature_items:
            if not isinstance(ligature_item, QGraphicsPathItem):
                continue
                
            path = ligature_item.path()
            closest_point = self._closest_point_on_path(point, path)
            distance = self._distance(point, closest_point)
            
            if distance < self.connection_tolerance and distance < best_distance:
                # Find which edge this ligature represents
                edge_id = self._find_edge_id_for_ligature_item(ligature_item)
                if edge_id:
                    best_distance = distance
                    best_connection = (edge_id, closest_point)
        
        return best_connection
    
    def _closest_point_on_path(self, point: QPointF, path: QPainterPath) -> QPointF:
        """Find the closest point on a QPainterPath to the given point."""
        # Simplified implementation - sample points along the path
        best_point = path.pointAtPercent(0)
        best_distance = self._distance(point, best_point)
        
        # Sample at regular intervals
        for i in range(1, 101):  # 100 samples
            t = i / 100.0
            path_point = path.pointAtPercent(t)
            distance = self._distance(point, path_point)
            
            if distance < best_distance:
                best_distance = distance
                best_point = path_point
        
        return best_point
    
    def _find_edge_id_for_ligature_item(self, ligature_item: QGraphicsPathItem) -> Optional[str]:
        """Find which edge ID corresponds to a ligature graphics item."""
        # This would need to be implemented based on how ligature items are tracked
        # For now, return None - this would need integration with the existing ligature system
        return None
    
    def _distance(self, p1: QPointF, p2: QPointF) -> float:
        """Calculate distance between two points."""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        return math.sqrt(dx * dx + dy * dy)
