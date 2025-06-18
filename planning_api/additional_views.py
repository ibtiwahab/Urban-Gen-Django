# planning_api/additional_views.py - Additional geometry endpoints
import logging
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .geometry import (
    Point3D, Polyline, GeometryUtils, CurveOperations, 
    OffsetOperations, IntersectionOperations
)
from .serializers import (
    GeometryValidationSerializer, GeometryValidationResponseSerializer,
    OffsetOperationSerializer, OffsetOperationResponseSerializer,
    IntersectionTestSerializer, IntersectionTestResponseSerializer
)

logger = logging.getLogger(__name__)


class GeometryValidationView(APIView):
    """Validate polygon geometry"""
    
    def post(self, request):
        try:
            serializer = GeometryValidationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            vertices = data['vertices']
            tolerance = data.get('tolerance', 1e-6)
            
            # Convert to polyline
            polyline_data = []
            for i in range(0, len(vertices), 3):
                if i + 2 < len(vertices):
                    polyline_data.append({
                        'x': vertices[i],
                        'y': vertices[i + 1], 
                        'z': vertices[i + 2]
                    })
            
            if len(polyline_data) < 3:
                return Response({
                    'is_valid': False,
                    'errors': ['Insufficient vertices for polygon (minimum 3 required)']
                })
            
            # Create polyline
            points = [Point3D(p['x'], p['y'], p['z']) for p in polyline_data]
            polyline = Polyline(points)
            
            # Perform validations
            errors = []
            warnings = []
            
            # Check if closed
            is_closed = polyline.make_closed(tolerance)
            if not is_closed and data.get('check_closure', True):
                warnings.append('Polygon is not closed')
            
            # Check self-intersection
            self_intersects = False
            if data.get('check_self_intersection', True):
                self_intersects = IntersectionOperations.polyline_self_intersection_check(
                    polyline, tolerance
                )
                if self_intersects:
                    errors.append('Polygon self-intersects')
            
            # Check planarity
            is_planar = True
            if data.get('check_planarity', True):
                plane = CurveOperations.get_curve_plane(polyline)
                is_planar = plane is not None
                if not is_planar:
                    warnings.append('Polygon is not planar')
            
            # Calculate metrics
            polygon_area = polyline.get_area() if is_closed else 0.0
            polygon_perimeter = polyline.length
            
            response_data = {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'polygon_area': polygon_area,
                'polygon_perimeter': polygon_perimeter,
                'is_closed': is_closed,
                'is_planar': is_planar,
                'self_intersects': self_intersects
            }
            
            response_serializer = GeometryValidationResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data)
            else:
                logger.error(f"Response serialization failed: {response_serializer.errors}")
                return Response(response_data)  # Return raw data as fallback
            
        except Exception as e:
            logger.error(f"Error in geometry validation: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Validation error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PolygonOffsetView(APIView):
    """Create offset polygons"""
    
    def post(self, request):
        try:
            serializer = OffsetOperationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            vertices = data['vertices']
            offset_distance = data['offset_distance']
            offset_type = data.get('offset_type', 'inward')
            tolerance = data.get('tolerance', 1e-6)
            
            # Convert to polyline
            polyline_data = []
            for i in range(0, len(vertices), 3):
                if i + 2 < len(vertices):
                    polyline_data.append({
                        'x': vertices[i],
                        'y': vertices[i + 1],
                        'z': vertices[i + 2]
                    })
            
            if len(polyline_data) < 3:
                return Response({
                    'success': False,
                    'error_message': 'Insufficient vertices for polygon'
                })
            
            # Create polyline
            points = [Point3D(p['x'], p['y'], p['z']) for p in polyline_data]
            polyline = Polyline(points)
            
            # Ensure closed
            if not polyline.make_closed(tolerance):
                return Response({
                    'success': False,
                    'error_message': 'Cannot close polygon within tolerance'
                })
            
            # Apply offset distance direction
            actual_distance = offset_distance if offset_type == 'inward' else -offset_distance
            
            # Perform offset
            offset_polyline = OffsetOperations.offset_polygon(polyline, actual_distance, tolerance)
            
            if offset_polyline and len(offset_polyline.points) >= 3:
                # Convert back to flat array
                offset_vertices = []
                for point in offset_polyline.points:
                    offset_vertices.extend([point.x, point.y, point.z])
                
                response_data = {
                    'success': True,
                    'offset_vertices': offset_vertices
                }
            else:
                # Try alternative method
                inset_points = GeometryUtils.create_inset_polygon(points, actual_distance)
                if inset_points and len(inset_points) >= 3:
                    offset_vertices = []
                    for point in inset_points:
                        offset_vertices.extend([point.x, point.y, point.z])
                    
                    response_data = {
                        'success': True,
                        'offset_vertices': offset_vertices
                    }
                else:
                    response_data = {
                        'success': False,
                        'error_message': 'Unable to create valid offset polygon'
                    }
            
            response_serializer = OffsetOperationResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data)
            else:
                return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in polygon offset: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error_message': f'Offset error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IntersectionTestView(APIView):
    """Test polygon intersections"""
    
    def post(self, request):
        try:
            serializer = IntersectionTestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            vertices_a = data['polygon_a_vertices']
            vertices_b = data['polygon_b_vertices']
            tolerance = data.get('tolerance', 1e-6)
            
            # Convert to polylines
            def vertices_to_points(vertices):
                points = []
                for i in range(0, len(vertices), 3):
                    if i + 2 < len(vertices):
                        points.append(Point3D(vertices[i], vertices[i + 1], vertices[i + 2]))
                return points
            
            points_a = vertices_to_points(vertices_a)
            points_b = vertices_to_points(vertices_b)
            
            if len(points_a) < 3 or len(points_b) < 3:
                return Response({
                    'intersects': False,
                    'intersection_type': 'invalid'
                })
            
            # Basic intersection tests
            intersects = False
            intersection_type = 'separate'
            intersection_points = []
            
            # Check if any vertices of A are inside B
            a_points_in_b = sum(1 for p in points_a if GeometryUtils.point_in_polygon_2d(p, points_b))
            b_points_in_a = sum(1 for p in points_b if GeometryUtils.point_in_polygon_2d(p, points_a))
            
            if a_points_in_b > 0 or b_points_in_a > 0:
                intersects = True
                if a_points_in_b == len(points_a):
                    intersection_type = 'a_inside_b'
                elif b_points_in_a == len(points_b):
                    intersection_type = 'b_inside_a'
                else:
                    intersection_type = 'overlap'
            
            # Check edge intersections
            if not intersects:
                polyline_a = Polyline(points_a)
                polyline_b = Polyline(points_b)
                
                for i in range(len(points_a) - 1):
                    line_a = Line(points_a[i], points_a[i + 1])
                    
                    intersections = IntersectionOperations.line_polyline_intersections(
                        line_a, polyline_b, tolerance
                    )
                    
                    if intersections:
                        intersects = True
                        intersection_type = 'edge_intersection'
                        for point, _, _ in intersections:
                            intersection_points.append([point.x, point.y, point.z])
            
            response_data = {
                'intersects': intersects,
                'intersection_type': intersection_type,
                'intersection_points': intersection_points
            }
            
            response_serializer = IntersectionTestResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data)
            else:
                return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in intersection test: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Intersection test error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GeometryInfoView(APIView):
    """Get information about geometry capabilities"""
    
    def get(self, request):
        return Response({
            'geometry_engine': 'Custom Python Geometry Engine',
            'version': '1.0.0',
            'capabilities': [
                'Polygon validation',
                'Self-intersection detection',
                'Point-in-polygon testing',
                'Polygon offsetting',
                'Basic intersection testing',
                'Area and perimeter calculation',
                'Building placement algorithms',
                'Parametric urban design'
            ],
            'supported_operations': [
                'generateplan',
                'validate_geometry',
                'offset_polygon', 
                'test_intersection'
            ],
            'coordinate_system': '3D Cartesian (X, Y, Z)',
            'precision': 'Double precision floating point',
            'tolerance_range': '1e-10 to 1e-3'
        })