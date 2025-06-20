# planning_api/geometry/line_addon.py
import math
from typing import Tuple
from .utils import Point3D, Vector3D, Line, Plane
from .constants import Constants
from .vector3d_addon import Vector3DAddOn
from .plane_addon import PlaneAddOn


class Interval:
    """Interval representation"""
    def __init__(self, t0: float, t1: float):
        self.t0 = min(t0, t1)
        self.t1 = max(t0, t1)
    
    @property
    def min(self) -> float:
        return self.t0
    
    @property
    def max(self) -> float:
        return self.t1
    
    @property
    def length(self) -> float:
        return self.t1 - self.t0
    
    def __eq__(self, other):
        if isinstance(other, Interval):
            return abs(self.t0 - other.t0) < Constants.TOLERANCE and abs(self.t1 - other.t1) < Constants.TOLERANCE
        return False


class LineAddOn:
    """Enhanced line operations similar to C# LineAddOn"""
    
    @staticmethod
    def parameter_at_point(line: Line, point: Point3D) -> float:
        """
        Get parameter value at point on line
        Returns parameter (0 = start, 1 = end, negative if before start)
        """
        if point is None:
            raise ValueError("Point is null")
        if line is None:
            raise ValueError("Line is null")
        if not line.is_valid:
            raise ValueError("Line is not valid")
        
        # Vector from line start to direction
        line_direction = line.direction.normalize()
        
        # Create plane at line start with line direction as normal
        plane_at_start = Plane(line.start, line_direction)
        
        # Project point onto plane
        projected_point = plane_at_start.closest_point(point)
        
        # Vector from projected point to actual point
        point_to_projected = Vector3D(
            point.x - projected_point.x,
            point.y - projected_point.y,
            point.z - projected_point.z
        )
        
        point_to_projected = point_to_projected.normalize()
        
        if point_to_projected.length() == 0:
            return 0.0
        
        # Check if point is in line direction or opposite
        if Vector3DAddOn.is_parallel_to(line_direction, point_to_projected) != 1:
            # Point is before line start
            return -(line.start.distance_to(point) / line.length)
        else:
            # Point is after line start
            return line.start.distance_to(point) / line.length
    
    @staticmethod
    def interval_of_internal_points(line: Line, point1: Point3D, point2: Point3D) -> Interval:
        """Get interval between two points on line"""
        if line is None:
            raise ValueError("Line is null")
        if point1 is None:
            raise ValueError("First point is null")
        if point2 is None:
            raise ValueError("Second point is null")
        if not line.is_valid:
            raise ValueError("Line is not valid")
        
        line_interval1 = line.start.distance_to(point1) / line.length
        line_interval2 = line.start.distance_to(point2) / line.length
        
        if line_interval2 < line_interval1:
            line_interval1, line_interval2 = line_interval2, line_interval1
        
        return Interval(line_interval1, line_interval2)
    
    @staticmethod
    def project_onto_plane(line: Line, target_plane: Plane) -> Tuple[bool, Line]:
        """
        Project line onto plane
        Returns (success, projected_line)
        """
        if line is None:
            raise ValueError("Line is null")
        if target_plane is None:
            raise ValueError("Plane is null")
        if not line.is_valid:
            raise ValueError("Line is not valid")
        if not target_plane.is_valid:
            raise ValueError("Plane is not valid")
        
        # Project both endpoints
        projected_start = PlaneAddOn.project_point(target_plane, line.start)
        projected_end = PlaneAddOn.project_point(target_plane, line.end)
        
        if projected_start is None or projected_end is None:
            return False, None
        
        new_line = Line(projected_start, projected_end)
        return True, new_line
    
    @staticmethod
    def offset(line: Line, direction_point: Point3D, distance: float, plane: Plane = None) -> Line:
        """
        Create offset line
        """
        if plane is None or plane.normal.length() == 0:
            # Create plane from direction point and line points
            plane = Plane.from_three_points(direction_point, line.start, line.end)
            if plane is None or plane.normal.length() == 0:
                return Line(line.start, line.end)
        
        # Create offset vector
        start_vector = line.direction.normalize()
        start_vector = start_vector * distance
        
        # Rotate by 90 degrees around plane normal
        start_vector = Vector3DAddOn.rotate(start_vector, math.pi / 2, plane.normal)
        result_start1 = Point3D(
            line.start.x + start_vector.x,
            line.start.y + start_vector.y,
            line.start.z + start_vector.z
        )
        
        # Rotate by -180 degrees to get opposite direction
        start_vector = Vector3DAddOn.rotate(start_vector, -math.pi, plane.normal)
        result_start2 = Point3D(
            line.start.x + start_vector.x,
            line.start.y + start_vector.y,
            line.start.z + start_vector.z
        )
        
        # Choose the direction closer to the direction point
        if result_start1.distance_to(direction_point) < result_start2.distance_to(direction_point):
            result_start = result_start1
        else:
            result_start = result_start2
        
        # Create offset line
        return Line(result_start, Point3D(
            result_start.x + line.direction.x,
            result_start.y + line.direction.y,
            result_start.z + line.direction.z
        ))