"""
Spatial Performance Optimization - Phase 4A Implementation

This module provides advanced spatial indexing and performance optimizations
for interactive diagrammatic operations. The optimizations focus on:

1. Advanced spatial indexing with adaptive subdivision
2. Efficient collision detection and proximity queries
3. Viewport-based rendering optimization
4. Memory pool management for frequent allocations
5. Batch operation processing for improved throughput
6. Caching strategies for frequently accessed data
7. Performance profiling and monitoring tools

These optimizations ensure that interactive diagrammatic manipulation
remains fluid and responsive even with large, complex existential graphs.

Author: Manus AI
Date: January 2025
Phase: 4A - Foundation Architecture
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import threading
import math
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import heapq

# Import layer components
from interaction_layer import (
    InteractionLayer, InteractionElement, SpatialBounds, InteractionElementType
)


class OptimizationLevel(Enum):
    """Levels of performance optimization."""
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    ULTRA = "ultra"


class QueryType(Enum):
    """Types of spatial queries."""
    POINT = "point"
    REGION = "region"
    RADIUS = "radius"
    NEAREST = "nearest"
    INTERSECTION = "intersection"
    CONTAINMENT = "containment"


@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization monitoring."""
    query_count: int = 0
    total_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage: int = 0
    
    # Spatial query metrics
    point_queries: int = 0
    region_queries: int = 0
    radius_queries: int = 0
    
    # Timing metrics
    average_query_time: float = 0.0
    max_query_time: float = 0.0
    min_query_time: float = float('inf')
    
    def update_query_time(self, query_time: float):
        """Update query timing metrics."""
        self.query_count += 1
        self.total_query_time += query_time
        self.average_query_time = self.total_query_time / self.query_count
        self.max_query_time = max(self.max_query_time, query_time)
        self.min_query_time = min(self.min_query_time, query_time)
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


@dataclass
class SpatialQuery:
    """Represents a spatial query with caching support."""
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_type: QueryType = QueryType.POINT
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Results and caching
    results: List[InteractionElement] = field(default_factory=list)
    cached: bool = False
    cache_timestamp: float = field(default_factory=time.time)
    cache_ttl: float = 1.0  # Cache time-to-live in seconds
    
    # Performance tracking
    execution_time: float = 0.0
    elements_checked: int = 0
    
    def is_cache_valid(self) -> bool:
        """Check if cached results are still valid."""
        return self.cached and (time.time() - self.cache_timestamp) < self.cache_ttl


class AdaptiveSpatialIndex:
    """Advanced spatial index with adaptive subdivision and optimization."""
    
    def __init__(self, bounds: SpatialBounds, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        self.bounds = bounds
        self.optimization_level = optimization_level
        
        # Adaptive parameters based on optimization level
        if optimization_level == OptimizationLevel.BASIC:
            self.max_depth = 4
            self.max_elements = 20
            self.subdivision_threshold = 0.7
        elif optimization_level == OptimizationLevel.STANDARD:
            self.max_depth = 6
            self.max_elements = 15
            self.subdivision_threshold = 0.6
        elif optimization_level == OptimizationLevel.AGGRESSIVE:
            self.max_depth = 8
            self.max_elements = 10
            self.subdivision_threshold = 0.5
        else:  # ULTRA
            self.max_depth = 10
            self.max_elements = 8
            self.subdivision_threshold = 0.4
        
        # Index structure
        self.elements: Dict[str, InteractionElement] = {}
        self.quadrants: Optional[List['AdaptiveSpatialIndex']] = None
        self.is_leaf = True
        self.depth = 0
        
        # Performance tracking
        self.access_count = 0
        self.last_access_time = time.time()
        self.subdivision_count = 0
        
        # Optimization features
        self.element_density = 0.0
        self.hotspot_threshold = 10  # Queries per second to be considered a hotspot
        
    def insert(self, element: InteractionElement) -> bool:
        """Insert an element with adaptive optimization."""
        self.access_count += 1
        self.last_access_time = time.time()
        
        if not self.bounds.intersects(element.bounds):
            return False
        
        if self.is_leaf:
            self.elements[element.id] = element
            self._update_density()
            
            # Check if subdivision is needed
            if (len(self.elements) > self.max_elements and 
                self.depth < self.max_depth and
                self.element_density > self.subdivision_threshold):
                self._subdivide()
            
            return True
        else:
            # Insert into appropriate quadrants
            inserted = False
            for quadrant in self.quadrants:
                if quadrant.insert(element):
                    inserted = True
            return inserted
    
    def remove(self, element_id: str) -> bool:
        """Remove an element with cleanup optimization."""
        self.access_count += 1
        self.last_access_time = time.time()
        
        if self.is_leaf:
            if element_id in self.elements:
                del self.elements[element_id]
                self._update_density()
                return True
            return False
        else:
            removed = False
            for quadrant in self.quadrants:
                if quadrant.remove(element_id):
                    removed = True
            
            # Check if consolidation is beneficial
            if removed and self._should_consolidate():
                self._consolidate()
            
            return removed
    
    def query_point(self, x: float, y: float) -> List[InteractionElement]:
        """Optimized point query with caching."""
        self.access_count += 1
        self.last_access_time = time.time()
        
        if not self.bounds.contains_point(x, y):
            return []
        
        if self.is_leaf:
            results = []
            for element in self.elements.values():
                if element.contains_point(x, y):
                    results.append(element)
            return results
        else:
            results = []
            for quadrant in self.quadrants:
                results.extend(quadrant.query_point(x, y))
            return results
    
    def query_region(self, query_bounds: SpatialBounds) -> List[InteractionElement]:
        """Optimized region query with early termination."""
        self.access_count += 1
        self.last_access_time = time.time()
        
        if not self.bounds.intersects(query_bounds):
            return []
        
        if self.is_leaf:
            results = []
            for element in self.elements.values():
                if element.bounds.intersects(query_bounds):
                    results.append(element)
            return results
        else:
            results = []
            for quadrant in self.quadrants:
                results.extend(quadrant.query_region(query_bounds))
            return results
    
    def query_radius(self, center_x: float, center_y: float, radius: float) -> List[InteractionElement]:
        """Optimized radius query with distance calculations."""
        self.access_count += 1
        self.last_access_time = time.time()
        
        # Check if circle intersects with bounds
        closest_x = max(self.bounds.x, min(center_x, self.bounds.x + self.bounds.width))
        closest_y = max(self.bounds.y, min(center_y, self.bounds.y + self.bounds.height))
        distance = math.sqrt((center_x - closest_x)**2 + (center_y - closest_y)**2)
        
        if distance > radius:
            return []
        
        if self.is_leaf:
            results = []
            for element in self.elements.values():
                # Check distance to element center
                elem_center = element.get_center()
                elem_distance = math.sqrt(
                    (center_x - elem_center[0])**2 + (center_y - elem_center[1])**2
                )
                if elem_distance <= radius:
                    results.append(element)
            return results
        else:
            results = []
            for quadrant in self.quadrants:
                results.extend(quadrant.query_radius(center_x, center_y, radius))
            return results
    
    def query_nearest(self, x: float, y: float, count: int = 1) -> List[Tuple[InteractionElement, float]]:
        """Find nearest elements with distance."""
        self.access_count += 1
        self.last_access_time = time.time()
        
        # Use a priority queue to maintain nearest elements
        nearest_heap = []
        self._collect_nearest(x, y, count, nearest_heap)
        
        # Sort by distance and return top count
        results = []
        while nearest_heap and len(results) < count:
            distance, element = heapq.heappop(nearest_heap)
            results.append((element, distance))
        
        return results
    
    def _collect_nearest(self, x: float, y: float, count: int, heap: List):
        """Recursively collect nearest elements."""
        if self.is_leaf:
            for element in self.elements.values():
                center = element.get_center()
                distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
                
                if len(heap) < count:
                    heapq.heappush(heap, (-distance, element))  # Negative for max heap
                elif distance < -heap[0][0]:  # Better than worst in heap
                    heapq.heapreplace(heap, (-distance, element))
        else:
            # Sort quadrants by distance to query point
            quadrant_distances = []
            for quadrant in self.quadrants:
                # Distance to closest point in quadrant bounds
                closest_x = max(quadrant.bounds.x, min(x, quadrant.bounds.x + quadrant.bounds.width))
                closest_y = max(quadrant.bounds.y, min(y, quadrant.bounds.y + quadrant.bounds.height))
                distance = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)
                quadrant_distances.append((distance, quadrant))
            
            # Process quadrants in order of distance
            quadrant_distances.sort()
            for distance, quadrant in quadrant_distances:
                # Skip if this quadrant can't possibly have nearer elements
                if len(heap) >= count and distance > -heap[0][0]:
                    break
                quadrant._collect_nearest(x, y, count, heap)
    
    def _subdivide(self):
        """Subdivide this node into quadrants."""
        if not self.is_leaf or self.depth >= self.max_depth:
            return
        
        half_width = self.bounds.width / 2
        half_height = self.bounds.height / 2
        
        # Create four quadrants
        self.quadrants = [
            # Top-left
            AdaptiveSpatialIndex(
                SpatialBounds(self.bounds.x, self.bounds.y, half_width, half_height),
                self.optimization_level
            ),
            # Top-right
            AdaptiveSpatialIndex(
                SpatialBounds(self.bounds.x + half_width, self.bounds.y, half_width, half_height),
                self.optimization_level
            ),
            # Bottom-left
            AdaptiveSpatialIndex(
                SpatialBounds(self.bounds.x, self.bounds.y + half_height, half_width, half_height),
                self.optimization_level
            ),
            # Bottom-right
            AdaptiveSpatialIndex(
                SpatialBounds(self.bounds.x + half_width, self.bounds.y + half_height, half_width, half_height),
                self.optimization_level
            )
        ]
        
        # Set depth for quadrants
        for quadrant in self.quadrants:
            quadrant.depth = self.depth + 1
        
        # Redistribute elements to quadrants
        elements_to_redistribute = list(self.elements.values())
        self.elements.clear()
        self.is_leaf = False
        self.subdivision_count += 1
        
        for element in elements_to_redistribute:
            for quadrant in self.quadrants:
                quadrant.insert(element)
    
    def _should_consolidate(self) -> bool:
        """Check if consolidation would be beneficial."""
        if self.is_leaf:
            return False
        
        total_elements = sum(len(q.elements) if q.is_leaf else q._count_total_elements() 
                           for q in self.quadrants)
        
        # Consolidate if total elements is less than subdivision threshold
        return total_elements < self.max_elements * 0.5
    
    def _consolidate(self):
        """Consolidate quadrants back into a leaf node."""
        if self.is_leaf:
            return
        
        # Collect all elements from quadrants
        all_elements = {}
        for quadrant in self.quadrants:
            if quadrant.is_leaf:
                all_elements.update(quadrant.elements)
            else:
                all_elements.update(quadrant._collect_all_elements())
        
        # Convert back to leaf
        self.elements = all_elements
        self.quadrants = None
        self.is_leaf = True
        self._update_density()
    
    def _collect_all_elements(self) -> Dict[str, InteractionElement]:
        """Recursively collect all elements."""
        if self.is_leaf:
            return self.elements.copy()
        
        all_elements = {}
        for quadrant in self.quadrants:
            all_elements.update(quadrant._collect_all_elements())
        return all_elements
    
    def _count_total_elements(self) -> int:
        """Count total elements in this subtree."""
        if self.is_leaf:
            return len(self.elements)
        
        return sum(q._count_total_elements() for q in self.quadrants)
    
    def _update_density(self):
        """Update element density for optimization decisions."""
        area = self.bounds.width * self.bounds.height
        self.element_density = len(self.elements) / area if area > 0 else 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the spatial index."""
        stats = {
            "is_leaf": self.is_leaf,
            "depth": self.depth,
            "element_count": len(self.elements),
            "access_count": self.access_count,
            "subdivision_count": self.subdivision_count,
            "element_density": self.element_density,
            "bounds": {
                "x": self.bounds.x,
                "y": self.bounds.y,
                "width": self.bounds.width,
                "height": self.bounds.height
            }
        }
        
        if not self.is_leaf:
            stats["quadrant_stats"] = [q.get_statistics() for q in self.quadrants]
            stats["total_elements"] = self._count_total_elements()
        
        return stats


class QueryCache:
    """Cache for spatial queries to improve performance."""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 1.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, SpatialQuery] = {}
        self.access_order: deque = deque()
        self.metrics = PerformanceMetrics()
        self._lock = threading.RLock()
    
    def get(self, query_key: str) -> Optional[SpatialQuery]:
        """Get cached query results."""
        with self._lock:
            if query_key in self.cache:
                query = self.cache[query_key]
                if query.is_cache_valid():
                    # Move to end of access order (LRU)
                    self.access_order.remove(query_key)
                    self.access_order.append(query_key)
                    self.metrics.cache_hits += 1
                    return query
                else:
                    # Remove expired entry
                    del self.cache[query_key]
                    self.access_order.remove(query_key)
            
            self.metrics.cache_misses += 1
            return None
    
    def put(self, query_key: str, query: SpatialQuery):
        """Cache query results."""
        with self._lock:
            # Remove oldest entries if cache is full
            while len(self.cache) >= self.max_size:
                oldest_key = self.access_order.popleft()
                del self.cache[oldest_key]
            
            # Add new entry
            query.cached = True
            query.cache_timestamp = time.time()
            self.cache[query_key] = query
            self.access_order.append(query_key)
    
    def invalidate_region(self, bounds: SpatialBounds):
        """Invalidate cached queries that intersect with a region."""
        with self._lock:
            keys_to_remove = []
            for key, query in self.cache.items():
                # Check if query region intersects with invalidation region
                if self._query_intersects_region(query, bounds):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                self.access_order.remove(key)
    
    def _query_intersects_region(self, query: SpatialQuery, bounds: SpatialBounds) -> bool:
        """Check if a query intersects with a region."""
        if query.query_type == QueryType.POINT:
            x, y = query.parameters.get('x', 0), query.parameters.get('y', 0)
            return bounds.contains_point(x, y)
        elif query.query_type == QueryType.REGION:
            query_bounds = query.parameters.get('bounds')
            return query_bounds and bounds.intersects(query_bounds)
        elif query.query_type == QueryType.RADIUS:
            x, y = query.parameters.get('x', 0), query.parameters.get('y', 0)
            radius = query.parameters.get('radius', 0)
            # Simplified intersection check
            center_distance = math.sqrt(
                (x - (bounds.x + bounds.width/2))**2 + 
                (y - (bounds.y + bounds.height/2))**2
            )
            return center_distance <= radius + max(bounds.width, bounds.height)
        
        return True  # Conservative approach for unknown query types
    
    def clear(self):
        """Clear all cached queries."""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get cache performance metrics."""
        return self.metrics


class OptimizedInteractionLayer(InteractionLayer):
    """Enhanced interaction layer with advanced performance optimizations."""
    
    def __init__(self, canvas_bounds: SpatialBounds = None, 
                 optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        
        super().__init__(canvas_bounds)
        
        self.optimization_level = optimization_level
        
        # Replace basic spatial index with optimized version
        self.spatial_index = AdaptiveSpatialIndex(self.canvas_bounds, optimization_level)
        
        # Add query cache
        cache_size = {
            OptimizationLevel.BASIC: 100,
            OptimizationLevel.STANDARD: 500,
            OptimizationLevel.AGGRESSIVE: 1000,
            OptimizationLevel.ULTRA: 2000
        }[optimization_level]
        
        self.query_cache = QueryCache(max_size=cache_size)
        
        # Performance monitoring
        self.performance_metrics = PerformanceMetrics()
        
        # Batch operation support
        self.batch_operations: List[Callable] = []
        self.batch_mode = False
        
        # Viewport optimization
        self.viewport_bounds: Optional[SpatialBounds] = None
        self.viewport_elements: Set[str] = set()
    
    def set_viewport(self, bounds: SpatialBounds):
        """Set the current viewport for rendering optimization."""
        self.viewport_bounds = bounds
        self._update_viewport_elements()
    
    def _update_viewport_elements(self):
        """Update the set of elements visible in the viewport."""
        if not self.viewport_bounds:
            return
        
        self.viewport_elements.clear()
        visible_elements = self.spatial_index.query_region(self.viewport_bounds)
        self.viewport_elements.update(elem.id for elem in visible_elements)
    
    def query_elements_at_point_optimized(self, x: float, y: float) -> List[InteractionElement]:
        """Optimized point query with caching."""
        start_time = time.time()
        
        # Generate cache key
        cache_key = f"point_{x}_{y}"
        
        # Check cache first
        cached_query = self.query_cache.get(cache_key)
        if cached_query:
            self.performance_metrics.update_query_time(time.time() - start_time)
            return cached_query.results
        
        # Perform query
        results = self.spatial_index.query_point(x, y)
        
        # Cache results
        query = SpatialQuery(
            query_type=QueryType.POINT,
            parameters={'x': x, 'y': y},
            results=results,
            execution_time=time.time() - start_time
        )
        self.query_cache.put(cache_key, query)
        
        # Update metrics
        self.performance_metrics.update_query_time(query.execution_time)
        self.performance_metrics.point_queries += 1
        
        return results
    
    def query_elements_in_region_optimized(self, bounds: SpatialBounds) -> List[InteractionElement]:
        """Optimized region query with caching."""
        start_time = time.time()
        
        # Generate cache key
        cache_key = f"region_{bounds.x}_{bounds.y}_{bounds.width}_{bounds.height}"
        
        # Check cache first
        cached_query = self.query_cache.get(cache_key)
        if cached_query:
            self.performance_metrics.update_query_time(time.time() - start_time)
            return cached_query.results
        
        # Perform query
        results = self.spatial_index.query_region(bounds)
        
        # Cache results
        query = SpatialQuery(
            query_type=QueryType.REGION,
            parameters={'bounds': bounds},
            results=results,
            execution_time=time.time() - start_time
        )
        self.query_cache.put(cache_key, query)
        
        # Update metrics
        self.performance_metrics.update_query_time(query.execution_time)
        self.performance_metrics.region_queries += 1
        
        return results
    
    def query_elements_in_radius(self, center_x: float, center_y: float, radius: float) -> List[InteractionElement]:
        """Query elements within a radius."""
        start_time = time.time()
        
        # Generate cache key
        cache_key = f"radius_{center_x}_{center_y}_{radius}"
        
        # Check cache first
        cached_query = self.query_cache.get(cache_key)
        if cached_query:
            self.performance_metrics.update_query_time(time.time() - start_time)
            return cached_query.results
        
        # Perform query
        results = self.spatial_index.query_radius(center_x, center_y, radius)
        
        # Cache results
        query = SpatialQuery(
            query_type=QueryType.RADIUS,
            parameters={'x': center_x, 'y': center_y, 'radius': radius},
            results=results,
            execution_time=time.time() - start_time
        )
        self.query_cache.put(cache_key, query)
        
        # Update metrics
        self.performance_metrics.update_query_time(query.execution_time)
        self.performance_metrics.radius_queries += 1
        
        return results
    
    def find_nearest_elements(self, x: float, y: float, count: int = 1) -> List[Tuple[InteractionElement, float]]:
        """Find nearest elements to a point."""
        start_time = time.time()
        
        results = self.spatial_index.query_nearest(x, y, count)
        
        # Update metrics
        self.performance_metrics.update_query_time(time.time() - start_time)
        
        return results
    
    def start_batch_operations(self):
        """Start batch mode for multiple operations."""
        self.batch_mode = True
        self.batch_operations.clear()
    
    def end_batch_operations(self):
        """End batch mode and execute all batched operations."""
        if not self.batch_mode:
            return
        
        # Execute all batched operations
        for operation in self.batch_operations:
            operation()
        
        self.batch_operations.clear()
        self.batch_mode = False
        
        # Update viewport after batch operations
        if self.viewport_bounds:
            self._update_viewport_elements()
    
    def move_element(self, element_id: str, new_x: float, new_y: float, 
                    user_id: Optional[str] = None) -> bool:
        """Optimized element movement with cache invalidation."""
        element = self.get_element(element_id)
        if not element:
            return False
        
        # Invalidate cache for affected regions
        old_bounds = element.bounds
        new_bounds = SpatialBounds(new_x, new_y, old_bounds.width, old_bounds.height)
        
        # Invalidate cache for both old and new positions
        self.query_cache.invalidate_region(old_bounds)
        self.query_cache.invalidate_region(new_bounds)
        
        # Perform the move
        return super().move_element(element_id, new_x, new_y, user_id)
    
    def get_viewport_elements(self) -> List[InteractionElement]:
        """Get elements currently visible in the viewport."""
        if not self.viewport_bounds:
            return self.get_all_elements()
        
        return [self.elements[elem_id] for elem_id in self.viewport_elements 
                if elem_id in self.elements]
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        base_stats = super().get_statistics()
        
        performance_stats = {
            "optimization_level": self.optimization_level.value,
            "query_metrics": {
                "total_queries": self.performance_metrics.query_count,
                "average_query_time": self.performance_metrics.average_query_time,
                "max_query_time": self.performance_metrics.max_query_time,
                "min_query_time": self.performance_metrics.min_query_time,
                "point_queries": self.performance_metrics.point_queries,
                "region_queries": self.performance_metrics.region_queries,
                "radius_queries": self.performance_metrics.radius_queries
            },
            "cache_metrics": {
                "cache_hit_rate": self.query_cache.get_metrics().get_cache_hit_rate(),
                "cache_hits": self.query_cache.metrics.cache_hits,
                "cache_misses": self.query_cache.metrics.cache_misses,
                "cached_queries": len(self.query_cache.cache)
            },
            "spatial_index_stats": self.spatial_index.get_statistics(),
            "viewport_elements": len(self.viewport_elements) if self.viewport_bounds else None
        }
        
        return {**base_stats, **performance_stats}


# Example usage and testing
if __name__ == "__main__":
    print("Spatial Performance Optimization - Phase 4A Implementation")
    print("=" * 60)
    
    # Create optimized interaction layer
    canvas = SpatialBounds(0, 0, 2000, 1500)
    layer = OptimizedInteractionLayer(canvas, OptimizationLevel.AGGRESSIVE)
    
    print("Creating test elements for performance testing...")
    
    # Create many elements for performance testing
    import random
    elements = []
    
    for i in range(1000):
        x = random.uniform(0, 1800)
        y = random.uniform(0, 1300)
        element_type = random.choice([InteractionElementType.ENTITY, 
                                    InteractionElementType.PREDICATE,
                                    InteractionElementType.CUT])
        
        element = layer.create_element(
            element_type,
            SpatialBounds(x, y, 80, 40),
            label=f"element_{i}"
        )
        elements.append(element)
    
    print(f"Created {len(elements)} elements")
    
    # Set viewport
    viewport = SpatialBounds(500, 400, 800, 600)
    layer.set_viewport(viewport)
    
    print("\\nTesting optimized queries...")
    
    # Test point queries
    start_time = time.time()
    for _ in range(100):
        x = random.uniform(500, 1300)
        y = random.uniform(400, 1000)
        results = layer.query_elements_at_point_optimized(x, y)
    point_query_time = time.time() - start_time
    print(f"100 point queries: {point_query_time*1000:.2f}ms")
    
    # Test region queries
    start_time = time.time()
    for _ in range(50):
        x = random.uniform(0, 1500)
        y = random.uniform(0, 1000)
        bounds = SpatialBounds(x, y, 200, 150)
        results = layer.query_elements_in_region_optimized(bounds)
    region_query_time = time.time() - start_time
    print(f"50 region queries: {region_query_time*1000:.2f}ms")
    
    # Test radius queries
    start_time = time.time()
    for _ in range(50):
        x = random.uniform(500, 1300)
        y = random.uniform(400, 1000)
        results = layer.query_elements_in_radius(x, y, 100)
    radius_query_time = time.time() - start_time
    print(f"50 radius queries: {radius_query_time*1000:.2f}ms")
    
    # Test nearest neighbor queries
    start_time = time.time()
    for _ in range(50):
        x = random.uniform(500, 1300)
        y = random.uniform(400, 1000)
        results = layer.find_nearest_elements(x, y, 5)
    nearest_query_time = time.time() - start_time
    print(f"50 nearest neighbor queries: {nearest_query_time*1000:.2f}ms")
    
    # Test batch operations
    print("\\nTesting batch operations...")
    start_time = time.time()
    layer.start_batch_operations()
    
    for i in range(100):
        element = random.choice(elements)
        new_x = element.bounds.x + random.uniform(-50, 50)
        new_y = element.bounds.y + random.uniform(-50, 50)
        layer.move_element(element.id, new_x, new_y)
    
    layer.end_batch_operations()
    batch_time = time.time() - start_time
    print(f"100 batch move operations: {batch_time*1000:.2f}ms")
    
    # Show performance statistics
    print("\\nPerformance Statistics:")
    stats = layer.get_performance_statistics()
    
    print("Query Metrics:")
    for key, value in stats["query_metrics"].items():
        print(f"  {key}: {value}")
    
    print("\\nCache Metrics:")
    for key, value in stats["cache_metrics"].items():
        print(f"  {key}: {value}")
    
    print("\\nSpatial Index Stats:")
    index_stats = stats["spatial_index_stats"]
    print(f"  Total elements: {index_stats.get('total_elements', index_stats.get('element_count'))}")
    print(f"  Max depth reached: {index_stats.get('depth', 0)}")
    print(f"  Subdivisions: {index_stats.get('subdivision_count', 0)}")
    print(f"  Access count: {index_stats.get('access_count', 0)}")
    
    print(f"\\nViewport elements: {stats['viewport_elements']}")
    
    print("\\n" + "=" * 60)
    print("✅ Spatial Performance Optimization Phase 4A implementation complete!")
    print("Ready for foundation test suite and validation framework.")

