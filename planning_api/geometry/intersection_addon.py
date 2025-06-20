# planning_api/geometry/intersection_addon.py
import math
from typing import List, Tuple, Optional, Union
from .utils import Point3D, Vector3D, Line, Plane, Polyline
from .constants import Constants
from .line_addon import Interval
from .vector3d_addon import Vector3DAddOn


class IntersectionEventAddOn:
    """Intersection event data structure"""
    
    def __init__(self):
        self.type = 0  # 1 = point, 2 = overlap
        self.point_a = Point3D(0, 0, 0)
        self.point_a2 = Point3D(0, 0, 0)
        self.point_b = Point3D(0, 0, 0)
        self.point_b2 = Point3D(0, 0, 0)
        self.overlap_a = Interval(0, 0)
        self.overlap_b = Interval(0, 0)
    
    @property
    def is_point(self) -> bool:
        """Check if intersection is a point"""
        return self.type == 1 or self.type == 3
    
    @property
    def is_overlap(self) -> bool:
        """Check if intersection is an overlap"""
        return not self.is_point


class IntersectionAddOn:
    """Enhanced intersection operations similar to C# IntersectionAddOn"""
    
    @staticmethod
    def line_line(line_a: Line, line_b: Line, tolerance: float = Constants.TOLERANCE, 
                 finite_segments: bool = False) -> Tuple[bool, float, float]:
        """
        Find intersection between two lines
        Returns (intersects, parameter_a, parameter_b)
        """
        if line_a is None:
            raise ValueError("First line is null")
        if line_b is None:
            raise ValueError("Second line is null")
        if not line_a.is_valid:
            raise ValueError("First line is not valid")
        if not line_b.is_valid:
            raise ValueError("Second line is not valid")
        
        # Calculate closest points between lines
        l1 = line_b.closest_point(line_a.start, True).distance_to(line_a.start)
        l2 = line_b.closest_point(line_a.end, True).distance_to(line_a.end)
        l3 = line_a.closest_point(line_b.start, True).distance_to(line_b.start)
        l4 = line_a.closest_point(line_b.end, True).distance_to(line_b.end)
        
        # Try to find exact intersection
        success, a, b = IntersectionAddOn._line_line_intersection(line_a, line_b)
        
        if not success:
            # Lines are parallel or skew, find closest approach
            min_distance = min(l1, l2, l3, l4)
            
            if min_distance <= tolerance:
                if l1 == min_distance:
                    a = 0
                    b = line_b.closest_parameter(line_a.start)
                elif l3 == min_distance:
                    a = line_a.closest_parameter(line_b.start)
                    b = 0
                elif l2 == min_distance:
                    a = 1
                    b = line_b.closest_parameter(line_a.end)
                else:
                    a = line_a.closest_parameter(line_b.end)
                    b = 1
                
                # Clamp parameters if needed
                if finite_segments:
                    a = max(0, min(1, a))
                    b = max(0, min(1, b))
                
                return True, a, b
            
            return False, 0, 0
        
        # Check if intersection is within segment bounds
        if finite_segments:
            if a < 0 or a > 1 or b < 0 or b > 1:
                return False, a, b
            
            # Verify distance is within tolerance
            point_a = line_a.point_at(a)
            point_b = line_b.point_at(b)
            if point_a.distance_to(point_b) > tolerance:
                return False, a, b
        
        return True, a, b
    
    @staticmethod
    def _line_line_intersection(line_a: Line, line_b: Line) -> Tuple[bool, float, float]:
        """
        Calculate exact line-line intersection using vector math
        Returns (success, parameter_a, parameter_b)
        """
        # Vector from line_a start to line_b start
        w = Vector3D(
            line_a.start.x - line_b.start.x,
            line_a.start.y - line_b.start.y,
            line_a.start.z - line_b.start.z
        )
        
        u = line_a.direction
        v = line_b.direction
        
        # Calculate determinants
        a = u.dot(u)
        b = u.dot(v)
        c = v.dot(v)
        d = u.dot(w)
        e = v.dot(w)
        
        denominator = a * c - b * b
        
        # Check if lines are parallel
        if abs(denominator) < Constants.TOLERANCE:
            return False, 0, 0
        
        # Calculate parameters
        sc = (b * e - c * d) / denominator
        tc = (a * e - b * d) / denominator
        
        return True, sc, tc
    
    @staticmethod
    def line_polyline(line: Line, polyline: Polyline) -> List[Tuple[float, float]]:
        """
        Find all intersections between line and polyline
        Returns list of (line_parameter, polyline_parameter) tuples
        """
        if line is None:
            raise ValueError("Line is null")
        if polyline is None:
            raise ValueError("Polyline is null")
        if not line.is_valid:
            raise ValueError("Line is not valid")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        
        result = []
        
        for i in range(len(polyline.points) - 1):
            polyline_line = Line(polyline.points[i], polyline.points[i + 1])
            intersects, t0, t1 = IntersectionAddOn.line_line(line, polyline_line, Constants.TOLERANCE, True)
            
            if intersects:
                result.append((t0, t1))
        
        return result
    
    @staticmethod
    def check_polyline_self(polyline: Polyline, finite_segments: bool = True) -> bool:
        """Check if polyline self-intersects"""
        if polyline is None:
            raise ValueError("Polyline is null")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        
        lines = []
        
        for i in range(len(polyline.points) - 1):
            lines.append(Line(polyline.points[i], polyline.points[i + 1]))
        
        for i in range(len(lines)):
            k = i - 1
            if k < 0:
                k = len(lines) - 1
            
            for j in range((i + 2) % len(lines), k, 1):
                if j >= len(lines):
                    j = j % len(lines)
                if j == k:
                    break
                
                intersects, _, _ = IntersectionAddOn.line_line(lines[i], lines[j], Constants.TOLERANCE, finite_segments)
                
                if intersects:
                    return True
        
        return False
    
    @staticmethod
    def check_curve_curve(curve_a: Union[Polyline, List[Point3D]], 
                         curve_b: Union[Polyline, List[Point3D]], 
                         tolerance: float, approx: bool = True) -> bool:
        """Check if two curves intersect"""
        if curve_a is None:
            raise ValueError("First curve is null")
        if curve_b is None:
            raise ValueError("Second curve is null")
        
        # Convert to polylines if needed
        from .curve_addon import CurveAddOn
        
        success_a, polyline_a = CurveAddOn.try_get_polyline(curve_a, approx)
        success_b, polyline_b = CurveAddOn.try_get_polyline(curve_b, approx)
        
        if not success_a or not success_b:
            raise ValueError("Curves are not representable as polylines")
        
        # Handle point curves
        if len(polyline_a.points) == 1 and len(polyline_b.points) == 1:
            return polyline_a.points[0].distance_to(polyline_b.points[0]) <= tolerance
        
        if len(polyline_a.points) == 1:
            for i in range(len(polyline_b.points) - 1):
                line_b = Line(polyline_b.points[i], polyline_b.points[i + 1])
                closest = line_b.closest_point(polyline_a.points[0], True)
                if closest.distance_to(polyline_a.points[0]) <= tolerance:
                    return True
            return False
        
        if len(polyline_b.points) == 1:
            for i in range(len(polyline_a.points) - 1):
                line_a = Line(polyline_a.points[i], polyline_a.points[i + 1])
                closest = line_a.closest_point(polyline_b.points[0], True)
                if closest.distance_to(polyline_b.points[0]) <= tolerance:
                    return True
            return False
        
        # Check line-line intersections
        for i in range(len(polyline_a.points) - 1):
            line_a = Line(polyline_a.points[i], polyline_a.points[i + 1])
            
            for j in range(len(polyline_b.points) - 1):
                line_b = Line(polyline_b.points[j], polyline_b.points[j + 1])
                intersects, _, _ = IntersectionAddOn.line_line(line_a, line_b, tolerance, True)
                
                if intersects:
                    return True
        
        return False
    
    @staticmethod
    def line_overlap(line: Line, overlap_line: Line, tolerance: float) -> Optional[Interval]:
        """Find overlap interval between two lines"""
        if line is None:
            raise ValueError("Line is null")
        if overlap_line is None:
            raise ValueError("Overlap line is null")
        if not line.is_valid:
            raise ValueError("Line is not valid")
        if not overlap_line.is_valid:
            raise ValueError("Overlap line is not valid")
        
        # Check if lines intersect/overlap
        intersects, _, _ = IntersectionAddOn.line_line(line, overlap_line, tolerance, True)
        if not intersects:
            return None
        
        # Find which endpoints of line are on overlap_line
        from_on_overlap = overlap_line.closest_point(line.start, True).distance_to(line.start) <= tolerance
        to_on_overlap = overlap_line.closest_point(line.end, True).distance_to(line.end) <= tolerance
        
        if from_on_overlap and to_on_overlap:
            # Entire line overlaps
            return Interval(0, 1)
        elif from_on_overlap:
            # Line start overlaps, find other end
            param = IntersectionAddOn._find_overlap_parameter(line, overlap_line, tolerance, True)
            return Interval(0, param) if param is not None else None
        elif to_on_overlap:
            # Line end overlaps, find other end
            param = IntersectionAddOn._find_overlap_parameter(line, overlap_line, tolerance, False)
            return Interval(param, 1) if param is not None else None
        else:
            # Find overlap region within line
            param1 = IntersectionAddOn._find_overlap_parameter(line, overlap_line, tolerance, True)
            param2 = IntersectionAddOn._find_overlap_parameter(line, overlap_line, tolerance, False)
            
            if param1 is not None and param2 is not None:
                return Interval(min(param1, param2), max(param1, param2))
        
        return None
    
    @staticmethod
    def _find_overlap_parameter(line: Line, overlap_line: Line, tolerance: float, from_start: bool) -> Optional[float]:
        """Helper method to find overlap parameter"""
        # Simplified implementation - in practice this would use sphere and cylinder intersections
        # as in the original C# code
        
        # Check intersections with overlap line endpoints
        start_sphere_center = overlap_line.start
        end_sphere_center = overlap_line.end
        
        # Find closest points
        if from_start:
            test_point = start_sphere_center
        else:
            test_point = end_sphere_center
        
        closest_on_line = line.closest_point(test_point, False)
        if closest_on_line.distance_to(test_point) <= tolerance:
            return line.closest_parameter(closest_on_line)
        
        return None
    
    @staticmethod
    def line_line_overlap(line_a: Line, line_b: Line, tolerance: float) -> Optional[IntersectionEventAddOn]:
        """Find overlap between two lines"""
        if line_a is None:
            raise ValueError("First line is null")
        if line_b is None:
            raise ValueError("Second line is null")
        if not line_a.is_valid:
            raise ValueError("First line is not valid")
        if not line_b.is_valid:
            raise ValueError("Second line is not valid")
        
        # Check if lines intersect
        intersects, _, _ = IntersectionAddOn.line_line(line_a, line_b, tolerance, True)
        if not intersects:
            return None
        
        # Find overlap intervals
        overlap_a = IntersectionAddOn.line_overlap(line_a, line_b, tolerance)
        overlap_b = IntersectionAddOn.line_overlap(line_b, line_a, tolerance)
        
        if overlap_a is None or overlap_b is None:
            return None
        
        # Create intersection event
        overlap = IntersectionEventAddOn()
        overlap.type = 2  # Overlap
        overlap.overlap_a = overlap_a
        overlap.point_a = line_a.point_at(overlap_a.t0)
        overlap.point_a2 = line_a.point_at(overlap_a.t1)
        overlap.overlap_b = overlap_b
        overlap.point_b = line_b.point_at(overlap_b.t0)
        overlap.point_b2 = line_b.point_at(overlap_b.t1)
        
        return overlap
    
    @staticmethod
    def line_polyline_overlaps(line: Line, polyline: Polyline, tolerance: float) -> List[IntersectionEventAddOn]:
        """Find all overlaps between line and polyline"""
        if line is None:
            raise ValueError("Line is null")
        if polyline is None:
            raise ValueError("Polyline is null")
        if not line.is_valid:
            raise ValueError("Line is not valid")
        if not polyline.is_valid:
            raise ValueError("Polyline is not valid")
        
        overlaps = []
        
        for i in range(len(polyline.points) - 1):
            polyline_line = Line(polyline.points[i], polyline.points[i + 1])
            overlap = IntersectionAddOn.line_line_overlap(line, polyline_line, tolerance)
            
            if overlap is not None:
                # Adjust polyline parameter to global polyline coordinate
                overlap.overlap_b = Interval(
                    i + overlap.overlap_b.t0,
                    i + overlap.overlap_b.t1
                )
                overlaps.append(overlap)
        
        return overlaps
    
    @staticmethod
    def curve_curve(curve_a: Union[Polyline, List[Point3D]], 
                   curve_b: Union[Polyline, List[Point3D]], 
                   tolerance: float, overlap_tolerance: float, approx: bool = False) -> List[IntersectionEventAddOn]:
        """Find all intersections between two curves"""
        if curve_a is None:
            raise ValueError("First curve is null")
        if curve_b is None:
            raise ValueError("Second curve is null")
        
        # Convert to polylines
        from .curve_addon import CurveAddOn
        
        success_a, polyline_a = CurveAddOn.try_get_polyline(curve_a, approx)
        success_b, polyline_b = CurveAddOn.try_get_polyline(curve_b, approx)
        
        if not success_a or not success_b:
            raise ValueError("Curves are not representable as polylines")
        
        intersections = []
        
        for i in range(len(polyline_a.points) - 1):
            line = Line(polyline_a.points[i], polyline_a.points[i + 1])
            overlaps = IntersectionAddOn.line_polyline_overlaps(line, polyline_b, tolerance)
            
            for overlap in overlaps:
                # Adjust curve A parameter
                overlap.overlap_a = Interval(
                    i + overlap.overlap_a.t0,
                    i + overlap.overlap_a.t1
                )
                intersections.append(overlap)
        
        # Combine overlaps if needed (simplified version)
        final_intersections = []
        
        for intersection in intersections:
            # Convert polyline parameters to curve parameters
            if polyline_a.length > 0:
                from .polyline_addon import PolylineAddOn
                
                length_at_param1 = PolylineAddOn.length_at_param(polyline_a, intersection.overlap_a.t0)
                length_at_param2 = PolylineAddOn.length_at_param(polyline_a, intersection.overlap_a.t1)
                
                if not (math.isnan(length_at_param1) or math.isnan(length_at_param2)):
                    # Check if it's a point intersection
                    if abs(length_at_param2 - length_at_param1) <= overlap_tolerance:
                        intersection.type = 1  # Point
                    
                    # Convert to normalized curve parameters (0-1)
                    intersection.overlap_a = Interval(
                        length_at_param1 / polyline_a.length,
                        length_at_param2 / polyline_a.length
                    )
                    
                    # Update points
                    intersection.point_a = polyline_a.point_at_parameter(intersection.overlap_a.t0)
                    intersection.point_a2 = polyline_a.point_at_parameter(intersection.overlap_a.t1)
                    
                    # Similar for curve B
                    length_at_param1_b = PolylineAddOn.length_at_param(polyline_b, intersection.overlap_b.t0)
                    length_at_param2_b = PolylineAddOn.length_at_param(polyline_b, intersection.overlap_b.t1)
                    
                    if not (math.isnan(length_at_param1_b) or math.isnan(length_at_param2_b)):
                        intersection.overlap_b = Interval(
                            length_at_param1_b / polyline_b.length,
                            length_at_param2_b / polyline_b.length
                        )
                        
                        intersection.point_b = polyline_b.point_at_parameter(intersection.overlap_b.t0)
                        intersection.point_b2 = polyline_b.point_at_parameter(intersection.overlap_b.t1)
                        
                        if intersection.is_point:
                            intersection.point_a2 = intersection.point_a
                            intersection.point_b2 = intersection.point_b
                            intersection.overlap_a = Interval(intersection.overlap_a.t0, intersection.overlap_a.t0)
                            intersection.overlap_b = Interval(intersection.overlap_b.t0, intersection.overlap_b.t0)
                        
                        final_intersections.append(intersection)
        
        return final_intersections