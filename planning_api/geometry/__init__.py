# planning_api/geometry/__init__.py
"""
Geometry processing package for urban planning applications.
Provides 3D geometry operations similar to Rhino3D and CAD systems.
Enhanced with AddOn modules for advanced operations.
"""

from .utils import (
    Point3D,
    Vector3D,
    Line,
    Plane,
    Polyline,
    GeometryUtils
)

from .advanced import (
    CurveOperations,
    OffsetOperations,
    BuildingPlacement,
    TriangulationOperations,
    BooleanOperations,
    IntersectionOperations,
    SurfaceOperations,
    ParametricDesign
)

# Enhanced AddOn modules
from .constants import Constants
from .curve_addon import CurveAddOn, PointContainment, RegionContainment, CurveOffsetCornerStyle
from .line_addon import LineAddOn, Interval
from .plane_addon import PlaneAddOn
from .point3d_addon import Point3DAddOn
from .polyline_addon import PolylineAddOn
from .vector3d_addon import Vector3DAddOn
from .intersection_addon import IntersectionAddOn, IntersectionEventAddOn
from .brep_addon import BrepAddOn, BrepFaceAddOn, Brep, BrepFace, BrepLoop

__all__ = [
    # Basic geometry types
    'Point3D',
    'Vector3D', 
    'Line',
    'Plane',
    'Polyline',
    'GeometryUtils',
    
    # Advanced operations
    'CurveOperations',
    'OffsetOperations',
    'BuildingPlacement',
    'TriangulationOperations',
    'BooleanOperations',
    'IntersectionOperations',
    'SurfaceOperations',
    'ParametricDesign',
    
    # Constants and enums
    'Constants',
    'PointContainment',
    'RegionContainment', 
    'CurveOffsetCornerStyle',
    'Interval',
    
    # AddOn modules
    'CurveAddOn',
    'LineAddOn',
    'PlaneAddOn',
    'Point3DAddOn',
    'PolylineAddOn',
    'Vector3DAddOn',
    'IntersectionAddOn',
    'IntersectionEventAddOn',
    'BrepAddOn',
    'BrepFaceAddOn',
    'Brep',
    'BrepFace',
    'BrepLoop'
]