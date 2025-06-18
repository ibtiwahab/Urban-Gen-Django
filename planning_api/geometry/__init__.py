# planning_api/geometry/__init__.py
"""
Geometry processing package for urban planning applications.
Provides 3D geometry operations similar to Rhino3D and CAD systems.
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
    'ParametricDesign'
]