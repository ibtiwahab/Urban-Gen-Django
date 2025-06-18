# planning_api/views.py - Fixed version with proper building placement
import logging
import math
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GeneratePlanRequestSerializer, GeneratePlanResponseSerializer

logger = logging.getLogger(__name__)


class SiteParameters:
    """Simplified site parameters class"""
    def __init__(self):
        self.site_type = 0
        self.density = 0.5
        self.site_far = 1.0
        self.mix_ratio = 0.0
        self.building_style = 0
        self.radiant = 0.0
        self.site_area = 0.0
        self.site_curve = None
        self.site_bounds = None  # Add bounds for proper placement
    
    def set_site_from_polyline(self, polyline):
        """Set site parameters from polyline data"""
        self.site_curve = polyline
        if len(polyline) >= 3:
            self.site_area = self._calculate_area(polyline)
            self.radiant = self._calculate_orientation(polyline)
            self.site_bounds = self._calculate_bounds(polyline)
    
    def _calculate_area(self, polyline):
        """Calculate polygon area using shoelace formula"""
        if len(polyline) < 3:
            return 1000.0  # Default area
        
        area = 0.0
        n = len(polyline)
        for i in range(n):
            j = (i + 1) % n
            area += polyline[i]['x'] * polyline[j]['y']
            area -= polyline[j]['x'] * polyline[i]['y']
        return abs(area) / 2.0
    
    def _calculate_orientation(self, polyline):
        """Calculate main orientation of the polygon"""
        if len(polyline) < 2:
            return 0.0
        
        # Find the longest edge
        max_length = 0.0
        main_angle = 0.0
        
        for i in range(len(polyline)):
            j = (i + 1) % len(polyline)
            dx = polyline[j]['x'] - polyline[i]['x']
            dy = polyline[j]['y'] - polyline[i]['y']
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > max_length:
                max_length = length
                main_angle = math.atan2(dy, dx)
        
        return main_angle
    
    def _calculate_bounds(self, polyline):
        """Calculate bounding box of the polygon"""
        if not polyline:
            return {'min_x': 0, 'max_x': 100, 'min_y': 0, 'max_y': 100}
        
        min_x = min(point['x'] for point in polyline)
        max_x = max(point['x'] for point in polyline)
        min_y = min(point['y'] for point in polyline)
        max_y = max(point['y'] for point in polyline)
        
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y
        }


class GeometryProcessor:
    """Simplified geometry processor"""
    
    @staticmethod
    def create_polyline_from_vertices(flattened_vertices):
        """Convert flattened vertices to polyline structure"""
        points = []
        for i in range(0, len(flattened_vertices), 3):
            points.append({
                'x': flattened_vertices[i],
                'y': flattened_vertices[i + 1],
                'z': flattened_vertices[i + 2]
            })
        return points
    
    @staticmethod
    def compute_parameters(polyline):
        """Create site parameters from polyline"""
        site_params = SiteParameters()
        site_params.set_site_from_polyline(polyline)
        return [site_params]
    
    @staticmethod
    def point_in_polygon(point, polygon):
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point['x'], point['y']
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]['x'], polygon[0]['y']
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]['x'], polygon[i % n]['y']
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    @staticmethod
    def generate_building_positions_in_polygon(polygon, num_buildings, building_width, building_depth, min_spacing=5):
        """Generate valid building positions within the polygon boundary"""
        if not polygon or len(polygon) < 3:
            return []
        
        bounds = {
            'min_x': min(point['x'] for point in polygon),
            'max_x': max(point['x'] for point in polygon),
            'min_y': min(point['y'] for point in polygon),
            'max_y': max(point['y'] for point in polygon)
        }
        
        positions = []
        attempts = 0
        max_attempts = num_buildings * 50  # Prevent infinite loops
        
        while len(positions) < num_buildings and attempts < max_attempts:
            attempts += 1
            
            # Generate random position within bounds
            x = random.uniform(bounds['min_x'] + building_width/2, bounds['max_x'] - building_width/2)
            y = random.uniform(bounds['min_y'] + building_depth/2, bounds['max_y'] - building_depth/2)
            
            # Check if all corners of the building are inside the polygon
            building_corners = [
                {'x': x - building_width/2, 'y': y - building_depth/2},
                {'x': x + building_width/2, 'y': y - building_depth/2},
                {'x': x + building_width/2, 'y': y + building_depth/2},
                {'x': x - building_width/2, 'y': y + building_depth/2}
            ]
            
            all_corners_inside = all(GeometryProcessor.point_in_polygon(corner, polygon) for corner in building_corners)
            
            if not all_corners_inside:
                continue
            
            # Check minimum distance from other buildings
            too_close = False
            for existing_pos in positions:
                distance = math.sqrt((x - existing_pos['x'])**2 + (y - existing_pos['y'])**2)
                if distance < (building_width + min_spacing):
                    too_close = True
                    break
            
            if not too_close:
                positions.append({'x': x, 'y': y})
        
        return positions
    
    @staticmethod
    def create_inset_polygon(polygon, inset_distance):
        """Create an inset polygon (simplified approach)"""
        if not polygon or len(polygon) < 3:
            return polygon
        
        # Calculate centroid
        centroid_x = sum(point['x'] for point in polygon) / len(polygon)
        centroid_y = sum(point['y'] for point in polygon) / len(polygon)
        
        # Move each point towards the centroid
        inset_polygon = []
        for point in polygon:
            # Vector from centroid to point
            dx = point['x'] - centroid_x
            dy = point['y'] - centroid_y
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > inset_distance:
                # Normalize and scale
                dx = dx / length * (length - inset_distance)
                dy = dy / length * (length - inset_distance)
                
                inset_polygon.append({
                    'x': centroid_x + dx,
                    'y': centroid_y + dy,
                    'z': point.get('z', 0) + 0.2  # Slight Z offset
                })
        
        return inset_polygon if len(inset_polygon) >= 3 else polygon
    
    @staticmethod
    def compute_design(site_parameters_list):
        """Generate urban design based on parameters"""
        if not site_parameters_list:
            return GeometryProcessor._get_default_response()
        
        site_params = site_parameters_list[0]
        
        if not site_params.site_curve or len(site_params.site_curve) < 3:
            return GeometryProcessor._get_default_response()
        
        # Calculate number of buildings based on area and density
        base_building_area = 300  # Base area per building
        adjusted_area = base_building_area / max(0.1, site_params.density)
        num_buildings = max(1, int(site_params.site_area / adjusted_area))
        num_buildings = min(num_buildings, 8)  # Reasonable limit
        
        response = {
            'buildingLayersHeights': [],
            'buildingLayersVertices': [],
            'subSiteVertices': [],
            'subSiteSetbackVertices': []
        }
        
        # Building parameters
        building_width = 15.0 + (site_params.density * 10.0)  # Density affects size
        building_depth = 12.0 + (site_params.density * 8.0)
        floor_height = 3.0
        num_floors = max(2, int(site_params.site_far * 4))  # FAR affects height
        
        # Generate building positions within the polygon
        building_positions = GeometryProcessor.generate_building_positions_in_polygon(
            site_params.site_curve, num_buildings, building_width, building_depth
        )
        
        logger.info(f"Generated {len(building_positions)} building positions for {num_buildings} requested buildings")
        
        # Create buildings at valid positions
        for pos in building_positions:
            # Building heights for each floor
            heights = [floor_height] * num_floors
            response['buildingLayersHeights'].append(heights)
            
            # Building vertices for each floor
            building_vertices = []
            for floor in range(num_floors):
                z = floor * floor_height
                floor_vertices = [
                    pos['x'] - building_width/2, pos['y'] - building_depth/2, z,  # Bottom-left
                    pos['x'] + building_width/2, pos['y'] - building_depth/2, z,  # Bottom-right  
                    pos['x'] + building_width/2, pos['y'] + building_depth/2, z,  # Top-right
                    pos['x'] - building_width/2, pos['y'] + building_depth/2, z   # Top-left
                ]
                building_vertices.append(floor_vertices)
            
            response['buildingLayersVertices'].append(building_vertices)
        
        # Generate sub-site (use original polyline)
        site_vertices = []
        for point in site_params.site_curve:
            site_vertices.extend([point['x'], point['y'], point.get('z', 0)])
        response['subSiteVertices'].append(site_vertices)
        
        # Generate setback (inset polygon)
        setback_distance = 3.0 + (site_params.density * 2.0)  # Density affects setback
        inset_polygon = GeometryProcessor.create_inset_polygon(site_params.site_curve, setback_distance)
        
        setback_vertices = []
        for point in inset_polygon:
            setback_vertices.extend([point['x'], point['y'], point.get('z', 0.2)])
        
        if setback_vertices:
            response['subSiteSetbackVertices'].append(setback_vertices)
        
        return response
    
    @staticmethod
    def _get_default_response():
        """Return a default response structure"""
        return {
            'buildingLayersHeights': [
                [3.0, 3.0, 3.0],  # Building 1 floor heights
                [4.0, 3.5, 3.5],  # Building 2 floor heights
            ],
            'buildingLayersVertices': [
                [  # Building 1 - 3 floors
                    [0.0, 0.0, 0.0, 20.0, 0.0, 0.0, 20.0, 15.0, 0.0, 0.0, 15.0, 0.0],  # Floor 1
                    [0.0, 0.0, 3.0, 20.0, 0.0, 3.0, 20.0, 15.0, 3.0, 0.0, 15.0, 3.0],  # Floor 2
                    [0.0, 0.0, 6.0, 20.0, 0.0, 6.0, 20.0, 15.0, 6.0, 0.0, 15.0, 6.0],  # Floor 3
                ],
                [  # Building 2 - 3 floors  
                    [30.0, 0.0, 0.0, 50.0, 0.0, 0.0, 50.0, 15.0, 0.0, 30.0, 15.0, 0.0],  # Floor 1
                    [30.0, 0.0, 4.0, 50.0, 0.0, 4.0, 50.0, 15.0, 4.0, 30.0, 15.0, 4.0],  # Floor 2
                    [30.0, 0.0, 7.5, 50.0, 0.0, 7.5, 50.0, 15.0, 7.5, 30.0, 15.0, 7.5],  # Floor 3
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
    """Generate urban plan endpoint"""
    
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
            
            # Convert vertices to polyline
            polyline = GeometryProcessor.create_polyline_from_vertices(flattened_vertices)
            logger.info(f"Converted to polyline with {len(polyline)} points")
            
            # Compute site parameters
            site_parameters_list = GeometryProcessor.compute_parameters(polyline)
            site_parameters = site_parameters_list[0] if site_parameters_list else SiteParameters()
            
            # Fill plan parameters from request
            self._fill_plan_parameters(plan_parameters_data, site_parameters)
            
            logger.info(f"Site parameters: area={site_parameters.site_area:.2f}, FAR={site_parameters.site_far}, density={site_parameters.density}")
            
            # Compute design
            design_result = GeometryProcessor.compute_design(site_parameters_list)
            
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