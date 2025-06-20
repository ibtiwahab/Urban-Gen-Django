# planning_api/geometry/plane_addon.py
from typing import Optional
from .utils import Point3D, Vector3D, Line, Plane


class PlaneAddOn:
    """Enhanced plane operations similar to C# PlaneAddOn"""
    
    @staticmethod
    def project_point(plane: Plane, point: Point3D) -> Optional[Point3D]:
        """
        Project point onto plane
        Returns projected point or None if failed
        """
        if plane is None:
            raise ValueError("Plane is null")
        if point is None:
            raise ValueError("Point is null")
        if not plane.is_valid:
            raise ValueError("Plane is not valid")
        
        try:
            # Create line from point in direction of plane normal
            perpendicular_line = Line(point, Point3D(
                point.x + plane.normal.x,
                point.y + plane.normal.y,
                point.z + plane.normal.z
            ))
            
            # Find intersection with plane
            intersection_point = PlaneAddOn.line_plane_intersection(perpendicular_line, plane)
            return intersection_point
            
        except Exception:
            return None
    
    @staticmethod
    def line_plane_intersection(line: Line, plane: Plane) -> Optional[Point3D]:
        """
        Find intersection between line and plane
        Returns intersection point or None if no intersection
        """
        if line is None or plane is None:
            return None
        
        # Get line direction and a point on the line
        line_direction = line.direction
        line_point = line.start
        
        # Get plane normal and a point on the plane
        plane_normal = plane.normal
        plane_point = plane.origin
        
        # Calculate denominator
        denominator = plane_normal.dot(line_direction)
        
        # Check if line is parallel to plane
        if abs(denominator) < 1e-10:
            return None
        
        # Calculate parameter t
        to_plane_point = Vector3D(
            plane_point.x - line_point.x,
            plane_point.y - line_point.y,
            plane_point.z - line_point.z
        )
        
        t = plane_normal.dot(to_plane_point) / denominator
        
        # Calculate intersection point
        intersection = Point3D(
            line_point.x + t * line_direction.x,
            line_point.y + t * line_direction.y,
            line_point.z + t * line_direction.z
        )
        
        return intersection