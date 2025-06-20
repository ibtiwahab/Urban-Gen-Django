# planning_api/views.py - Fixed parameter handling and building generation
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
    """Enhanced site parameters class with better parameter handling"""
    def __init__(self):
        self.site_type = 0
        self.density = 0.5
        self.site_far = 1.0
        self.mix_ratio = 0.0
        self.building_style = 0
        self.radiant = 0.0
        self.site_area = 0.0
        self.site_curve = None
        self.site_polyline = None
        self.site_bounds = None
        
        # Enhanced parameters
        self.min_building_spacing = 5.0
        self.setback_distance = 3.0
        self.use_grid_layout = False
        self.adaptive_orientation = True
        self.max_buildings = 50  # Increased from 8
    
    def set_site_from_polyline(self, flattened_vertices):
        """Set site parameters from flattened vertices using geometry classes"""
        self.site_polyline = CurveOperations.polyline_from_vertices(flattened_vertices)
        
        if self.site_polyline and len(self.site_polyline.points) >= 3:
            self.site_polyline.make_closed()
            self.site_area = self.site_polyline.get_area()
            self.radiant = CurveOperations.calculate_main_orientation(self.site_polyline)
            
            min_point, max_point = self.site_polyline.get_bounding_box()
            self.site_bounds = {
                'min_x': min_point.x,
                'max_x': max_point.x,
                'min_y': min_point.y,
                'max_y': max_point.y
            }
            
            self.site_curve = [{'x': p.x, 'y': p.y, 'z': p.z} for p in self.site_polyline.points]

    def update_dependent_parameters(self):
        """Update dependent parameters based on site type and other settings"""
        # Update building spacing based on density
        base_spacing = 5.0
        if self.density > 0.7:
            self.min_building_spacing = max(3.0, base_spacing * 0.8)
        elif self.density < 0.3:
            self.min_building_spacing = base_spacing * 1.5
        else:
            self.min_building_spacing = base_spacing

        # Update setback based on FAR and site type
        base_setback = 3.0
        if self.site_far > 2.0:
            self.setback_distance = max(base_setback, 4.0)
        else:
            self.setback_distance = base_setback

        # Adjust max buildings based on site area and density
        if self.site_area > 0:
            # Calculate theoretical maximum based on site area
            building_footprint = self.get_building_dimensions()[0] * self.get_building_dimensions()[1]
            spacing_area = self.min_building_spacing * self.min_building_spacing
            total_building_space = building_footprint + spacing_area
            
            theoretical_max = int(self.site_area / total_building_space)
            self.max_buildings = min(theoretical_max, 100)  # Cap at 100 for performance
        
        logger.info(f"Updated parameters: spacing={self.min_building_spacing}, setback={self.setback_distance}, max_buildings={self.max_buildings}")

    def get_building_dimensions(self):
        """Get building dimensions based on site type and density"""
        base_width = 15.0
        base_depth = 12.0
        
        # Adjust based on site type
        type_multipliers = {
            0: (1.0, 1.0),    # Residential
            1: (1.3, 1.2),    # Commercial
            2: (1.2, 1.1),    # Office
            3: (1.1, 1.0),    # Mixed Use
            4: (1.5, 1.4)     # Industrial
        }
        
        width_mult, depth_mult = type_multipliers.get(self.site_type, (1.0, 1.0))
        
        # Adjust based on density
        density_factor = 0.7 + (self.density * 0.6)  # 0.7 to 1.3
        
        width = base_width * width_mult * density_factor
        depth = base_depth * depth_mult * density_factor
        
        return width, depth


class EnhancedGeometryProcessor:
    """Enhanced geometry processor with better building generation"""
    
    @staticmethod
    def compute_parameters(flattened_vertices):
        """Create site parameters from flattened vertices"""
        site_params = SiteParameters()
        site_params.set_site_from_polyline(flattened_vertices)
        return [site_params]
    
    @staticmethod
    def compute_design(site_parameters_list):
        """Generate urban design with improved building placement"""
        if not site_parameters_list:
            return EnhancedGeometryProcessor._get_default_response()
        
        site_params = site_parameters_list[0]
        
        if not site_params.site_polyline or len(site_params.site_polyline.points) < 3:
            return EnhancedGeometryProcessor._get_default_response()
        
        try:
            # Update dependent parameters
            site_params.update_dependent_parameters()
            
            # Use parametric design to generate layout
            design_result = ParametricDesign.apply_site_parameters(
                site_params.site_polyline.points,
                site_params.site_area,
                site_params.density,
                site_params.site_far,
                site_params.mix_ratio,
                site_params.building_style,
                site_params.radiant,
                site_params.max_buildings  # Pass max buildings limit
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
            
            logger.info(f"Generated {len(building_positions)} buildings with width={building_width:.1f}, depth={building_depth:.1f}")
            
            # Create buildings using surface operations
            for pos in building_positions:
                building_vertices = SurfaceOperations.create_building_vertices_array(
                    pos, building_width, building_depth, floors_per_building, floor_height
                )
                
                heights = [floor_height] * floors_per_building
                response['buildingLayersHeights'].append(heights)
                response['buildingLayersVertices'].append(building_vertices)
            
            # Generate sub-site (original polygon)
            site_vertices = []
            for point in site_params.site_polyline.points:
                site_vertices.extend([point.x, point.y, point.z])
            response['subSiteVertices'].append(site_vertices)
            
            # Generate setback using offset operations
            offset_polyline = OffsetOperations.offset_polygon(
                site_params.site_polyline, site_params.setback_distance
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
    """Enhanced generate urban plan endpoint with better parameter handling"""
    
    def post(self, request):
        try:
            # Validate input data
            serializer = GeneratePlanRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            flattened_vertices = validated_data['plan_flattened_vertices']
            plan_parameters_data = validated_data.get('plan_parameters', {})
            
            logger.info(f"Received plan generation request with {len(flattened_vertices)} vertices")
            logger.info(f"Plan parameters: {plan_parameters_data}")
            
            # Compute site parameters using enhanced geometry processor
            site_parameters_list = EnhancedGeometryProcessor.compute_parameters(flattened_vertices)
            site_parameters = site_parameters_list[0] if site_parameters_list else SiteParameters()
            
            # Fill plan parameters from request - FIXED PARAMETER HANDLING
            self._fill_plan_parameters(plan_parameters_data, site_parameters)
            
            logger.info(f"Final parameters: area={site_parameters.site_area:.2f}, FAR={site_parameters.site_far}, density={site_parameters.density}, site_type={site_parameters.site_type}, building_style={site_parameters.building_style}")
            
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
        """Fill site parameters from request data - FIXED VERSION"""
        if not plan_params_data:
            logger.warning("No plan parameters provided, using defaults")
            return
        
        logger.info(f"Processing plan parameters: {plan_params_data}")
        
        # Site type - FIXED
        if 'site_type' in plan_params_data:
            site_type = int(plan_params_data['site_type'])
            if 0 <= site_type <= 4:
                site_parameters.site_type = site_type
                logger.info(f"Set site_type to {site_type}")
            else:
                logger.warning(f"Invalid site_type: {site_type}")
        
        # FAR (Floor Area Ratio) - FIXED
        if 'far' in plan_params_data:
            far = float(plan_params_data['far'])
            if 0.0 <= far <= 10.0:
                site_parameters.site_far = far
                logger.info(f"Set FAR to {far}")
            else:
                logger.warning(f"Invalid FAR: {far}")
        
        # Density - FIXED
        if 'density' in plan_params_data:
            density = float(plan_params_data['density'])
            if 0.0 <= density <= 0.99:  # Changed from 1.0 to 0.99 to match frontend
                site_parameters.density = density
                logger.info(f"Set density to {density}")
            else:
                logger.warning(f"Invalid density: {density}")
        
        # Mix ratio - FIXED
        if 'mix_ratio' in plan_params_data:
            mix_ratio = float(plan_params_data['mix_ratio'])
            if 0.0 <= mix_ratio <= 0.99:  # Changed from 1.0 to 0.99 to match frontend
                site_parameters.mix_ratio = mix_ratio
                logger.info(f"Set mix_ratio to {mix_ratio}")
            else:
                logger.warning(f"Invalid mix_ratio: {mix_ratio}")
        
        # Building style - FIXED
        if 'building_style' in plan_params_data:
            building_style = int(plan_params_data['building_style'])
            if 0 <= building_style <= 3:
                site_parameters.building_style = building_style
                logger.info(f"Set building_style to {building_style}")
            else:
                logger.warning(f"Invalid building_style: {building_style}")
        
        # Orientation - FIXED
        if 'orientation' in plan_params_data:
            orientation = float(plan_params_data['orientation'])
            if 0.0 <= orientation <= 180.0:
                site_parameters.radiant = math.radians(orientation)
                logger.info(f"Set orientation to {orientation} degrees ({site_parameters.radiant} radians)")
            else:
                logger.warning(f"Invalid orientation: {orientation}")


class GeometryAnalysisView(APIView):
    """Enhanced geometry analysis endpoint"""
    
    def post(self, request):
        try:
            flattened_vertices = request.data.get('vertices', [])
            operation = request.data.get('operation', 'analyze')
            
            if len(flattened_vertices) < 9:
                return Response(
                    {'error': 'At least 3 vertices required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            polyline = CurveOperations.polyline_from_vertices(flattened_vertices)
            
            if operation == 'analyze':
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