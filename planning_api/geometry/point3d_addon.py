# planning_api/geometry/point3d_addon.py
from typing import Optional
from .utils import Point3D, Vector3D, Line, Plane
from .vector3d_addon import Vector3DAddOn
from .plane_addon import PlaneAddOn


class Point3DAddOn:
    """Enhanced Point3D operations similar to C# Point3dAddOn"""
    
    @staticmethod
    def within_constraints_of_line(point: Point3D, line: Line) -> bool:
        """
        Check if point lies within the constraints of a line segment
        """
        if point is None:
            raise ValueError("Point is null")
        if line is None:
            raise ValueError("Line is null")
        if not line.is_valid:
            raise ValueError("Line is not valid")
        
        # Vector from line start in line direction
        line_direction = line.direction.normalize()
        plane_at_start = Plane(line.start, line_direction)
        
        # Vector from plane to point
        plane_to_point = Vector3D(
            point.x - plane_at_start.closest_point(point).x,
            point.y - plane_at_start.closest_point(point).y,
            point.z - plane_at_start.closest_point(point).z
        )
        plane_to_point = plane_to_point.normalize()
        
        # If point is on the line plane
        if plane_to_point.length() == 0:
            return True
        
        # Check if point is in same direction as line
        if Vector3DAddOn.is_parallel_to(line_direction, plane_to_point) != 1:
            return False
        
        # Check against line end
        line_end_direction = line.direction * -1
        line_end_direction = line_end_direction.normalize()
        plane_at_end = Plane(line.end, line_end_direction)
        
        # Vector from end plane to point
        end_plane_to_point = Vector3D(
            point.x - plane_at_end.closest_point(point).x,
            point.y - plane_at_end.closest_point(point).y,
            point.z - plane_at_end.closest_point(point).z
        )
        end_plane_to_point = end_plane_to_point.normalize()
        
        # If point is on the end plane
        if end_plane_to_point.length() == 0:
            return True
        
        # Check if point is in same direction as reverse line direction
        if Vector3DAddOn.is_parallel_to(line_end_direction, end_plane_to_point) != 1:
            return False
        
        return True
    
    @staticmethod
    def project_onto_plane(point: Point3D, plane: Plane) -> Optional[Point3D]:
        """
        Project point onto plane
        Returns projected point or None if failed
        """
        if point is None or plane is None:
            return None
        
        return PlaneAddOn.project_point(plane, point)