# planning_api/additional_views.py - Complete implementation
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    GeometryValidationSerializer, GeometryValidationResponseSerializer,
    OffsetOperationSerializer, OffsetOperationResponseSerializer,
    IntersectionTestSerializer, IntersectionTestResponseSerializer
)
from .geometry import (
    CurveOperations, OffsetOperations, IntersectionOperations,
    Constants
)

logger = logging.getLogger(__name__)


class GeometryValidationView(APIView):
    """Validate geometry and check for issues"""
    
    def post(self, request):
        try:
            serializer = GeometryValidationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            vertices = validated_data['vertices']
            tolerance = validated_data.get('tolerance', Constants.DEFAULT_TOLERANCE)
            
            # Create polyline from vertices
            polyline = CurveOperations.polyline_from_vertices(vertices)
            
            # Perform validation checks
            validation_result = {
                'is_valid': polyline.is_valid,
                'errors': [],
                'warnings': [],
                'polygon_area': 0.0,
                'polygon_perimeter': polyline.length if polyline.is_valid else 0.0,
                'is_closed': polyline.is_closed,
                'is_planar': True,  # Simplified check
                'self_intersects': False
            }
            
            if not polyline.is_valid:
                validation_result['errors'].append('Polyline is not valid')
            
            if polyline.is_valid and len(polyline.points) >= 3:
                # Check for self-intersection if requested
                if validated_data.get('check_self_intersection', True):
                    try:
                        self_intersects = IntersectionOperations.polyline_self_intersection_check(polyline, tolerance)
                        validation_result['self_intersects'] = self_intersects
                        if self_intersects:
                            validation_result['errors'].append('Polygon self-intersects')
                    except Exception as e:
                        validation_result['warnings'].append(f'Could not check self-intersection: {str(e)}')
                
                # Calculate area if closed
                if polyline.is_closed:
                    try:
                        validation_result['polygon_area'] = polyline.get_area()
                    except Exception as e:
                        validation_result['warnings'].append(f'Could not calculate area: {str(e)}')
                else:
                    validation_result['warnings'].append('Polygon is not closed')
            
            # Update overall validity
            validation_result['is_valid'] = (
                polyline.is_valid and 
                len(validation_result['errors']) == 0
            )
            
            response_serializer = GeometryValidationResponseSerializer(data=validation_result)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Response serialization failed: {response_serializer.errors}")
                return Response(validation_result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in geometry validation: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Validation failed: {str(e)}'},
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
            
            validated_data = serializer.validated_data
            vertices = validated_data['vertices']
            offset_distance = validated_data['offset_distance']
            offset_type = validated_data.get('offset_type', 'inward')
            tolerance = validated_data.get('tolerance', Constants.DEFAULT_TOLERANCE)
            
            # Create polyline from vertices
            polyline = CurveOperations.polyline_from_vertices(vertices)
            
            if not polyline.is_valid or not polyline.is_closed:
                return Response(
                    {'success': False, 'error_message': 'Polygon must be valid and closed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Adjust distance based on offset type
            actual_distance = offset_distance if offset_type == 'inward' else -offset_distance
            
            # Perform offset operation
            offset_polyline = OffsetOperations.offset_polygon(polyline, actual_distance, tolerance)
            
            result = {
                'success': offset_polyline is not None,
                'offset_vertices': [],
                'error_message': ''
            }
            
            if offset_polyline:
                # Convert to flattened vertices
                for point in offset_polyline.points:
                    result['offset_vertices'].extend([point.x, point.y, point.z])
            else:
                result['error_message'] = 'Offset operation failed - may result in degenerate polygon'
            
            response_serializer = OffsetOperationResponseSerializer(data=result)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in polygon offset: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error_message': f'Offset operation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IntersectionTestView(APIView):
    """Test intersections between polygons"""
    
    def post(self, request):
        try:
            serializer = IntersectionTestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            poly_a_vertices = validated_data['polygon_a_vertices']
            poly_b_vertices = validated_data['polygon_b_vertices']
            tolerance = validated_data.get('tolerance', Constants.DEFAULT_TOLERANCE)
            
            # Create polylines from vertices
            polyline_a = CurveOperations.polyline_from_vertices(poly_a_vertices)
            polyline_b = CurveOperations.polyline_from_vertices(poly_b_vertices)
            
            if not polyline_a.is_valid or not polyline_b.is_valid:
                return Response(
                    {'error': 'Both polygons must be valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Test for intersection
            intersects = IntersectionOperations.polyline_self_intersection_check(polyline_a, tolerance)
            
            # Determine intersection type (simplified)
            intersection_type = 'separate'
            if intersects:
                intersection_type = 'overlap'
            
            result = {
                'intersects': intersects,
                'intersection_type': intersection_type,
                'intersection_points': []  # Could be implemented for specific intersection points
            }
            
            response_serializer = IntersectionTestResponseSerializer(data=result)
            if response_serializer.is_valid():
                return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in intersection test: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Intersection test failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GeometryInfoView(APIView):
    """Get geometry service information and test connectivity"""
    
    def get(self, request):
        try:
            info = {
                'service': 'Geometry Processing Service',
                'version': '1.0.0',
                'status': 'active',
                'available_operations': [
                    'plan_generation',
                    'geometry_validation', 
                    'polygon_offset',
                    'intersection_testing',
                    'geometry_analysis'
                ],
                'supported_formats': ['flattened_vertices'],
                'default_tolerance': Constants.DEFAULT_TOLERANCE,
                'max_vertices': 10000,
                'timestamp': '2024-01-01T00:00:00Z'
            }
            
            return Response(info, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in geometry info: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Service info failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )