# planning_api/geometry/polyline_addon.py
import math
from typing import List, Tuple, Optional
from .utils import Point3D, Vector3D, Line, Plane, Polyline, GeometryUtils
from .constants import Constants
from .plane_addon import PlaneAddOn
from .point3d_addon import Point3DAddOn
from .vector3d_addon import Vector3DAddOn
from .line_addon import LineAddOn


class PointContainment:
    """Point containment enumeration"""
    UNSET = 0
    INSIDE = 1
    OUTSIDE = 2
    COINCIDENT = 3


class CurveOffsetCornerStyle:
    """Curve offset corner style enumeration"""
    SHARP = 0
    ROUND = 1
    SMOOTH = 2


class PolylineAddOn:
    """Enhanced polyline operations similar to C# PolylineAddOn"""
    
    @staticmethod
    def make_closed(polyline: Polyline, tolerance: float) -> bool:
        """
        Make polyline closed if endpoints are close enough
        Modifies polyline in place
        """
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        
        if polyline.is_closed:
            return True
        
        if len(polyline.points) < 4:
            return False
        
        if polyline.points[0].distance_to(polyline.points[-1]) > tolerance:
            return False
        
        # Close the polyline
        polyline.points[-1] = polyline.points[0]
        return True
    
    @staticmethod
    def project_onto_plane(polyline: Polyline, target_plane: Plane) -> Optional[Polyline]:
        """
        Project polyline onto plane
        Returns projected polyline or None if failed
        """
        if polyline is None:
            raise ValueError("Polyline is null")
        if target_plane is None:
            raise ValueError("Plane is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        if not target_plane.is_valid:
            raise ValueError("Plane is not valid")
        
        output_points = []
        
        for vertex in polyline.points:
            projected_point = PlaneAddOn.project_point(target_plane, vertex)
            if projected_point is None:
                return None
            output_points.append(projected_point)
        
        return Polyline(output_points)
    
    @staticmethod
    def length_at_param(polyline: Polyline, parameter: float) -> float:
        """Calculate length at parameter along polyline"""
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        
        if parameter < 0.0 or parameter > (len(polyline.points) - 1):
            return float('nan')
        
        point_index = 0
        length = 0.0
        t = parameter
        
        while t >= 1:
            length += polyline.points[point_index].distance_to(polyline.points[point_index + 1])
            point_index += 1
            t -= 1
        
        if point_index == (len(polyline.points) - 1):
            length = polyline.length
        else:
            length += (polyline.points[point_index].distance_to(polyline.points[point_index + 1]) * t)
        
        return length
    
    @staticmethod
    def remove_repeating_points(polyline: Polyline) -> Polyline:
        """Remove consecutive duplicate points"""
        if polyline is None:
            raise ValueError("Polyline is null")
        
        if len(polyline.points) == 0:
            return Polyline([])
        
        result_points = [polyline.points[0]]
        
        for i in range(1, len(polyline.points)):
            if polyline.points[i].distance_to(polyline.points[i - 1]) > Constants.TOLERANCE:
                result_points.append(polyline.points[i])
        
        return Polyline(result_points)
    
    @staticmethod
    def remove_extra_points(polyline: Polyline) -> Polyline:
        """Remove collinear points and zero-length segments"""
        if polyline is None:
            raise ValueError("Polyline is null")
        
        points = polyline.points[:]
        ender = 0
        
        if polyline.is_closed:
            points.pop()  # Remove last point (duplicate of first)
            ender = 1
        
        if len(points) <= 2:
            return Polyline(points)
        
        start = True
        i = 1
        
        while len(points) > 2 and (start or i != ender):
            j = i - 1
            if j < 0:
                j = len(points) - 1
            
            start_point = points[j]
            mid_point = points[i]
            end_point = points[(i + 1) % len(points)]
            
            s_to_m = Vector3D(mid_point.x - start_point.x, mid_point.y - start_point.y, mid_point.z - start_point.z)
            s_to_e = Vector3D(end_point.x - start_point.x, end_point.y - start_point.y, end_point.z - start_point.z)
            
            removal = []
            
            if s_to_m.length() == 0:
                removal.append(i)
            if s_to_e.length() == 0:
                removal.append(j)
            
            if removal:
                for k in sorted(removal, reverse=True):
                    if k < len(points):
                        points.pop(k)
                i = i % len(points)
            elif Vector3DAddOn.is_parallel_to(s_to_m, s_to_e) != 0:
                points.pop(i)
                i = i % len(points)
            else:
                i = (i + 1) % len(points)
            
            start = False
        
        result = Polyline(points)
        
        if len(points) >= 3 and polyline.is_closed:
            result.points.append(points[0])  # Close the polyline
        
        return result
    
    @staticmethod
    def get_area(polyline: Polyline) -> float:
        """Calculate area of closed planar polyline"""
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        if not polyline.is_closed:
            raise ValueError("Polyline is not closed")
        
        return polyline.get_area()
    
    @staticmethod
    def contains(polyline: Polyline, point: Point3D, plane: Plane) -> int:
        """
        Test point containment in polyline
        Returns PointContainment value
        """
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        if not polyline.is_closed:
            return PointContainment.UNSET
        
        # Project polyline onto plane
        projected_polyline = PolylineAddOn.project_onto_plane(polyline, plane)
        if projected_polyline is None:
            return PointContainment.UNSET
        
        # Project point onto plane
        projected_point = Point3DAddOn.project_onto_plane(point, plane)
        if projected_point is None:
            return PointContainment.UNSET
        
        # Transform to XY plane for easier computation
        transform_to_xy = GeometryUtils.plane_to_plane_transform(plane, Plane.world_xy())
        
        # Apply transformation
        transformed_polyline = GeometryUtils.transform_polyline(projected_polyline, transform_to_xy)
        transformed_point = GeometryUtils.transform_point(projected_point, transform_to_xy)
        
        # Get bounding box
        bbox = transformed_polyline.get_bounding_box()
        max_point = Point3D(bbox[1].x + 1, bbox[1].y + 1, bbox[1].z)
        
        intersecting_line = Line(transformed_point, max_point)
        intersections = 0
        skip = False
        
        for i in range(len(transformed_polyline.points) - 1):
            if skip:
                skip = False
                continue
            
            start = transformed_polyline.points[i]
            end = transformed_polyline.points[i + 1]
            line = Line(start, end)
            
            # Import here to avoid circular import
            from .intersection_addon import IntersectionAddOn
            
            if IntersectionAddOn.line_line(line, intersecting_line, Constants.TOLERANCE, True)[0]:
                closest_point = line.closest_point(transformed_point, True)
                if closest_point.distance_to(transformed_point) <= Constants.TOLERANCE:
                    return PointContainment.COINCIDENT
                
                intersections += 1
                
                # Check if intersection is at vertex to avoid double counting
                line_to_point = Vector3D(
                    line.end.x - transformed_point.x,
                    line.end.y - transformed_point.y,
                    line.end.z - transformed_point.z
                )
                
                if Vector3DAddOn.is_parallel_to(line_to_point, intersecting_line.direction) == 1:
                    skip = True
        
        return PointContainment.INSIDE if intersections % 2 == 1 else PointContainment.OUTSIDE
    
    @staticmethod
    def cut_by_planes(polyline: Polyline, tolerance: float) -> List[Polyline]:
        """Cut polyline into planar segments"""
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        if not polyline.is_closed:
            raise ValueError("Polyline is not closed")
        
        # Import here to avoid circular import
        from .intersection_addon import IntersectionAddOn
        
        if IntersectionAddOn.check_polyline_self(polyline, True):
            raise ValueError("Polyline self-intersects")
        
        points = polyline.points[:-1]  # Remove closing point
        result = []
        
        while len(points) > 2:
            start = 0
            end = 2
            
            # Create plane from three points
            if len(points) < 3:
                break
            
            plane = Plane.from_three_points(points[start], points[1], points[end])
            if plane is None:
                # Points are collinear, try next point
                if end + 1 < len(points):
                    end += 1
                    continue
                else:
                    break
            
            # Find extent of planar region
            start = (start - 1) % len(points)
            while start != end and plane.distance_to_point(points[start]) <= tolerance:
                start = (start - 1) % len(points)
            
            if start != end:
                start = (start + 1) % len(points)
                end = (end + 1) % len(points)
                
                while start != end and plane.distance_to_point(points[end]) <= tolerance:
                    end = (end + 1) % len(points)
                
                end = (end - 1) % len(points)
            
            # Extract planar segment
            next_points = []
            i = start
            
            if start != end:
                while i != end:
                    next_points.append(points[i])
                    i = (i - 1) % len(points)
                next_points.append(points[end])
            
            # Create planar polyline
            i = start
            plane_polyline = []
            
            while i != end:
                plane_polyline.append(points[i])
                i = (i + 1) % len(points)
            plane_polyline.append(points[end])
            
            if len(plane_polyline) >= 3:
                result.append(Polyline(plane_polyline))
            
            points = next_points
        
        return result
    
    @staticmethod
    def cut_into_triangles(polyline: Polyline, tolerance: float) -> List[Polyline]:
        """Cut polyline into triangles using ear clipping"""
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        if not polyline.is_closed:
            raise ValueError("Polyline is not closed")
        
        # Import here to avoid circular import
        from .intersection_addon import IntersectionAddOn
        
        if IntersectionAddOn.check_polyline_self(polyline, True):
            raise ValueError("Polyline self-intersects")
        
        result = []
        polylines = PolylineAddOn.cut_by_planes(polyline, tolerance)
        
        for poly in polylines:
            points = poly.points[:-1]  # Remove closing point
            
            if len(points) < 3:
                continue
            
            i = 0
            
            while len(points) > 3:
                j = (i - 1) % len(points)
                start_point = points[j]
                mid_point = points[i]
                end_point = points[(i + 1) % len(points)]
                
                s_to_m = Vector3D(mid_point.x - start_point.x, mid_point.y - start_point.y, mid_point.z - start_point.z)
                s_to_e = Vector3D(end_point.x - start_point.x, end_point.y - start_point.y, end_point.z - start_point.z)
                
                # Check for degenerate triangle
                if (s_to_m.length() == 0 or s_to_e.length() == 0 or 
                    Vector3DAddOn.is_parallel_to(s_to_m, s_to_e) != 0):
                    points.pop(i)
                    i = i % len(points)
                    continue
                
                # Check if triangle is an "ear"
                check_point = Point3D(
                    (start_point.x + end_point.x) / 2,
                    (start_point.y + end_point.y) / 2,
                    (start_point.z + end_point.z) / 2
                )
                
                # Create current polyline for containment test
                current_poly = Polyline(points + [points[0]])
                triangle_plane = Plane.from_three_points(start_point, mid_point, end_point)
                
                if triangle_plane is not None:
                    contained = PolylineAddOn.contains(current_poly, check_point, triangle_plane)
                    
                    # Count intersections with triangle edge
                    edge_line = Line(end_point, start_point)
                    intersections = IntersectionAddOn.line_polyline(edge_line, current_poly)
                    
                    if len(intersections) <= 4 and (contained == PointContainment.INSIDE or contained == PointContainment.COINCIDENT):
                        # Valid ear - create triangle
                        triangle_points = [start_point, mid_point, end_point, start_point]
                        result.append(Polyline(triangle_points))
                        points.pop(i)
                        i = i % len(points)
                    else:
                        i = (i + 1) % len(points)
                else:
                    i = (i + 1) % len(points)
            
            # Add final triangle
            if len(points) == 3:
                final_triangle = Polyline(points + [points[0]])
                result.append(final_triangle)
        
        return result
    
    @staticmethod
    def offset(polyline: Polyline, direction_point: Point3D, normal: Vector3D, 
              distance: float, tolerance: float, corner_style: int) -> Optional[Polyline]:
        """
        Create offset polyline
        """
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        
        # Get polyline plane
        curve_plane = GeometryUtils.get_polyline_plane(polyline)
        if curve_plane is None:
            raise ValueError("Polyline is not planar")
        
        if Vector3DAddOn.is_parallel_to(normal, curve_plane.normal) == 0:
            raise ValueError("Polyline plane normal is not same as input normal")
        
        # Project direction point onto curve plane
        projected_point = Point3DAddOn.project_onto_plane(direction_point, curve_plane)
        if projected_point is None:
            return None
        
        # Find closest line segment
        closest_index = 0
        min_distance = float('inf')
        
        for i in range(len(polyline.points) - 1):
            line = Line(polyline.points[i], polyline.points[i + 1])
            closest_on_line = line.closest_point(projected_point, True)
            dist = closest_on_line.distance_to(projected_point)
            
            if dist < min_distance:
                min_distance = dist
                closest_index = i
        
        # Create offset lines
        offset_lines = []
        
        for i in range(len(polyline.points) - 1):
            line = Line(polyline.points[i], polyline.points[i + 1])
            offset_line = LineAddOn.offset(line, projected_point, distance, curve_plane)
            offset_lines.append(offset_line)
        
        # Connect offset lines at intersections
        if not offset_lines:
            return None
        
        # For closed polylines, connect all segments
        if polyline.is_closed and len(offset_lines) > 2:
            final_points = []
            
            for i in range(len(offset_lines)):
                current_line = offset_lines[i]
                next_line = offset_lines[(i + 1) % len(offset_lines)]
                
                # Import here to avoid circular import
                from .intersection_addon import IntersectionAddOn
                
                # Find intersection
                intersects, t0, t1 = IntersectionAddOn.line_line(current_line, next_line, tolerance, False)
                
                if intersects:
                    intersection_point = current_line.point_at(t0)
                    final_points.append(intersection_point)
                else:
                    # No intersection, use endpoints
                    final_points.append(current_line.start)
            
            if len(final_points) >= 3:
                final_points.append(final_points[0])  # Close the polyline
                return Polyline(final_points)
        
        # For open polylines or simple case
        result_points = []
        for line in offset_lines:
            if not result_points:
                result_points.append(line.start)
            result_points.append(line.end)
        
        return Polyline(result_points) if len(result_points) >= 2 else None