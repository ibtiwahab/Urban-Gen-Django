# planning_api/urls.py - Fixed URLs with correct imports and mappings
from django.urls import path
from .views import GeneratePlanView, GeometryAnalysisView
from .additional_views import (
    GeometryValidationView,
    PolygonOffsetView,
    IntersectionTestView,
    GeometryInfoView
)

urlpatterns = [
    # Main planning endpoints
    path('planning/main/generateplan/', GeneratePlanView.as_view(), name='generate_plan'),
    
    # Geometry analysis endpoints
    path('planning/geometry/analyze/', GeometryAnalysisView.as_view(), name='geometry_analysis'),
    path('planning/geometry/validate/', GeometryValidationView.as_view(), name='geometry_validation'),
    path('planning/geometry/offset/', PolygonOffsetView.as_view(), name='polygon_offset'),
    path('planning/geometry/intersection/', IntersectionTestView.as_view(), name='intersection_test'),
    path('planning/geometry/info/', GeometryInfoView.as_view(), name='geometry_info'),
    
    # Additional potential endpoints (uncomment when implemented)
    # path('planning/geometry/boolean/', BooleanOperationView.as_view(), name='boolean_operation'),
    # path('planning/geometry/triangulate/', TriangulationView.as_view(), name='triangulation'),
    # path('planning/geometry/curve/', CurveAnalysisView.as_view(), name='curve_analysis'),
    # path('planning/geometry/line/', LineOperationView.as_view(), name='line_operation'),
]