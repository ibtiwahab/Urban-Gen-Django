# planning_api/geometry/advanced.py - Complete implementation with all classes
import math
import random
from typing import List, Tuple, Optional, Dict, Any
from .utils import Point3D, Vector3D, Line, Plane, Polyline, GeometryUtils


class CurveOperations:
    """Advanced curve operations similar to C# CurveAddOn"""
    
    @staticmethod
    def polyline_from_vertices(flattened_vertices: List[float]) -> Polyline:
        """Convert flattened vertices to polyline"""
        points = []
        for i in range(0, len(flattened_vertices), 3):
            if i + 2 < len(flattened_vertices):
                points.append(Point3D(
                    flattened_vertices[i],
                    flattened_vertices[i + 1],
                    flattened_vertices[i + 2]
                ))
        return Polyline(points)
    
    @staticmethod
    def get_curve_plane(polyline: Polyline) -> Optional[Plane]:
        """Get the best-fit plane for a polyline"""
        if len(polyline.points) < 3:
            return None
        
        # Use first three non-collinear points to define plane
        p0 = polyline.points[0]
        p1 = polyline.points[1]
        
        for i in range(2, len(polyline.points)):
            p2 = polyline.points[i]
            
            v1 = Vector3D(p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
            v2 = Vector3D(p2.x - p0.x, p2.y - p0.y, p2.z - p0.z)
            
            normal = v1.cross(v2)
            if normal.length() > 1e-6:  # Found non-collinear points
                return Plane(p0, normal.normalize())
        
        return None
    
    @staticmethod
    def calculate_main_orientation(polyline: Polyline) -> float:
        """Calculate main orientation of the polygon (angle of longest edge)"""
        if len(polyline.points) < 2:
            return 0.0
        
        max_length = 0.0
        main_angle = 0.0
        
        for i in range(len(polyline.points)):
            j = (i + 1) % len(polyline.points)
            if j < len(polyline.points):
                dx = polyline.points[j].x - polyline.points[i].x
                dy = polyline.points[j].y - polyline.points[i].y
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > max_length:
                    max_length = length
                    main_angle = math.atan2(dy, dx)
        
        return main_angle
    
    @staticmethod
    def point_containment(polyline: Polyline, point: Point3D) -> str:
        """Check point containment in polygon. Returns 'inside', 'outside', or 'coincident'"""
        if not polyline.is_closed:
            return 'outside'
        
        # Check if point is on boundary first
        tolerance = 1e-6
        for i in range(len(polyline.points) - 1):
            line = Line(polyline.points[i], polyline.points[i + 1])
            closest = line.closest_point(point, limit_to_segment=True)
            if point.distance_to(closest) <= tolerance:
                return 'coincident'
        
        # Use ray casting for inside/outside test
        if GeometryUtils.point_in_polygon_2d(point, polyline.points):
            return 'inside'
        else:
            return 'outside'


class OffsetOperations:
    """Polygon offset operations"""
    
    @staticmethod
    def offset_polygon(polyline: Polyline, distance: float, tolerance: float = 1e-6) -> Optional[Polyline]:
        """Create offset polygon (simplified version)"""
        if not polyline.is_closed or len(polyline.points) < 4:
            return None
        
        # Simple inward offset by moving each vertex toward centroid
        centroid = polyline.get_centroid()
        offset_points = []
        
        for point in polyline.points[:-1]:  # Exclude duplicate closing point
            # Vector from centroid to point
            to_point = Vector3D(
                point.x - centroid.x,
                point.y - centroid.y,
                point.z - centroid.z
            )
            
            length = to_point.length()
            if length > distance:
                # Move point toward centroid
                direction = to_point.normalize()
                new_point = Point3D(
                    point.x - direction.x * distance,
                    point.y - direction.y * distance,
                    point.z - direction.z * distance
                )
                offset_points.append(new_point)
        
        if len(offset_points) >= 3:
            # Close the polygon
            offset_points.append(offset_points[0])
            return Polyline(offset_points)
        
        return None


class BuildingPlacement:
    """Building placement algorithms"""
    
    @staticmethod
    def generate_building_positions(
        site_polygon: List[Point3D],
        num_buildings: int,
        building_width: float,
        building_depth: float,
        min_spacing: float = 5.0,
        max_attempts: int = 1000
    ) -> List[Point3D]:
        """Generate valid building positions within polygon boundary"""
        
        if len(site_polygon) < 3:
            return []
        
        # Calculate bounding box
        min_x = min(p.x for p in site_polygon)
        max_x = max(p.x for p in site_polygon)
        min_y = min(p.y for p in site_polygon)
        max_y = max(p.y for p in site_polygon)
        
        positions = []
        attempts = 0
        
        while len(positions) < num_buildings and attempts < max_attempts:
            attempts += 1
            
            # Generate random position within bounds
            x = random.uniform(min_x + building_width/2, max_x - building_width/2)
            y = random.uniform(min_y + building_depth/2, max_y - building_depth/2)
            
            candidate = Point3D(x, y, 0)
            
            # Check if all corners of building are inside polygon
            corners = [
                Point3D(x - building_width/2, y - building_depth/2, 0),
                Point3D(x + building_width/2, y - building_depth/2, 0),
                Point3D(x + building_width/2, y + building_depth/2, 0),
                Point3D(x - building_width/2, y + building_depth/2, 0)
            ]
            
            all_inside = all(GeometryUtils.point_in_polygon_2d(corner, site_polygon) for corner in corners)
            
            if not all_inside:
                continue
            
            # Check minimum distance from existing buildings
            too_close = False
            for existing in positions:
                distance = candidate.distance_to(existing)
                if distance < (max(building_width, building_depth) + min_spacing):
                    too_close = True
                    break
            
            if not too_close:
                positions.append(candidate)
        
        return positions
    
    @staticmethod
    def generate_grid_positions(
        site_polygon: List[Point3D],
        building_width: float,
        building_depth: float,
        spacing: float = 10.0
    ) -> List[Point3D]:
        """Generate buildings in a grid pattern within the polygon"""
        
        if len(site_polygon) < 3:
            return []
        
        # Calculate bounding box
        min_x = min(p.x for p in site_polygon)
        max_x = max(p.x for p in site_polygon)
        min_y = min(p.y for p in site_polygon)
        max_y = max(p.y for p in site_polygon)
        
        positions = []
        
        # Grid spacing
        step_x = building_width + spacing
        step_y = building_depth + spacing
        
        current_x = min_x + building_width/2
        while current_x + building_width/2 <= max_x:
            current_y = min_y + building_depth/2
            while current_y + building_depth/2 <= max_y:
                candidate = Point3D(current_x, current_y, 0)
                
                # Check if building center is inside polygon
                if GeometryUtils.point_in_polygon_2d(candidate, site_polygon):
                    # Check if all corners are inside
                    corners = [
                        Point3D(current_x - building_width/2, current_y - building_depth/2, 0),
                        Point3D(current_x + building_width/2, current_y - building_depth/2, 0),
                        Point3D(current_x + building_width/2, current_y + building_depth/2, 0),
                        Point3D(current_x - building_width/2, current_y + building_depth/2, 0)
                    ]
                    
                    if all(GeometryUtils.point_in_polygon_2d(corner, site_polygon) for corner in corners):
                        positions.append(candidate)
                
                current_y += step_y
            current_x += step_x
        
        return positions


class TriangulationOperations:
    """Polygon triangulation operations"""
    
    @staticmethod
    def simple_triangulation(polygon: List[Point3D]) -> List[List[Point3D]]:
        """Simple ear clipping triangulation for polygon"""
        if len(polygon) < 3:
            return []
        
        # Remove duplicate closing point if present
        points = polygon[:-1] if len(polygon) > 3 and polygon[0].distance_to(polygon[-1]) < 1e-6 else polygon
        
        if len(points) < 3:
            return []
        
        triangles = []
        remaining = points[:]
        
        while len(remaining) > 3:
            # Find an ear (a vertex that can be removed)
            ear_found = False
            
            for i in range(len(remaining)):
                prev_i = (i - 1) % len(remaining)
                next_i = (i + 1) % len(remaining)
                
                triangle = [remaining[prev_i], remaining[i], remaining[next_i]]
                
                # Check if this is a valid ear (no other vertices inside)
                is_ear = True
                for j, point in enumerate(remaining):
                    if j != prev_i and j != i and j != next_i:
                        if GeometryUtils.point_in_polygon_2d(point, triangle):
                            is_ear = False
                            break
                
                if is_ear:
                    triangles.append(triangle)
                    remaining.pop(i)
                    ear_found = True
                    break
            
            if not ear_found:
                # Fallback: just take the first triangle
                if len(remaining) >= 3:
                    triangles.append(remaining[:3])
                    remaining.pop(1)
                else:
                    break
        
        # Add the final triangle
        if len(remaining) == 3:
            triangles.append(remaining)
        
        return triangles


class BooleanOperations:
    """Boolean operations on polygons (simplified)"""
    
    @staticmethod
    def polygon_difference(poly_a: List[Point3D], poly_b: List[Point3D]) -> List[List[Point3D]]:
        """Simplified polygon difference operation"""
        # This is a very simplified version - for production use, consider using a library like Shapely
        
        # Check if poly_b is completely inside poly_a
        b_inside_a = all(GeometryUtils.point_in_polygon_2d(p, poly_a) for p in poly_b)
        
        if not b_inside_a:
            return [poly_a]  # No intersection, return original
        
        # For simplicity, if poly_b is inside poly_a, return empty or approximation
        # In a real implementation, you'd need proper polygon clipping algorithms
        return []
    
    @staticmethod
    def polygon_intersection(poly_a: List[Point3D], poly_b: List[Point3D]) -> List[List[Point3D]]:
        """Simplified polygon intersection operation"""
        # This is a placeholder - real polygon intersection is complex
        
        # Check for vertex intersections
        intersecting_points = []
        
        for point in poly_a:
            if GeometryUtils.point_in_polygon_2d(point, poly_b):
                intersecting_points.append(point)
        
        for point in poly_b:
            if GeometryUtils.point_in_polygon_2d(point, poly_a):
                intersecting_points.append(point)
        
        if len(intersecting_points) >= 3:
            return [intersecting_points]
        
        return []


class IntersectionOperations:
    """Line and curve intersection operations"""
    
    @staticmethod
    def line_line_intersection(line1: Line, line2: Line, tolerance: float = 1e-6) -> Optional[Tuple[Point3D, float, float]]:
        """Find intersection point and parameters for two lines"""
        intersection = GeometryUtils.line_intersection_2d(line1, line2, tolerance)
        
        if intersection is None:
            return None
        
        t, u = intersection
        
        # Calculate intersection point
        point = line1.point_at(t)
        
        return point, t, u
    
    @staticmethod
    def line_polyline_intersections(line: Line, polyline: Polyline, tolerance: float = 1e-6) -> List[Tuple[Point3D, float, float]]:
        """Find all intersections between a line and polyline"""
        intersections = []
        
        for i in range(len(polyline.points) - 1):
            segment = Line(polyline.points[i], polyline.points[i + 1])
            intersection = IntersectionOperations.line_line_intersection(line, segment, tolerance)
            
            if intersection is not None:
                point, t, u = intersection
                # Check if intersection is within both line segments
                if 0 <= t <= 1 and 0 <= u <= 1:
                    intersections.append((point, t, u))
        
        return intersections
    
    @staticmethod
    def polyline_self_intersection_check(polyline: Polyline, tolerance: float = 1e-6) -> bool:
        """Check if polyline self-intersects"""
        points = polyline.points
        n = len(points)
        
        for i in range(n - 1):
            line1 = Line(points[i], points[i + 1])
            
            # Check against non-adjacent segments
            start_j = i + 2
            end_j = n - 1 if i > 0 else n - 2  # Avoid checking last segment against first
            
            for j in range(start_j, end_j):
                line2 = Line(points[j], points[j + 1])
                
                if GeometryUtils.lines_intersect_2d(line1, line2, tolerance, True):
                    return True
        
        return False


class SurfaceOperations:
    """Surface and 3D operations"""
    
    @staticmethod
    def create_extruded_building(
        base_polygon: List[Point3D],
        floor_heights: List[float],
        base_z: float = 0.0
    ) -> Dict[str, Any]:
        """Create extruded building geometry"""
        
        floors = []
        current_z = base_z
        
        for floor_height in floor_heights:
            # Create floor polygon at current height
            floor_points = []
            for point in base_polygon:
                floor_points.append(Point3D(point.x, point.y, current_z))
            
            floors.append({
                'vertices': floor_points,
                'height': floor_height,
                'z_level': current_z
            })
            
            current_z += floor_height
        
        return {
            'floors': floors,
            'total_height': current_z - base_z,
            'base_polygon': base_polygon
        }
    
    @staticmethod
    def create_building_vertices_array(
        center: Point3D,
        width: float,
        depth: float,
        floors: int,
        floor_height: float,
        base_z: float = 0.0
    ) -> List[List[float]]:
        """Create building vertices array for each floor"""
        
        half_width = width / 2
        half_depth = depth / 2
        
        vertices_per_floor = []
        
        for floor in range(floors):
            z = base_z + floor * floor_height
            
            # Create rectangular floor vertices (clockwise from bottom-left)
            floor_vertices = [
                center.x - half_width, center.y - half_depth, z,  # Bottom-left
                center.x + half_width, center.y - half_depth, z,  # Bottom-right
                center.x + half_width, center.y + half_depth, z,  # Top-right
                center.x - half_width, center.y + half_depth, z   # Top-left
            ]
            
            vertices_per_floor.append(floor_vertices)
        
        return vertices_per_floor


class ParametricDesign:
    """Enhanced parametric design operations with better building generation"""
    
    @staticmethod
    def apply_site_parameters(
        site_polygon: List[Point3D],
        site_area: float,
        density: float = 0.5,
        far: float = 1.0,
        mix_ratio: float = 0.0,
        building_style: int = 0,
        orientation: float = 0.0,
        max_buildings: int = 50  # Added max_buildings parameter
    ) -> Dict[str, Any]:
        """Apply parametric design rules to generate building layout - IMPROVED VERSION"""
        
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Applying site parameters: density={density}, far={far}, building_style={building_style}, max_buildings={max_buildings}")
        
        # Enhanced building size calculation based on parameters
        building_width, building_depth = ParametricDesign._calculate_building_dimensions(
            density, building_style, site_area
        )
        
        # Enhanced number of buildings calculation
        num_buildings = ParametricDesign._calculate_num_buildings(
            site_area, density, building_width, building_depth, max_buildings
        )
        
        # Enhanced floor calculation based on FAR
        floors_per_building, floor_height = ParametricDesign._calculate_floors(
            site_area, far, num_buildings, building_width, building_depth, building_style
        )
        
        logger.info(f"Calculated: {num_buildings} buildings, {building_width:.1f}x{building_depth:.1f}m, {floors_per_building} floors")
        
        # Enhanced building placement strategy
        building_positions = ParametricDesign._generate_building_positions(
            site_polygon, num_buildings, building_width, building_depth, 
            density, orientation, max_buildings
        )
        
        logger.info(f"Generated {len(building_positions)} building positions")
        
        return {
            'building_positions': building_positions,
            'building_width': building_width,
            'building_depth': building_depth,
            'floors_per_building': floors_per_building,
            'floor_height': floor_height,
            'num_buildings': len(building_positions),
            'total_floor_area': len(building_positions) * floors_per_building * (building_width * building_depth)
        }
    
    @staticmethod
    def _calculate_building_dimensions(density: float, building_style: int, site_area: float) -> Tuple[float, float]:
        """Calculate building dimensions based on parameters"""
        
        # Base dimensions by building style
        base_dimensions = {
            0: (15.0, 12.0),   # Residential
            1: (18.0, 14.0),   # Office
            2: (22.0, 16.0),   # Commercial
            3: (16.0, 13.0)    # Mixed
        }
        
        base_width, base_depth = base_dimensions.get(building_style, (15.0, 12.0))
        
        # Scale by density (higher density = larger buildings to accommodate more people)
        density_scale = 0.8 + (density * 0.6)  # Range: 0.8 to 1.4
        
        # Scale by site area (larger sites can accommodate larger buildings)
        area_scale = 1.0
        if site_area > 10000:  # Large site
            area_scale = 1.2
        elif site_area > 5000:  # Medium site
            area_scale = 1.1
        elif site_area < 1000:  # Small site
            area_scale = 0.9
        
        final_width = base_width * density_scale * area_scale
        final_depth = base_depth * density_scale * area_scale
        
        # Ensure reasonable limits
        final_width = max(10.0, min(40.0, final_width))
        final_depth = max(8.0, min(30.0, final_depth))
        
        return final_width, final_depth
    
    @staticmethod
    def _calculate_num_buildings(
        site_area: float, density: float, building_width: float, 
        building_depth: float, max_buildings: int
    ) -> int:
        """Calculate number of buildings based on site parameters"""
        
        # Building footprint
        building_footprint = building_width * building_depth
        
        # Minimum spacing between buildings (varies with density)
        if density > 0.8:
            min_spacing = 3.0
        elif density > 0.6:
            min_spacing = 5.0
        elif density > 0.4:
            min_spacing = 8.0
        else:
            min_spacing = 12.0
        
        # Total space needed per building (including spacing)
        spacing_area = min_spacing * min_spacing
        total_space_per_building = building_footprint + spacing_area
        
        # Theoretical maximum based on area
        theoretical_max = int(site_area / total_space_per_building)
        
        # Apply density factor
        density_adjusted = int(theoretical_max * density)
        
        # Ensure minimum and maximum bounds
        num_buildings = max(1, min(density_adjusted, max_buildings))
        
        # Additional constraint: ensure buildings fit physically
        if num_buildings > theoretical_max:
            num_buildings = theoretical_max
        
        return num_buildings
    
    @staticmethod
    def _calculate_floors(
        site_area: float, far: float, num_buildings: int, 
        building_width: float, building_depth: float, building_style: int
    ) -> Tuple[int, float]:
        """Calculate number of floors and floor height"""
        
        # Floor heights by building style
        floor_heights = {
            0: 3.0,   # Residential
            1: 3.5,   # Office
            2: 4.0,   # Commercial
            3: 3.2    # Mixed
        }
        
        floor_height = floor_heights.get(building_style, 3.0)
        
        # Calculate total required floor area from FAR
        total_floor_area_needed = site_area * far
        
        # Floor area per building
        floor_area_per_building = building_width * building_depth
        
        # Total floor area for all buildings
        total_building_floor_area = num_buildings * floor_area_per_building
        
        # Calculate floors needed
        if total_building_floor_area > 0:
            floors_per_building = max(1, int(total_floor_area_needed / total_building_floor_area))
        else:
            floors_per_building = 1
        
        # Reasonable limits for floors
        floors_per_building = max(1, min(20, floors_per_building))
        
        return floors_per_building, floor_height
    
    @staticmethod
    def _generate_building_positions(
        site_polygon: List[Point3D], num_buildings: int, building_width: float, 
        building_depth: float, density: float, orientation: float, max_buildings: int
    ) -> List[Point3D]:
        """Generate building positions using improved placement strategies"""
        
        if len(site_polygon) < 3:
            return []
        
        # Choose placement strategy based on density and number of buildings
        if density < 0.3 or num_buildings <= 5:
            # Low density: scattered placement
            return ParametricDesign._generate_scattered_positions(
                site_polygon, num_buildings, building_width, building_depth
            )
        elif density > 0.7 or num_buildings > 15:
            # High density: grid-based placement
            return ParametricDesign._generate_grid_positions(
                site_polygon, num_buildings, building_width, building_depth, orientation
            )
        else:
            # Medium density: organic placement
            return ParametricDesign._generate_organic_positions(
                site_polygon, num_buildings, building_width, building_depth, orientation
            )
    
    @staticmethod
    def _generate_scattered_positions(
        site_polygon: List[Point3D], num_buildings: int, 
        building_width: float, building_depth: float
    ) -> List[Point3D]:
        """Generate scattered building positions"""
        
        # Calculate bounding box
        min_x = min(p.x for p in site_polygon)
        max_x = max(p.x for p in site_polygon)
        min_y = min(p.y for p in site_polygon)
        max_y = max(p.y for p in site_polygon)
        
        positions = []
        attempts = 0
        max_attempts = num_buildings * 50  # More attempts for better placement
        min_distance = max(building_width, building_depth) + 8.0  # Larger spacing for scattered
        
        while len(positions) < num_buildings and attempts < max_attempts:
            attempts += 1
            
            # Generate random position within bounds
            margin_x = building_width / 2
            margin_y = building_depth / 2
            
            x = random.uniform(min_x + margin_x, max_x - margin_x)
            y = random.uniform(min_y + margin_y, max_y - margin_y)
            
            candidate = Point3D(x, y, 0)
            
            # Check if building corners are inside polygon
            if ParametricDesign._is_building_inside_polygon(
                candidate, building_width, building_depth, site_polygon
            ):
                # Check minimum distance from existing buildings
                if ParametricDesign._check_minimum_distance(candidate, positions, min_distance):
                    positions.append(candidate)
        
        return positions
    
    @staticmethod
    def _generate_grid_positions(
        site_polygon: List[Point3D], num_buildings: int, 
        building_width: float, building_depth: float, orientation: float
    ) -> List[Point3D]:
        """Generate grid-based building positions"""
        
        # Calculate bounding box
        min_x = min(p.x for p in site_polygon)
        max_x = max(p.x for p in site_polygon)
        min_y = min(p.y for p in site_polygon)
        max_y = max(p.y for p in site_polygon)
        
        # Calculate grid spacing
        spacing_x = building_width + 4.0  # Tighter spacing for grid
        spacing_y = building_depth + 4.0
        
        # Calculate grid dimensions
        grid_width = max_x - min_x
        grid_height = max_y - min_y
        
        cols = max(1, int(grid_width / spacing_x))
        rows = max(1, int(grid_height / spacing_y))
        
        positions = []
        
        # Generate grid positions
        for row in range(rows):
            for col in range(cols):
                if len(positions) >= num_buildings:
                    break
                
                x = min_x + (col + 0.5) * spacing_x
                y = min_y + (row + 0.5) * spacing_y
                
                candidate = Point3D(x, y, 0)
                
                # Apply orientation rotation
                if abs(orientation) > 0.01:
                    candidate = ParametricDesign._rotate_point_around_center(
                        candidate, site_polygon, orientation
                    )
                
                # Check if building is inside polygon
                if ParametricDesign._is_building_inside_polygon(
                    candidate, building_width, building_depth, site_polygon
                ):
                    positions.append(candidate)
            
            if len(positions) >= num_buildings:
                break
        
        return positions[:num_buildings]
    
    @staticmethod
    def _generate_organic_positions(
        site_polygon: List[Point3D], num_buildings: int, 
        building_width: float, building_depth: float, orientation: float
    ) -> List[Point3D]:
        """Generate organic building positions with some regularity"""
        
        # Start with a loose grid
        grid_positions = ParametricDesign._generate_grid_positions(
            site_polygon, num_buildings * 2, building_width, building_depth, orientation
        )
        
        # Add randomization to grid positions
        positions = []
        variation = min(building_width, building_depth) * 0.3  # 30% variation
        min_distance = max(building_width, building_depth) + 5.0
        
        for pos in grid_positions:
            if len(positions) >= num_buildings:
                break
            
            # Add random offset
            offset_x = random.uniform(-variation, variation)
            offset_y = random.uniform(-variation, variation)
            
            new_pos = Point3D(pos.x + offset_x, pos.y + offset_y, pos.z)
            
            # Check if still inside polygon and maintains minimum distance
            if (ParametricDesign._is_building_inside_polygon(
                new_pos, building_width, building_depth, site_polygon
            ) and ParametricDesign._check_minimum_distance(new_pos, positions, min_distance)):
                positions.append(new_pos)
        
        return positions
    
    @staticmethod
    def _is_building_inside_polygon(
        center: Point3D, width: float, depth: float, polygon: List[Point3D]
    ) -> bool:
        """Check if all corners of a building are inside the polygon"""
        
        half_width = width / 2
        half_depth = depth / 2
        
        corners = [
            Point3D(center.x - half_width, center.y - half_depth, center.z),
            Point3D(center.x + half_width, center.y - half_depth, center.z),
            Point3D(center.x + half_width, center.y + half_depth, center.z),
            Point3D(center.x - half_width, center.y + half_depth, center.z)
        ]
        
        return all(GeometryUtils.point_in_polygon_2d(corner, polygon) for corner in corners)
    
    @staticmethod
    def _check_minimum_distance(
        candidate: Point3D, existing_positions: List[Point3D], min_distance: float
    ) -> bool:
        """Check if candidate maintains minimum distance from existing positions"""
        
        for existing in existing_positions:
            distance = candidate.distance_to(existing)
            if distance < min_distance:
                return False
        return True
    
    @staticmethod
    def _rotate_point_around_center(
        point: Point3D, polygon: List[Point3D], angle: float
    ) -> Point3D:
        """Rotate a point around the polygon centroid"""
        
        # Calculate polygon centroid
        centroid_x = sum(p.x for p in polygon) / len(polygon)
        centroid_y = sum(p.y for p in polygon) / len(polygon)
        
        # Translate to origin
        x = point.x - centroid_x
        y = point.y - centroid_y
        
        # Rotate
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        
        new_x = x * cos_angle - y * sin_angle
        new_y = x * sin_angle + y * cos_angle
        
        # Translate back
        return Point3D(new_x + centroid_x, new_y + centroid_y, point.z)