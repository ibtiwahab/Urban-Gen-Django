# planning_api/geometry/brep_addon.py
from typing import List, Optional, Union
from .utils import Point3D, Plane, Polyline, Line
from .curve_addon import CurveAddOn
from .intersection_addon import IntersectionAddOn


class BrepLoop:
    """Simplified Brep loop representation"""
    def __init__(self, curves: List[Polyline], loop_type: str = "outer"):
        self.curves = curves
        self.loop_type = loop_type  # "outer", "inner", "unknown"
    
    def to_3d_curve(self) -> Optional[Polyline]:
        """Convert loop to 3D curve"""
        if not self.curves:
            return None
        
        # Join all curves into one polyline
        all_points = []
        for curve in self.curves:
            all_points.extend(curve.points[:-1])  # Exclude last point to avoid duplication
        
        if all_points:
            all_points.append(all_points[0])  # Close the loop
            return Polyline(all_points)
        
        return None


class BrepFace:
    """Simplified Brep face representation"""
    def __init__(self, outer_loop: BrepLoop, inner_loops: List[BrepLoop] = None):
        self.outer_loop = outer_loop
        self.inner_loops = inner_loops or []
        self.loops = [outer_loop] + self.inner_loops
    
    @property
    def is_valid(self) -> bool:
        """Check if face is valid"""
        return self.outer_loop is not None


class Brep:
    """Simplified Brep representation"""
    def __init__(self, faces: List[BrepFace]):
        self.faces = faces
    
    @property
    def is_valid(self) -> bool:
        """Check if Brep is valid"""
        return len(self.faces) > 0 and all(face.is_valid for face in self.faces)
    
    @staticmethod
    def create_trimmed_plane(plane: Plane, boundary_curve: Union[Polyline, List[Point3D]]) -> Optional['Brep']:
        """Create a trimmed planar Brep from boundary curve"""
        success, polyline = CurveAddOn.try_get_polyline(boundary_curve)
        if not success or polyline is None:
            return None
        
        # Create outer loop
        outer_loop = BrepLoop([polyline], "outer")
        
        # Create face
        face = BrepFace(outer_loop)
        
        return Brep([face])


class BrepAddOn:
    """Enhanced Brep operations similar to C# BrepAddOn"""
    
    @staticmethod
    def create_closed_curve_planar_brep(curve: Union[Polyline, List[Point3D]], 
                                       tolerance: float, approx: bool = True) -> Optional[Brep]:
        """Create planar Brep from closed curve"""
        if curve is None:
            raise ValueError("Curve is null")
        
        success, polyline = CurveAddOn.try_get_polyline(curve, approx)
        if not success or polyline is None:
            raise ValueError("Curve is not representable as a polyline")
        
        if not polyline.is_closed:
            raise ValueError("Curve is not closed")
        
        # Check if planar (simplified)
        from .utils import GeometryUtils
        plane = GeometryUtils.get_polyline_plane(polyline)
        if plane is None:
            raise ValueError("Curve is not planar")
        
        # Check for self-intersection
        if IntersectionAddOn.check_polyline_self(polyline, True):
            raise ValueError("Curve self-intersects")
        
        return Brep.create_trimmed_plane(plane, polyline)
    
    @staticmethod
    def get_area(brep: Brep, approx: bool = True) -> float:
        """Calculate total area of Brep"""
        if brep is None:
            raise ValueError("Brep is null")
        if not brep.is_valid:
            raise ValueError("Brep is not valid")
        
        total_area = 0.0
        
        for face in brep.faces:
            face_area = 0.0
            
            # Add outer loop area
            outer_curve = face.outer_loop.to_3d_curve()
            if outer_curve is not None:
                try:
                    face_area += CurveAddOn.get_area(outer_curve, approx)
                except ValueError:
                    # Skip if area calculation fails
                    continue
            
            # Subtract inner loop areas
            for inner_loop in face.inner_loops:
                inner_curve = inner_loop.to_3d_curve()
                if inner_curve is not None:
                    try:
                        face_area -= CurveAddOn.get_area(inner_curve, approx)
                    except ValueError:
                        # Skip if area calculation fails
                        continue
            
            total_area += face_area
        
        return total_area


class BrepFaceAddOn:
    """Enhanced BrepFace operations similar to C# BrepFaceAddOn"""
    
    @staticmethod
    def split_by_line_for_outer_loops(face: BrepFace, cutter: Line, tolerance: float, 
                                    approx: bool = True) -> List[Polyline]:
        """Split Brep face by line, returning split curves"""
        if face is None:
            raise ValueError("Face is null")
        if cutter is None:
            raise ValueError("Cutter is null")
        if not face.is_valid:
            raise ValueError("Face is invalid")
        
        result = []
        
        # Get face outer loop curve
        face_curve = face.outer_loop.to_3d_curve()
        if face_curve is None:
            return result
        
        if not face_curve.is_closed:
            raise ValueError("Face loop is not closed")
        
        success, face_polyline = CurveAddOn.try_get_polyline(face_curve, approx)
        if not success:
            raise ValueError("Face loop is not representable as a polyline")
        
        # Check for self-intersection
        if IntersectionAddOn.check_polyline_self(face_polyline, tolerance, True):
            raise ValueError("Face loop self intersects")
        
        # Get curve plane
        from .utils import GeometryUtils
        plane = GeometryUtils.get_polyline_plane(face_polyline)
        if plane is None:
            raise ValueError("Face loop is not planar")
        
        # Project cutter onto plane
        from .line_addon import LineAddOn
        success, projected_cutter = LineAddOn.project_onto_plane(cutter, plane)
        if not success or projected_cutter is None:
            raise ValueError("Cannot project cutter")
        
        if not projected_cutter.is_valid:
            result.append(face_curve)
            return result
        
        # Find intersections with face boundary
        face_points = face_polyline.points[:-1]  # Remove closing point
        intersections = []
        
        for i in range(len(face_points)):
            j = (i + 1) % len(face_points)
            boundary_line = Line(face_points[i], face_points[j])
            
            intersects, t0, t1 = IntersectionAddOn.line_line(boundary_line, projected_cutter, tolerance, True)
            
            if intersects:
                # Check if lines are not parallel
                from .vector3d_addon import Vector3DAddOn
                if Vector3DAddOn.is_parallel_to(boundary_line.direction, projected_cutter.direction) == 0:
                    intersection_point = boundary_line.point_at(t0)
                    intersections.append((j, intersection_point))
        
        if len(intersections) < 2:
            result.append(face_curve)
            return result
        
        if len(intersections) > 2:
            raise ValueError("Not able to handle more than 2 intersections yet")
        
        # Create two split curves
        for i in range(2):
            split_points = []
            intersect = intersections[i]
            next_intersect = intersections[(i + 1) % 2]
            
            split_points.append(intersect[1])  # Start with intersection point
            
            # Add intermediate points
            j = intersect[0]
            while j != next_intersect[0]:
                split_points.append(face_points[j])
                j = (j + 1) % len(face_points)
            
            split_points.append(next_intersect[1])  # End with next intersection point
            split_points.append(intersect[1])  # Close the curve
            
            result.append(Polyline(split_points))
        
        return result