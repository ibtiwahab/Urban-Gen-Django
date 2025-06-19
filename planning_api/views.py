# planning_api/views.py - Enhanced with geometry integration
import logging
import math
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GeneratePlanRequestSerializer, GeneratePlanResponseSerializer
from .geometry import (
    Point3D, Polyline, CurveOperations, ParametricDesign, 
    BuildingPlacement, OffsetOperations, SurfaceOperations
)

logger = logging.getLogger(__name__)


class SiteParameters:
    """Enhanced site parameters class with geometry integration"""
    def __init__(self):
        self.site_type = 0
        self.density = 0.5
        self.site_far = 1.0
        self.mix_ratio = 0.0
        self.building_style = 0
        self.radiant = 0.0
        self.site_area = 0.0
        self.site_curve = None
        self.site_polyline = None  # Add Polyline object
        self.site_bounds = None
    
    def set_site_from_polyline(self, flattened_vertices):
        """Set site parameters from flattened vertices using geometry classes"""
        # Convert to Polyline object
        self.site_polyline = CurveOperations.polyline_from_vertices(flattened_vertices)
        
        if self.site_polyline and len(self.site_polyline.points) >= 3:
            # Make closed if needed
            self.site_polyline.make_closed()
            
            # Calculate area using geometry class
            self.site_area = self.site_polyline.get_area()
            
            # Calculate orientation
            self.radiant = CurveOperations.calculate_main_orientation(self.site_polyline)
            
            # Calculate bounds
            min_point, max_point = self.site_polyline.get_bounding_box()
            self.site_bounds = {
                'min_x': min_point.x,
                'max_x': max_point.x,
                'min_y': min_point.y,
                'max_y': max_point.y
            }
            
            # Keep legacy format for compatibility
            self.site_curve = [{'x': p.x, 'y': p.y, 'z': p.z} for p in self.site_polyline.points]


class EnhancedGeometryProcessor:
    """Enhanced geometry processor using the geometry package"""
    
    @staticmethod
    def compute_parameters(flattened_vertices):
        """Create site parameters from flattened vertices"""
        site_params = SiteParameters()
        site_params.set_site_from_polyline(flattened_vertices)
        return [site_params]
    
    @staticmethod
    def compute_design(site_parameters_list):
        """Generate urban design using advanced geometry operations"""
        if not site_parameters_list:
            return EnhancedGeometryProcessor._get_default_response()
        
        site_params = site_parameters_list[0]
        
        if not site_params.site_polyline or len(site_params.site_polyline.points) < 3:
            return EnhancedGeometryProcessor._get_default_response()
        
        try:
            # Use parametric design to generate layout
            design_result = ParametricDesign.apply_site_parameters(
                site_params.site_polyline.points,
                site_params.site_area,
                site_params.density,
                site_params.site_far,
                site_params.mix_ratio,
                site_params.building_style,
                site_params.radiant
            )
            
            response = {
                'buildingLayersHeights': [],
                'buildingLayersVertices': [],
                'subSiteVertices': [],
                'subSiteSetbackVertices': []
            }
            
            # Generate buildings from parametric design
            building_positions = design_result['building_positions']
            building_width = design_result['building_width']
            building_depth = design_result['building_depth']
            floors_per_building = design_result['floors_per_building']
            floor_height = design_result['floor_height']
            
            logger.info(f"Parametric design generated {len(building_positions)} buildings")
            
            # Create buildings using surface operations
            for pos in building_positions:
                # Create building vertices using surface operations
                building_vertices = SurfaceOperations.create_building_vertices_array(
                    pos, building_width, building_depth, floors_per_building, floor_height
                )
                
                # Building heights for each floor
                heights = [floor_height] * floors_per_building
                response['buildingLayersHeights'].append(heights)
                response['buildingLayersVertices'].append(building_vertices)
            
            # Generate sub-site (original polygon)
            site_vertices = []
            for point in site_params.site_polyline.points:
                site_vertices.extend([point.x, point.y, point.z])
            response['subSiteVertices'].append(site_vertices)
            
            # Generate setback using offset operations
            setback_distance = 3.0 + (site_params.density * 2.0)
            
            # Use geometry operations for proper offset
            offset_polyline = OffsetOperations.offset_polygon(
                site_params.site_polyline, setback_distance
            )
            
            if offset_polyline:
                setback_vertices = []
                for point in offset_polyline.points:
                    setback_vertices.extend([point.x, point.y, point.z + 0.2])
                response['subSiteSetbackVertices'].append(setback_vertices)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in parametric design generation: {str(e)}")
            return EnhancedGeometryProcessor._get_default_response()
    
    @staticmethod
    def _get_default_response():
        """Return a default response structure"""
        return {
            'buildingLayersHeights': [
                [3.0, 3.0, 3.0],
                [4.0, 3.5, 3.5],
            ],
            'buildingLayersVertices': [
                [
                    [0.0, 0.0, 0.0, 20.0, 0.0, 0.0, 20.0, 15.0, 0.0, 0.0, 15.0, 0.0],
                    [0.0, 0.0, 3.0, 20.0, 0.0, 3.0, 20.0, 15.0, 3.0, 0.0, 15.0, 3.0],
                    [0.0, 0.0, 6.0, 20.0, 0.0, 6.0, 20.0, 15.0, 6.0, 0.0, 15.0, 6.0],
                ],
                [
                    [30.0, 0.0, 0.0, 50.0, 0.0, 0.0, 50.0, 15.0, 0.0, 30.0, 15.0, 0.0],
                    [30.0, 0.0, 4.0, 50.0, 0.0, 4.0, 50.0, 15.0, 4.0, 30.0, 15.0, 4.0],
                    [30.0, 0.0, 7.5, 50.0, 0.0, 7.5, 50.0, 15.0, 7.5, 30.0, 15.0, 7.5],
                ]
            ],
            'subSiteVertices': [
                [0.0, 0.0, 0.0, 80.0, 0.0, 0.0, 80.0, 50.0, 0.0, 0.0, 50.0, 0.0]
            ],
            'subSiteSetbackVertices': [
                [5.0, 5.0, 0.2, 75.0, 5.0, 0.2, 75.0, 45.0, 0.2, 5.0, 45.0, 0.2]
            ]
        }


class GeneratePlanView(APIView):
    """Enhanced generate urban plan endpoint with geometry integration"""
    
    def post(self, request):
        try:
            # Validate input data
            serializer = GeneratePlanRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            flattened_vertices = validated_data['plan_flattened_vertices']
            plan_parameters_data = validated_data.get('plan_parameters', {})
            
            logger.info(f"Received plan generation request with {len(flattened_vertices)} vertices")
            
            # Compute site parameters using enhanced geometry processor
            site_parameters_list = EnhancedGeometryProcessor.compute_parameters(flattened_vertices)
            site_parameters = site_parameters_list[0] if site_parameters_list else SiteParameters()
            
            # Fill plan parameters from request
            self._fill_plan_parameters(plan_parameters_data, site_parameters)
            
            logger.info(f"Site parameters: area={site_parameters.site_area:.2f}, FAR={site_parameters.site_far}, density={site_parameters.density}")
            
            # Compute design using enhanced processor
            design_result = EnhancedGeometryProcessor.compute_design(site_parameters_list)
            
            # Serialize response
            response_serializer = GeneratePlanResponseSerializer(data=design_result)
            if response_serializer.is_valid():
                logger.info(f"Plan generation successful - {len(design_result['buildingLayersVertices'])} buildings generated")
                return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Response serialization failed: {response_serializer.errors}")
                return Response(
                    {'error': 'Internal processing failed'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Error in GeneratePlan: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Internal server error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _fill_plan_parameters(self, plan_params_data, site_parameters):
        """Fill site parameters from request data"""
        if not plan_params_data:
            return
        
        # Site type
        if 'site_type' in plan_params_data:
            site_type = plan_params_data['site_type']
            if 0 <= site_type <= 4:
                site_parameters.site_type = site_type
        
        # FAR (Floor Area Ratio)
        if 'far' in plan_params_data:
            far = plan_params_data['far']
            if 0.0 <= far <= 10.0:
                site_parameters.site_far = far
        
        # Density
        if 'density' in plan_params_data:
            density = plan_params_data['density']
            if 0.0 <= density <= 1.0:
                site_parameters.density = density
        
        # Mix ratio
        if 'mix_ratio' in plan_params_data:
            mix_ratio = plan_params_data['mix_ratio']
            if 0.0 <= mix_ratio <= 1.0:
                site_parameters.mix_ratio = mix_ratio
        
        # Building style
        if 'building_style' in plan_params_data:
            building_style = plan_params_data['building_style']
            if 0 <= building_style <= 3:
                site_parameters.building_style = building_style
        
        # Orientation
        if 'orientation' in plan_params_data:
            orientation = plan_params_data['orientation']
            if 0.0 <= orientation <= 180.0:
                site_parameters.radiant = math.radians(orientation)


class GeometryAnalysisView(APIView):
    """New endpoint for geometry analysis operations"""
    
    def post(self, request):
        try:
            # Validate geometry data
            flattened_vertices = request.data.get('vertices', [])
            operation = request.data.get('operation', 'analyze')
            
            if len(flattened_vertices) < 9:  # At least 3 points
                return Response(
                    {'error': 'At least 3 vertices required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create polyline
            polyline = CurveOperations.polyline_from_vertices(flattened_vertices)
            
            if operation == 'analyze':
                # Basic analysis
                analysis = {
                    'area': polyline.get_area(),
                    'perimeter': polyline.length,
                    'is_closed': polyline.is_closed,
                    'is_valid': polyline.is_valid,
                    'centroid': {
                        'x': polyline.get_centroid().x,
                        'y': polyline.get_centroid().y,
                        'z': polyline.get_centroid().z
                    },
                    'main_orientation': CurveOperations.calculate_main_orientation(polyline)
                }
                return Response(analysis, status=status.HTTP_200_OK)
            
            elif operation == 'offset':
                # Offset polygon
                offset_distance = request.data.get('offset_distance', 5.0)
                offset_polyline = OffsetOperations.offset_polygon(polyline, offset_distance)
                
                if offset_polyline:
                    offset_vertices = []
                    for point in offset_polyline.points:
                        offset_vertices.extend([point.x, point.y, point.z])
                    return Response({'offset_vertices': offset_vertices}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Offset operation failed'}, status=status.HTTP_400_BAD_REQUEST)
            
            elif operation == 'validate':
                # Polygon validation
                from .geometry.advanced import IntersectionOperations
                self_intersects = IntersectionOperations.polyline_self_intersection_check(polyline)
                
                validation = {
                    'is_valid': polyline.is_valid,
                    'is_closed': polyline.is_closed,
                    'self_intersects': self_intersects,
                    'point_count': len(polyline.points)
                }
                return Response(validation, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {'error': f'Unknown operation: {operation}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            logger.error(f"Error in GeometryAnalysis: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Geometry analysis failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )