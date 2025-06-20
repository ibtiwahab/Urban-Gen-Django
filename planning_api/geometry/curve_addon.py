# planning_api/geometry/curve_addon.py
import math
from typing import List, Tuple, Optional, Union
from .utils import Point3D, Vector3D, Line, Plane, Polyline, GeometryUtils
from .constants import Constants
from .plane_addon import PlaneAddOn
from .point3d_addon import Point3DAddOn
from .vector3d_addon import Vector3DAddOn
from .line_addon import LineAddOn
from .polyline_addon import PolylineAddOn
from .intersection_addon import IntersectionAddOn


class PointContainment:
    """Point containment enumeration"""
    UNSET = 0
    INSIDE = 1
    OUTSIDE = 2
    COINCIDENT = 3


class RegionContainment:
    """Region containment enumeration"""
    DISJOINT = 0
    MUTUAL_INTERSECTION = 1
    A_INSIDE_B = 2
    B_INSIDE_A = 3


class CurveOffsetCornerStyle:
    """Curve offset corner style enumeration"""
    SHARP = 0
    ROUND = 1
    SMOOTH = 2


class CurveAddOn:
    """Enhanced curve operations similar to C# CurveAddOn"""
    
    @staticmethod
    def try_get_polyline(curve: Union[Polyline, List[Point3D]], approx: bool = True) -> Tuple[bool, Optional[Polyline]]:
        """
        Try to convert curve to polyline
        Args:
            curve: Input curve (can be Polyline or list of points)
            approx: Whether to allow approximation
        Returns:
            Tuple of (success, polyline)
        """
        if curve is None:
            raise ValueError("Curve is null")
        
        # If it's already a polyline, return it
        if isinstance(curve, Polyline):
            if curve.is_valid:
                return True, curve
            else:
                raise ValueError("Curve is not valid")
        
        # If it's a list of points, create polyline
        if isinstance(curve, list) and len(curve) > 0 and isinstance(curve[0], Point3D):
            polyline = Polyline(curve)
            return polyline.is_valid, polyline if polyline.is_valid else None
        
        # For approximation case, create subdivision
        if approx:
            # This would be implemented for NURBS curves in a full system
            # For now, return False as we don't have NURBS curve implementation
            return False, None
        
        return False, None
    
    @staticmethod
    def get_area(curve: Union[Polyline, List[Point3D]], approx: bool = True) -> float:
        """Calculate area of closed planar curve"""
        if curve is None:
            raise ValueError("Curve is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        if not polyline.is_closed:
            raise ValueError("Curve is not closed")
        
        # Check if planar (simplified check)
        if len(polyline.points) < 4:
            return 0.0
        
        return polyline.get_area()
    
    @staticmethod
    def get_length(curve: Union[Polyline, List[Point3D]], approx: bool = True) -> float:
        """Calculate length of curve"""
        if curve is None:
            raise ValueError("Curve is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        return polyline.length
    
    @staticmethod
    def get_centroid(curve: Union[Polyline, List[Point3D]], approx: bool = True) -> Point3D:
        """Calculate centroid of closed planar curve"""
        if curve is None:
            raise ValueError("Curve is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        if not polyline.is_closed:
            raise ValueError("Curve is not closed")
        
        # Check for self-intersection
        if IntersectionAddOn.check_polyline_self(polyline, True):
            raise ValueError("Curve self-intersects")
        
        # Use triangulation for complex polygons
        triangles = PolylineAddOn.cut_into_triangles(polyline, Constants.TOLERANCE)
        
        if not triangles:
            return polyline.get_centroid()
        
        weighted_centroid_sum = Point3D(0, 0, 0)
        area_sum = 0.0
        
        for triangle in triangles:
            centroid = triangle.get_centroid()
            area = PolylineAddOn.get_area(triangle)
            weighted_centroid_sum = weighted_centroid_sum + (centroid * area)
            area_sum += area
        
        if area_sum > 0:
            return weighted_centroid_sum / area_sum
        else:
            return polyline.get_centroid()
    
    @staticmethod
    def contains(curve: Union[Polyline, List[Point3D]], point: Point3D, plane: Plane, 
                tolerance: float, approx: bool = True) -> int:
        """
        Test point containment in curve
        Returns PointContainment value
        """
        if curve is None:
            raise ValueError("Curve is null")
        if point is None:
            raise ValueError("Point is null")
        if plane is None:
            raise ValueError("Plane is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
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
        
        # Transform polyline and point
        transformed_polyline = GeometryUtils.transform_polyline(projected_polyline, transform_to_xy)
        transformed_point = GeometryUtils.transform_point(projected_point, transform_to_xy)
        
        # Get bounding box and create test ray
        bbox = transformed_polyline.get_bounding_box()
        max_point = Point3D(bbox[1].x + tolerance * 3, bbox[1].y + tolerance * 3, bbox[1].z)
        
        if max_point.distance_to(transformed_point) <= tolerance:
            return PointContainment.OUTSIDE
        
        intersecting_line = Line(max_point, transformed_point)
        intersections = 0
        
        for i in range(len(transformed_polyline.points) - 1):
            start = transformed_polyline.points[i]
            end = transformed_polyline.points[i + 1]
            line = Line(start, end)
            
            if IntersectionAddOn.line_line(line, intersecting_line, tolerance, True)[0]:
                closest_point = line.closest_point(transformed_point, True)
                if closest_point.distance_to(transformed_point) <= tolerance:
                    return PointContainment.COINCIDENT
                
                intersections += 1
        
        return PointContainment.INSIDE if intersections % 2 == 1 else PointContainment.OUTSIDE
    
    @staticmethod
    def closest_point(curve: Union[Polyline, List[Point3D]], point: Point3D, 
                     maximum_distance: float = float('inf'), approx: bool = False) -> Tuple[bool, float]:
        """
        Find closest point parameter on curve
        Returns (success, parameter)
        """
        if curve is None:
            raise ValueError("Curve is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        closest_distance, closest_parameter = polyline.closest_parameter(point)
        
        if (closest_parameter < 0.0 or closest_parameter > (len(polyline.points) - 1) or
            closest_distance > maximum_distance):
            return False, 0.0
        
        # Convert polyline parameter to curve parameter
        point_index = 0
        length = 0.0
        t = closest_parameter
        
        while t >= 1:
            length += polyline.points[point_index].distance_to(polyline.points[point_index + 1])
            point_index += 1
            t -= 1
        
        if point_index == (len(polyline.points) - 1):
            # At end of curve
            curve_parameter = 1.0
        else:
            length += (polyline.points[point_index].distance_to(polyline.points[point_index + 1]) * t)
            curve_parameter = length / polyline.length
        
        return True, curve_parameter
    
    @staticmethod
    def coplanar_curves(curve_a: Union[Polyline, List[Point3D]], 
                       curve_b: Union[Polyline, List[Point3D]], tolerance: float) -> bool:
        """Check if two curves are coplanar"""
        if curve_a is None:
            raise ValueError("First curve is null")
        if curve_b is None:
            raise ValueError("Second curve is null")
        
        success_a, polyline_a = CurveAddOn.try_get_polyline(curve_a)
        success_b, polyline_b = CurveAddOn.try_get_polyline(curve_b)
        
        if not success_a or not success_b:
            raise ValueError("Curves are not representable as polylines")
        
        # Get planes for both curves
        plane_a = GeometryUtils.get_polyline_plane(polyline_a)
        plane_b = GeometryUtils.get_polyline_plane(polyline_b)
        
        if plane_a is None or plane_b is None:
            raise ValueError("Curves are not planar")
        
        # Check if normals are parallel
        if Vector3DAddOn.is_parallel_to(plane_a.normal, plane_b.normal) == 0:
            return False
        
        # Check if planes are coincident
        test_point = PlaneAddOn.project_point(plane_a, plane_b.origin)
        if test_point is None:
            return False
        
        distance = test_point.distance_to(plane_b.origin)
        return distance <= tolerance
    
    @staticmethod
    def make_closed(curve: Union[Polyline, List[Point3D]], tolerance: float, approx: bool = True) -> Tuple[bool, Optional[Polyline]]:
        """
        Make curve closed if endpoints are within tolerance
        Returns (success, modified_curve)
        """
        if curve is None:
            raise ValueError("Curve is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        if polyline.is_closed:
            return True, polyline
        
        if len(polyline.points) < 4:
            return False, None
        
        if polyline.points[0].distance_to(polyline.points[-1]) > tolerance:
            return False, None
        
        # Make closed by setting last point to first
        new_points = polyline.points[:]
        new_points[-1] = new_points[0]
        new_polyline = Polyline(new_points)
        
        return True, new_polyline
    
    @staticmethod
    def offset(curve: Union[Polyline, List[Point3D]], direction_point: Point3D, normal: Vector3D,
              distance: float, tolerance: float, corner_style: int, approx: bool = True) -> List[Polyline]:
        """
        Create offset curve
        Returns list of offset curves
        """
        if curve is None:
            raise ValueError("Curve is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        # Get curve plane
        curve_plane = GeometryUtils.get_polyline_plane(polyline)
        if curve_plane is None:
            raise ValueError("Curve is not planar")
        
        # Check if normals are parallel
        if Vector3DAddOn.is_parallel_to(normal, curve_plane.normal) == 0:
            raise ValueError("Curve plane normal is not same as input normal")
        
        # Use polyline offset
        offset_polyline = PolylineAddOn.offset(polyline, direction_point, normal, distance, tolerance, corner_style)
        
        if offset_polyline is not None:
            return [offset_polyline]
        else:
            return []
    
    @staticmethod
    def planar_closed_curve_relationship(curve_a: Union[Polyline, List[Point3D]], 
                                       curve_b: Union[Polyline, List[Point3D]], 
                                       plane: Plane, tolerance: float, approx: bool = True) -> int:
        """
        Determine relationship between two planar closed curves
        Returns RegionContainment value
        """
        if curve_a is None:
            raise ValueError("First curve is null")
        if curve_b is None:
            raise ValueError("Second curve is null")
        
        success_a, polyline_a = CurveAddOn.try_get_polyline(curve_a, approx)
        success_b, polyline_b = CurveAddOn.try_get_polyline(curve_b, approx)
        
        if not success_a or not success_b:
            raise ValueError("Curves are not representable as polylines")
        
        # Check for intersections
        if IntersectionAddOn.check_curve_curve(polyline_a, polyline_b, tolerance, approx):
            return RegionContainment.MUTUAL_INTERSECTION
        
        # Check containment
        if len(polyline_b.points) > 0:
            b_in_a = CurveAddOn.contains(polyline_a, polyline_b.points[0], plane, tolerance, approx)
            if polyline_a.is_closed and b_in_a == PointContainment.INSIDE:
                return RegionContainment.B_INSIDE_A
        
        if len(polyline_a.points) > 0:
            a_in_b = CurveAddOn.contains(polyline_b, polyline_a.points[0], plane, tolerance, approx)
            if polyline_b.is_closed and a_in_b == PointContainment.INSIDE:
                return RegionContainment.A_INSIDE_B
        
        return RegionContainment.DISJOINT
    
    @staticmethod
    def point_at_normalized_length(curve: Union[Polyline, List[Point3D]], length: float, approx: bool = True) -> Point3D:
        """
        Get point at normalized length parameter (0-1)
        """
        if curve is None:
            raise ValueError("Curve is null")
        
        if length < 0 or length > 1:
            raise ValueError("Length parameter must be between 0 and 1")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        return polyline.point_at_parameter(length)