# planning_api/geometry/utils.py
import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class Point3D:
    """3D Point representation"""
    x: float
    y: float
    z: float = 0.0
    
    def distance_to(self, other: 'Point3D') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def __add__(self, other: 'Point3D') -> 'Point3D':
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Point3D') -> 'Point3D':
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float) -> 'Point3D':
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __truediv__(self, scalar: float) -> 'Point3D':
        return Point3D(self.x / scalar, self.y / scalar, self.z / scalar)


@dataclass
class Vector3D:
    """3D Vector representation"""
    x: float
    y: float
    z: float = 0.0
    
    def length(self) -> float:
        """Calculate vector length"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector3D':
        """Return normalized vector"""
        length = self.length()
        if length == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / length, self.y / length, self.z / length)
    
    def dot(self, other: 'Vector3D') -> float:
        """Dot product with another vector"""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'Vector3D') -> 'Vector3D':
        """Cross product with another vector"""
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def angle_to(self, other: 'Vector3D') -> float:
        """Calculate angle to another vector in radians"""
        dot_product = self.dot(other)
        lengths = self.length() * other.length()
        if lengths == 0:
            return 0
        cos_angle = max(-1, min(1, dot_product / lengths))
        return math.acos(cos_angle)
    
    def is_parallel_to(self, other: 'Vector3D', tolerance: float = 1e-6) -> int:
        """Check if parallel to another vector. Returns 1 (same), -1 (opposite), 0 (not parallel)"""
        if self.length() == 0 or other.length() == 0:
            return 0
        
        normalized_self = self.normalize()
        normalized_other = other.normalize()
        
        # Check if same direction
        diff = normalized_self - normalized_other
        if abs(diff.x) <= tolerance and abs(diff.y) <= tolerance and abs(diff.z) <= tolerance:
            return 1
        
        # Check if opposite direction
        sum_vec = normalized_self + normalized_other
        if abs(sum_vec.x) <= tolerance and abs(sum_vec.y) <= tolerance and abs(sum_vec.z) <= tolerance:
            return -1
        
        return 0
    
    def __add__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float) -> 'Vector3D':
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)


@dataclass
class Line:
    """3D Line representation"""
    start: Point3D
    end: Point3D
    
    @property
    def direction(self) -> Vector3D:
        """Get line direction vector"""
        return Vector3D(
            self.end.x - self.start.x,
            self.end.y - self.start.y,
            self.end.z - self.start.z
        )
    
    @property
    def length(self) -> float:
        """Get line length"""
        return self.start.distance_to(self.end)
    
    def point_at(self, t: float) -> Point3D:
        """Get point at parameter t (0 = start, 1 = end)"""
        return Point3D(
            self.start.x + t * (self.end.x - self.start.x),
            self.start.y + t * (self.end.y - self.start.y),
            self.start.z + t * (self.end.z - self.start.z)
        )
    
    def closest_point(self, point: Point3D, limit_to_segment: bool = True) -> Point3D:
        """Find closest point on line to given point"""
        direction = self.direction
        start_to_point = Vector3D(
            point.x - self.start.x,
            point.y - self.start.y,
            point.z - self.start.z
        )
        
        length_squared = direction.dot(direction)
        if length_squared == 0:
            return self.start
        
        t = start_to_point.dot(direction) / length_squared
        
        if limit_to_segment:
            t = max(0, min(1, t))
        
        return self.point_at(t)
    
    def closest_parameter(self, point: Point3D) -> float:
        """Get parameter of closest point on line"""
        direction = self.direction
        start_to_point = Vector3D(
            point.x - self.start.x,
            point.y - self.start.y,
            point.z - self.start.z
        )
        
        length_squared = direction.dot(direction)
        if length_squared == 0:
            return 0
        
        return start_to_point.dot(direction) / length_squared


@dataclass
class Plane:
    """3D Plane representation"""
    origin: Point3D
    normal: Vector3D
    
    def __post_init__(self):
        """Ensure normal is normalized"""
        self.normal = self.normal.normalize()
    
    def closest_point(self, point: Point3D) -> Point3D:
        """Project point onto plane"""
        to_point = Vector3D(
            point.x - self.origin.x,
            point.y - self.origin.y,
            point.z - self.origin.z
        )
        
        distance = to_point.dot(self.normal)
        projection_vector = self.normal * distance
        
        return Point3D(
            point.x - projection_vector.x,
            point.y - projection_vector.y,
            point.z - projection_vector.z
        )
    
    def distance_to_point(self, point: Point3D) -> float:
        """Calculate signed distance from point to plane"""
        to_point = Vector3D(
            point.x - self.origin.x,
            point.y - self.origin.y,
            point.z - self.origin.z
        )
        return to_point.dot(self.normal)


class Polyline:
    """3D Polyline representation"""
    
    def __init__(self, points: List[Point3D]):
        self.points = points
    
    @property
    def is_closed(self) -> bool:
        """Check if polyline is closed"""
        if len(self.points) < 4:
            return False
        return self.points[0].distance_to(self.points[-1]) < 1e-6
    
    @property
    def is_valid(self) -> bool:
        """Check if polyline is valid"""
        return len(self.points) >= 2
    
    @property
    def length(self) -> float:
        """Calculate total polyline length"""
        total = 0.0
        for i in range(len(self.points) - 1):
            total += self.points[i].distance_to(self.points[i + 1])
        return total
    
    def get_area(self) -> float:
        """Calculate area using shoelace formula (for closed planar polylines)"""
        if not self.is_closed or len(self.points) < 4:
            return 0.0
        
        # Using shoelace formula for 3D polygons
        area = 0.0
        p0 = self.points[0]
        a = b = c = 0.0
        
        for i in range(1, len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            
            v1 = Vector3D(p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
            v2 = Vector3D(p2.x - p0.x, p2.y - p0.y, p2.z - p0.z)
            
            a += (v1.y * v2.z) - (v2.y * v1.z)
            b -= (v1.z * v2.x) - (v2.z * v1.x)
            c += (v1.x * v2.y) - (v2.x * v1.y)
        
        area = math.sqrt(a * a + b * b + c * c) / 2
        return area
    
    def get_centroid(self) -> Point3D:
        """Calculate centroid of closed polyline"""
        if not self.is_closed or len(self.points) < 4:
            # Simple average for open polylines
            x = sum(p.x for p in self.points) / len(self.points)
            y = sum(p.y for p in self.points) / len(self.points)
            z = sum(p.z for p in self.points) / len(self.points)
            return Point3D(x, y, z)
        
        # For closed polylines, use proper polygon centroid calculation
        area = 0.0
        cx = cy = 0.0
        
        for i in range(len(self.points) - 1):
            x0, y0 = self.points[i].x, self.points[i].y
            x1, y1 = self.points[i + 1].x, self.points[i + 1].y
            
            cross = x0 * y1 - x1 * y0
            area += cross
            cx += (x0 + x1) * cross
            cy += (y0 + y1) * cross
        
        area *= 0.5
        if area == 0:
            # Fallback to simple average
            x = sum(p.x for p in self.points) / len(self.points)
            y = sum(p.y for p in self.points) / len(self.points)
            z = sum(p.z for p in self.points) / len(self.points)
            return Point3D(x, y, z)
        
        cx /= (6.0 * area)
        cy /= (6.0 * area)
        
        # Average Z coordinate
        z = sum(p.z for p in self.points) / len(self.points)
        
        return Point3D(cx, cy, z)
    
    def point_at_parameter(self, t: float) -> Point3D:
        """Get point at normalized parameter (0 to 1) along polyline"""
        if t <= 0:
            return self.points[0]
        if t >= 1:
            return self.points[-1]
        
        target_length = t * self.length
        current_length = 0.0
        
        for i in range(len(self.points) - 1):
            segment_length = self.points[i].distance_to(self.points[i + 1])
            
            if current_length + segment_length >= target_length:
                # Point is on this segment
                segment_t = (target_length - current_length) / segment_length
                return Point3D(
                    self.points[i].x + segment_t * (self.points[i + 1].x - self.points[i].x),
                    self.points[i].y + segment_t * (self.points[i + 1].y - self.points[i].y),
                    self.points[i].z + segment_t * (self.points[i + 1].z - self.points[i].z)
                )
            
            current_length += segment_length
        
        return self.points[-1]
    
    def closest_parameter(self, point: Point3D) -> float:
        """Find parameter of closest point on polyline"""
        min_distance = float('inf')
        best_param = 0.0
        current_length = 0.0
        
        for i in range(len(self.points) - 1):
            line = Line(self.points[i], self.points[i + 1])
            closest = line.closest_point(point, limit_to_segment=True)
            distance = point.distance_to(closest)
            
            if distance < min_distance:
                min_distance = distance
                line_param = line.closest_parameter(point)
                line_param = max(0, min(1, line_param))  # Clamp to segment
                best_param = (current_length + line_param * line.length) / self.length
            
            current_length += line.length
        
        return min_distance, best_param
    
    def make_closed(self, tolerance: float = 1e-6) -> bool:
        """Make polyline closed if endpoints are close enough"""
        if self.is_closed:
            return True
        
        if len(self.points) < 3:
            return False
        
        if self.points[0].distance_to(self.points[-1]) <= tolerance:
            self.points[-1] = self.points[0]
            return True
        
        return False
    
    def get_bounding_box(self) -> Tuple[Point3D, Point3D]:
        """Get bounding box as (min_point, max_point)"""
        if not self.points:
            return Point3D(0, 0, 0), Point3D(0, 0, 0)
        
        min_x = min(p.x for p in self.points)
        max_x = max(p.x for p in self.points)
        min_y = min(p.y for p in self.points)
        max_y = max(p.y for p in self.points)
        min_z = min(p.z for p in self.points)
        max_z = max(p.z for p in self.points)
        
        return Point3D(min_x, min_y, min_z), Point3D(max_x, max_y, max_z)


class GeometryUtils:
    """Utility functions for geometry operations"""
    
    @staticmethod
    def point_in_polygon_2d(point: Point3D, polygon: List[Point3D]) -> bool:
        """Test if point is inside 2D polygon using ray casting"""
        x, y = point.x, point.y
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0].x, polygon[0].y
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n].x, polygon[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    @staticmethod
    def line_intersection_2d(line1: Line, line2: Line, tolerance: float = 1e-6) -> Optional[Tuple[float, float]]:
        """Find intersection parameters for two 2D lines"""
        x1, y1 = line1.start.x, line1.start.y
        x2, y2 = line1.end.x, line1.end.y
        x3, y3 = line2.start.x, line2.start.y
        x4, y4 = line2.end.x, line2.end.y
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        if abs(denom) < tolerance:
            return None  # Lines are parallel
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        return t, u
    
    @staticmethod
    def lines_intersect_2d(line1: Line, line2: Line, tolerance: float = 1e-6, finite_segments: bool = True) -> bool:
        """Check if two 2D lines intersect"""
        intersection = GeometryUtils.line_intersection_2d(line1, line2, tolerance)
        
        if intersection is None:
            return False
        
        t, u = intersection
        
        if finite_segments:
            return 0 <= t <= 1 and 0 <= u <= 1
        
        return True
    
    @staticmethod
    def polygon_self_intersects(polygon: List[Point3D], tolerance: float = 1e-6) -> bool:
        """Check if polygon self-intersects"""
        n = len(polygon)
        
        for i in range(n):
            line1 = Line(polygon[i], polygon[(i + 1) % n])
            
            # Check against non-adjacent edges
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue  # Skip last edge when starting from first
                
                line2 = Line(polygon[j], polygon[(j + 1) % n])
                
                if GeometryUtils.lines_intersect_2d(line1, line2, tolerance, True):
                    return True
        
        return False
    
    @staticmethod
    def create_inset_polygon(polygon: List[Point3D], inset_distance: float) -> List[Point3D]:
        """Create an inset polygon (simplified approach moving vertices toward centroid)"""
        if len(polygon) < 3:
            return polygon
        
        # Calculate centroid
        cx = sum(p.x for p in polygon) / len(polygon)
        cy = sum(p.y for p in polygon) / len(polygon)
        cz = sum(p.z for p in polygon) / len(polygon)
        centroid = Point3D(cx, cy, cz)
        
        inset_polygon = []
        for point in polygon:
            # Vector from point to centroid
            to_centroid = Vector3D(
                centroid.x - point.x,
                centroid.y - point.y,
                centroid.z - point.z
            )
            
            length = to_centroid.length()
            if length > inset_distance:
                # Move point toward centroid by inset_distance
                normalized = to_centroid.normalize()
                new_point = Point3D(
                    point.x + normalized.x * inset_distance,
                    point.y + normalized.y * inset_distance,
                    point.z + normalized.z * inset_distance
                )
                inset_polygon.append(new_point)
        
        return inset_polygon if len(inset_polygon) >= 3 else polygon
    
    @staticmethod
    def offset_line(line: Line, direction_point: Point3D, distance: float, plane_normal: Vector3D = None) -> Line:
        """Offset a line by a distance in a direction"""
        if plane_normal is None:
            # Create a default plane normal perpendicular to the line and pointing up
            line_dir = line.direction.normalize()
            if abs(line_dir.z) < 0.9:
                plane_normal = Vector3D(0, 0, 1)
            else:
                plane_normal = Vector3D(1, 0, 0)
        
        line_dir = line.direction.normalize()
        offset_dir = line_dir.cross(plane_normal).normalize()
        
        # Choose direction based on which side the direction_point is on
        to_dir_point = Vector3D(
            direction_point.x - line.start.x,
            direction_point.y - line.start.y,
            direction_point.z - line.start.z
        )
        
        if to_dir_point.dot(offset_dir) < 0:
            offset_dir = offset_dir * -1
        
        offset_vector = offset_dir * distance
        
        new_start = Point3D(
            line.start.x + offset_vector.x,
            line.start.y + offset_vector.y,
            line.start.z + offset_vector.z
        )
        
        new_end = Point3D(
            line.end.x + offset_vector.x,
            line.end.y + offset_vector.y,
            line.end.z + offset_vector.z
        )
        
        return Line(new_start, new_end)