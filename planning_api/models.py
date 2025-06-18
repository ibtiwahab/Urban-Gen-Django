# planning_api/urban_design/models.py
import math
import random
from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np


class SiteTypes(Enum):
    """Site types enumeration"""
    R = 0    # Residential
    C = 1    # Commercial
    GIC = 2  # Government/Institutional/Cultural
    M = 3    # Mixed
    W = 4    # Waterfront
    U = 5    # Undefined


class MixTypes(Enum):
    """Mix types enumeration"""
    HORIZONTAL = 0  # Mixed buildings occupy another subsite
    VERTICAL = 1    # Mixed function share the same building with different layers
    NONE = 2        # Site only has main type buildings


class NonResidentialStyles(Enum):
    """Non-residential building styles"""
    ALONE = 0   # Single dot building
    GROUP = 1   # Group buildings around boundary
    MIXED = 2   # Combining Alone and Group style


class ResidentialStyles(Enum):
    """Residential building styles"""
    ROW_RADIANCE = 0        # Parallel partitions with certain radiance
    DOT_VARIOUS_HEIGHT = 1  # Dot residential style with different building height
    DOT_ROW_MAJOR = 2       # Horizontal parallel partitions with rotating building
    DOT_COLUMN_MAJOR = 3    # Vertical parallel partitions with rotating building


@dataclass
class Point3D:
    """3D Point representation"""
    x: float
    y: float
    z: float


@dataclass
class BuildingParameters:
    """Building parameters structure"""
    name: str
    area: float
    floor_range: Tuple[int, int]
    depth_range: Tuple[float, float]
    priority: int
    floor_height: float
    function: str


class BuildingDataset:
    """Static class for building data - equivalent to C# BuildingDataset"""
    
    # Building types database
    BUILDING_TYPES = {
        'ResidentialLow': BuildingParameters(
            name='ResidentialLow',
            area=400.0,
            floor_range=(1, 6),
            depth_range=(12.0, 18.0),
            priority=1,
            floor_height=3.0,
            function='R'
        ),
        'ResidentialMid': BuildingParameters(
            name='ResidentialMid',
            area=600.0,
            floor_range=(7, 18),
            depth_range=(15.0, 25.0),
            priority=2,
            floor_height=3.0,
            function='R'
        ),
        'ResidentialHigh': BuildingParameters(
            name='ResidentialHigh',
            area=800.0,
            floor_range=(19, 45),
            depth_range=(20.0, 30.0),
            priority=3,
            floor_height=3.0,
            function='R'
        ),
        'CommercialLow': BuildingParameters(
            name='CommercialLow',
            area=500.0,
            floor_range=(1, 5),
            depth_range=(15.0, 25.0),
            priority=1,
            floor_height=4.0,
            function='C'
        ),
        'CommercialMid': BuildingParameters(
            name='CommercialMid',
            area=800.0,
            floor_range=(6, 15),
            depth_range=(20.0, 30.0),
            priority=2,
            floor_height=4.0,
            function='C'
        ),
        'Office': BuildingParameters(
            name='Office',
            area=1000.0,
            floor_range=(5, 30),
            depth_range=(25.0, 35.0),
            priority=2,
            floor_height=3.5,
            function='O'
        ),
    }
    
    @staticmethod
    def get_building_parameters(building_type: str) -> BuildingParameters:
        """Get building parameters by type name"""
        return BuildingDataset.BUILDING_TYPES.get(building_type, 
                                                  BuildingDataset.BUILDING_TYPES['ResidentialLow'])
    
    @staticmethod
    def get_setback_r_type(floor_count: int) -> float:
        """Get setback distance for residential buildings"""
        if floor_count <= 3:
            return 3.0
        elif floor_count <= 6:
            return 5.0
        elif floor_count <= 12:
            return 8.0
        else:
            return 12.0
    
    @staticmethod
    def get_setback_other_type(height: float) -> float:
        """Get setback distance for other building types"""
        if height <= 15:
            return 4.0
        elif height <= 30:
            return 6.0
        elif height <= 60:
            return 10.0
        else:
            return 15.0
    
    @staticmethod
    def get_sunlight_distance(height: float, city_index: int = 0) -> float:
        """Calculate sunlight distance based on building height"""
        # Simplified calculation - in reality this would use sun angle calculations
        base_ratio = 1.5  # Base ratio for sunlight distance
        latitude_factor = 1.0  # Adjust based on city location
        return height * base_ratio * latitude_factor


class SiteDataset:
    """Static class for site data - equivalent to C# SiteDataset"""
    
    MAIN_BUILDING_TYPES = {
        SiteTypes.R: ['ResidentialLow', 'ResidentialMid', 'ResidentialHigh'],
        SiteTypes.C: ['CommercialLow', 'CommercialMid', 'Office'],
        SiteTypes.GIC: ['Office'],
        SiteTypes.M: ['ResidentialLow', 'CommercialLow', 'Office'],
        SiteTypes.W: ['ResidentialMid', 'CommercialMid'],
        SiteTypes.U: ['ResidentialLow']
    }
    
    MIXED_BUILDING_TYPES = {
        SiteTypes.R: ['CommercialLow'],
        SiteTypes.C: ['ResidentialLow'],
        SiteTypes.GIC: ['CommercialLow'],
        SiteTypes.M: ['ResidentialLow', 'CommercialLow'],
        SiteTypes.W: ['CommercialLow'],
        SiteTypes.U: ['CommercialLow']
    }
    
    FAR_INTERVALS = {
        SiteTypes.R: (0.5, 2.0),
        SiteTypes.C: (1.0, 4.0),
        SiteTypes.GIC: (0.8, 2.5),
        SiteTypes.M: (0.8, 3.0),
        SiteTypes.W: (0.4, 2.5),
        SiteTypes.U: (0.5, 2.0)
    }
    
    DENSITY_INTERVALS = {
        SiteTypes.R: (0.2, 0.8),
        SiteTypes.C: (0.3, 0.9),
        SiteTypes.GIC: (0.25, 0.7),
        SiteTypes.M: (0.3, 0.8),
        SiteTypes.W: (0.15, 0.6),
        SiteTypes.U: (0.2, 0.7)
    }
    
    MIX_COEFFICIENTS = {
        SiteTypes.R: 1.0,
        SiteTypes.C: 0.8,
        SiteTypes.GIC: 0.6,
        SiteTypes.M: 1.2,
        SiteTypes.W: 0.9,
        SiteTypes.U: 0.8
    }
    
    @staticmethod
    def get_main_building_types(site_type: SiteTypes) -> List[str]:
        """Get main building types for site type"""
        return SiteDataset.MAIN_BUILDING_TYPES.get(site_type, ['ResidentialLow'])
    
    @staticmethod
    def get_mixed_building_types(site_type: SiteTypes) -> List[str]:
        """Get mixed building types for site type"""
        return SiteDataset.MIXED_BUILDING_TYPES.get(site_type, ['CommercialLow'])
    
    @staticmethod
    def get_far_interval(site_type: SiteTypes) -> Tuple[float, float]:
        """Get FAR interval for site type"""
        return SiteDataset.FAR_INTERVALS.get(site_type, (0.5, 2.0))
    
    @staticmethod
    def get_density_interval(site_type: SiteTypes) -> Tuple[float, float]:
        """Get density interval for site type"""
        return SiteDataset.DENSITY_INTERVALS.get(site_type, (0.2, 0.8))
    
    @staticmethod
    def get_mixed_coefficients(site_type: SiteTypes) -> float:
        """Get mixed use coefficients"""
        return SiteDataset.MIX_COEFFICIENTS.get(site_type, 1.0)


class SiteParameters:
    """Site parameters class - equivalent to C# SiteParameters"""
    
    def __init__(self):
        self.site_curve = None
        self.radiant = 0.0
        self.scores = [1.0, 1.0, 1.0, 1.0]
        self.density = 0.5
        self.site_far = 1.0
        self.site_type = SiteTypes.R.value
        self.mix_ratio = 0.0
        self.building_style = 0
        self.site_area = 0.0
    
    def set_site_from_polyline(self, polyline: List[dict]):
        """Set site curve from polyline points"""
        self.site_curve = polyline
        self.site_area = self._calculate_area(polyline)
        self.radiant = self._calculate_radiant(polyline)
    
    def _calculate_area(self, polyline: List[dict]) -> float:
        """Calculate area using shoelace formula"""
        if len(polyline) < 3:
            return 0.0
        
        area = 0.0
        n = len(polyline)
        for i in range(n):
            j = (i + 1) % n
            area += polyline[i]['x'] * polyline[j]['y']
            area -= polyline[j]['x'] * polyline[i]['y']
        return abs(area) / 2.0
    
    def _calculate_radiant(self, polyline: List[dict]) -> float:
        """Calculate main orientation of the site"""
        if len(polyline) < 2:
            return 0.0
        
        # Find the longest edge
        max_length = 0.0
        main_vector = None
        
        for i in range(len(polyline)):
            j = (i + 1) % len(polyline)
            dx = polyline[j]['x'] - polyline[i]['x']
            dy = polyline[j]['y'] - polyline[i]['y']
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > max_length:
                max_length = length
                main_vector = (dx/length, dy/length)
        
        if main_vector:
            return math.atan2(main_vector[1], main_vector[0])
        return 0.0
    
    def get_mix_type(self) -> MixTypes:
        """Determine mix type based on mix ratio"""
        if self.mix_ratio <= 0.05:
            return MixTypes.NONE
        elif self.mix_ratio > 0.12:
            return MixTypes.HORIZONTAL
        else:
            return MixTypes.VERTICAL
    
    def set_site_type(self, site_type: int):
        """Set site type"""
        if 0 <= site_type <= 5:
            self.site_type = site_type
    
    def set_site_far(self, far: float):
        """Set Floor Area Ratio"""
        self.site_far = max(0.0, far)
    
    def set_density(self, density: float):
        """Set density"""
        self.density = max(0.0, min(1.0, density))
    
    def set_mix_ratio(self, mix_ratio: float):
        """Set mix ratio"""
        self.mix_ratio = max(0.0, min(1.0, mix_ratio))
    
    def set_building_style(self, building_style: int):
        """Set building style"""
        self.building_style = max(0, building_style)
    
    def set_radiant(self, radiant: float):
        """Set site orientation"""
        # Normalize radiant to be within reasonable range
        while radiant > math.pi:
            radiant -= math.pi
        while radiant < -math.pi:
            radiant += math.pi
        self.radiant = radiant


@dataclass
class BuildingType:
    """Building type structure - equivalent to C# BuildingType"""
    type_name: str
    floors: List[int]  # [mixed_floors, main_floors]
    site_area: float
    parameters: BuildingParameters = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = BuildingDataset.get_building_parameters(self.type_name)
    
    @property
    def area(self) -> float:
        """Get building footprint area"""
        return self.parameters.area
    
    @property
    def ratio(self) -> float:
        """Get area ratio to site"""
        return self.area / self.site_area if self.site_area > 0 else 0
    
    @property
    def priority(self) -> int:
        """Get building priority"""
        return self.parameters.priority


class BuildingGeometry:
    """Building geometry class - equivalent to C# BuildingGeometry"""
    
    def __init__(self, building_type: BuildingType, tolerance: float = 0.01):
        self.building_type = building_type
        self.tolerance = tolerance
        self.layers = []
        self.layer_heights = []
        self.building_area = 0.0
        self.footprint_area = 0.0
    
    def generate_residential_alone_style(self, outline: List[Point3D]):
        """Generate residential building in alone style"""
        self._generate_building_layers(outline)
    
    def generate_non_residential_alone_style(self, outline: List[Point3D]):
        """Generate non-residential building in alone style"""
        self._generate_building_layers(outline)
    
    def _generate_building_layers(self, outline: List[Point3D]):
        """Generate building layers from outline"""
        total_floors = sum(self.building_type.floors)
        floor_height = self.building_type.parameters.floor_height
        
        # Calculate footprint area
        self.footprint_area = self._calculate_polygon_area(outline)
        self.building_area = self.footprint_area * total_floors
        
        # Generate layers
        for floor in range(total_floors + 1):  # +1 for roof
            layer_z = floor * floor_height
            layer_outline = []
            
            for point in outline:
                layer_outline.append(Point3D(point.x, point.y, layer_z))
            
            self.layers.append(LayerGeometry(layer_outline))
            
            if floor < total_floors:
                self.layer_heights.append(floor_height)
    
    def _calculate_polygon_area(self, points: List[Point3D]) -> float:
        """Calculate polygon area using shoelace formula"""
        if len(points) < 3:
            return 0.0
        
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i].x * points[j].y
            area -= points[j].x * points[i].y
        return abs(area) / 2.0


@dataclass
class LayerGeometry:
    """Layer geometry structure"""
    vertices: List[Point3D]


class DesignResult:
    """Design result class - equivalent to C# DesignResult"""
    
    def __init__(self, site_curve, site_area: float, site_type: str):
        self.site_curve = site_curve
        self.site_area = site_area
        self.site_type = site_type
        self.building_geometries = []
        self.sub_sites = []
        self.setbacks = []
    
    def add_building_geometry(self, geometry: BuildingGeometry):
        """Add building geometry to result"""
        self.building_geometries.append(geometry)


class DesignCalculator:
    """Main design calculator - equivalent to C# DesignCalculator"""
    
    def __init__(self, site, site_type: SiteTypes, density: float, far: float, 
                 mix_type: MixTypes = MixTypes.NONE, mix_ratio: float = 0.0):
        self.site = site
        self.site_type = site_type
        self.density = density
        self.far = far
        self.mix_type = mix_type
        self.mix_ratio = mix_ratio
        self.site_area = self._calculate_site_area()
    
    def _calculate_site_area(self) -> float:
        """Calculate site area"""
        if isinstance(self.site, list) and len(self.site) > 0:
            if isinstance(self.site[0], dict):
                # Polyline format
                area = 0.0
                n = len(self.site)
                for i in range(n):
                    j = (i + 1) % n
                    area += self.site[i]['x'] * self.site[j]['y']
                    area -= self.site[j]['x'] * self.site[i]['y']
                return abs(area) / 2.0
        return 1000.0  # Default area
    
    def calculate_residential_types(self, city_index: int, radiant: float, 
                                  scores: List[float], style: int, tolerance: float) -> DesignResult:
        """Calculate residential building types"""
        result = DesignResult(self.site, self.site_area, "Residential")
        
        # Get building types for residential
        main_types = SiteDataset.get_main_building_types(SiteTypes.R)
        
        # Select appropriate building type based on density and FAR
        selected_type = self._select_building_type(main_types)
        
        # Calculate building count and floors
        building_count = self._calculate_building_count(selected_type)
        floors = self._calculate_floors(selected_type)
        
        # Create building geometry
        building_type = BuildingType(selected_type, floors, self.site_area)
        
        # Generate simple rectangular buildings
        for i in range(building_count):
            geometry = BuildingGeometry(building_type, tolerance)
            outline = self._generate_building_outline(i, building_count)
            geometry.generate_residential_alone_style(outline)
            result.add_building_geometry(geometry)
        
        return result
    
    def calculate_non_residential_types(self, radiant: float, scores: List[float], 
                                      tolerance: float, style: int) -> DesignResult:
        """Calculate non-residential building types"""
        result = DesignResult(self.site, self.site_area, "NonResidential")
        
        # Get building types for current site type
        site_type = SiteTypes(self.site_type)
        main_types = SiteDataset.get_main_building_types(site_type)
        
        # Select appropriate building type
        selected_type = self._select_building_type(main_types)
        
        # Calculate building parameters
        building_count = self._calculate_building_count(selected_type)
        floors = self._calculate_floors(selected_type)
        
        # Create building geometry
        building_type = BuildingType(selected_type, floors, self.site_area)
        
        # Generate buildings
        for i in range(building_count):
            geometry = BuildingGeometry(building_type, tolerance)
            outline = self._generate_building_outline(i, building_count)
            geometry.generate_non_residential_alone_style(outline)
            result.add_building_geometry(geometry)
        
        return result
    
    def _select_building_type(self, available_types: List[str]) -> str:
        """Select appropriate building type based on FAR and density"""
        if not available_types:
            return 'ResidentialLow'
        
        # Simple selection based on FAR
        if self.far < 1.5:
            return available_types[0] if len(available_types) > 0 else 'ResidentialLow'
        elif self.far < 3.0:
            return available_types[1] if len(available_types) > 1 else available_types[0]
        else:
            return available_types[-1]
    
    def _calculate_building_count(self, building_type: str) -> int:
        """Calculate number of buildings needed"""
        params = BuildingDataset.get_building_parameters(building_type)
        target_footprint_area = self.site_area * self.density
        building_footprint = params.area
        
        count = max(1, int(target_footprint_area / building_footprint))
        return min(count, 10)  # Limit to reasonable number
    
    def _calculate_floors(self, building_type: str) -> List[int]:
        """Calculate floor distribution"""
        params = BuildingDataset.get_building_parameters(building_type)
        target_total_area = self.site_area * self.far
        
        # Calculate total floors needed
        total_floors = int(target_total_area / params.area)
        total_floors = max(params.floor_range[0], min(total_floors, params.floor_range[1]))
        
        # Distribute between mixed and main use
        if self.mix_ratio > 0:
            mixed_floors = int(total_floors * self.mix_ratio)
            main_floors = total_floors - mixed_floors
            return [mixed_floors, main_floors]
        else:
            return [0, total_floors]
    
    def _generate_building_outline(self, building_index: int, total_buildings: int) -> List[Point3D]:
        """Generate a simple rectangular building outline"""
        # Simple grid placement
        buildings_per_row = int(math.sqrt(total_buildings)) + 1
        row = building_index // buildings_per_row
        col = building_index % buildings_per_row
        
        # Building dimensions
        width = 20.0
        depth = 15.0
        spacing = 5.0
        
        # Calculate position
        x_offset = col * (width + spacing)
        y_offset = row * (depth + spacing)
        
        # Create rectangular outline
        return [
            Point3D(x_offset, y_offset, 0),
            Point3D(x_offset + width, y_offset, 0),
            Point3D(x_offset + width, y_offset + depth, 0),
            Point3D(x_offset, y_offset + depth, 0)
        ]


class DesignToolbox:
    """Design toolbox class - equivalent to C# DesignToolbox"""
    
    @staticmethod
    def compute_parameters(sites, roads, scores, tolerance):
        """Compute site parameters from input geometry"""
        result = []
        for site in sites:
            params = SiteParameters()
            if isinstance(site, list):
                params.set_site_from_polyline(site)
            result.append(params)
        return result
    
    @staticmethod
    def computing_design(site_parameters_list, city_index, tolerance):
        """Main design computation method"""
        results = []
        
        for site_params in site_parameters_list:
            try:
                # Create design calculator
                site_type = SiteTypes(site_params.site_type)
                calculator = DesignCalculator(
                    site=site_params.site_curve,
                    site_type=site_type,
                    density=site_params.density,
                    far=site_params.site_far,
                    mix_type=site_params.get_mix_type(),
                    mix_ratio=site_params.mix_ratio
                )
                
                # Generate buildings based on site type
                if site_type == SiteTypes.R:
                    result = calculator.calculate_residential_types(
                        city_index=city_index,
                        radiant=site_params.radiant,
                        scores=site_params.scores,
                        style=site_params.building_style,
                        tolerance=tolerance
                    )
                else:
                    result = calculator.calculate_non_residential_types(
                        radiant=site_params.radiant,
                        scores=site_params.scores,
                        tolerance=tolerance,
                        style=site_params.building_style
                    )
                
                results.append(result)
                
            except Exception as e:
                # Create empty result on error
                empty_result = DesignResult(site_params.site_curve, site_params.site_area, "Error")
                results.append(empty_result)
        
        return results
    
    @staticmethod
    def safe_offset_curve(curve, distance, tolerance):
        """Safely offset a curve"""
        # Simplified offset - in practice you'd implement proper curve offsetting
        if isinstance(curve, list):
            # Simple inward/outward scaling for polygon
            center_x = sum(p['x'] for p in curve) / len(curve)
            center_y = sum(p['y'] for p in curve) / len(curve)
            
            offset_curve = []
            scale_factor = max(0.1, 1.0 - distance / 100.0)  # Simplified scaling
            
            for point in curve:
                dx = point['x'] - center_x
                dy = point['y'] - center_y
                new_x = center_x + dx * scale_factor
                new_y = center_y + dy * scale_factor
                offset_curve.append({'x': new_x, 'y': new_y, 'z': point.get('z', 0)})
            
            return True, offset_curve
        
        return False, curve
    
    @staticmethod
    def split_site_by_ratios(site, ratios, priorities, scores, radiant, renew_radiant, tolerance):
        """Split site into subsites based on ratios"""
        # Simplified site splitting - returns the original site for each ratio
        results = []
        for i, ratio in enumerate(ratios):
            # In a full implementation, this would use BSP trees to split the site
            # For now, return scaled versions of the original site
            if isinstance(site, list):
                scale = math.sqrt(ratio)
                scaled_site = []
                center_x = sum(p['x'] for p in site) / len(site)
                center_y = sum(p['y'] for p in site) / len(site)
                
                for point in site:
                    dx = (point['x'] - center_x) * scale
                    dy = (point['y'] - center_y) * scale
                    scaled_site.append({
                        'x': center_x + dx,
                        'y': center_y + dy,
                        'z': point.get('z', 0)
                    })
                results.append(scaled_site)
            else:
                results.append(site)
        
        return results


# Utility functions
class GeometryUtils:
    """Utility functions for geometry operations"""
    
    @staticmethod
    def calculate_polygon_area(points):
        """Calculate polygon area using shoelace formula"""
        if len(points) < 3:
            return 0.0
        
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            if isinstance(points[i], dict):
                area += points[i]['x'] * points[j]['y']
                area -= points[j]['x'] * points[i]['y']
            else:
                area += points[i].x * points[j].y
                area -= points[j].x * points[i].y
        return abs(area) / 2.0
    
    @staticmethod
    def polygon_centroid(points):
        """Calculate polygon centroid"""
        if isinstance(points[0], dict):
            x = sum(p['x'] for p in points) / len(points)
            y = sum(p['y'] for p in points) / len(points)
            z = sum(p.get('z', 0) for p in points) / len(points)
            return {'x': x, 'y': y, 'z': z}
        else:
            x = sum(p.x for p in points) / len(points)
            y = sum(p.y for p in points) / len(points)
            z = sum(p.z for p in points) / len(points)
            return Point3D(x, y, z)
    
    @staticmethod
    def point_in_polygon(point, polygon):
        """Check if point is inside polygon using ray casting"""
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


# Sun calculation utilities
class SunCalculator:
    """Sun calculation utilities - simplified version of C# SunCalculator"""
    
    @staticmethod
    def get_sunlight_distance(height: float, latitude: float = 40.0, 
                            season: str = 'winter') -> float:
        """Calculate minimum distance for sunlight access"""
        # Simplified calculation based on sun angle
        sun_angle_winter = 25.0  # degrees
        sun_angle_summer = 70.0  # degrees
        
        if season == 'winter':
            sun_angle = math.radians(sun_angle_winter)
        else:
            sun_angle = math.radians(sun_angle_summer)
        
        # Adjust for latitude
        latitude_factor = 1.0 + (latitude - 40.0) / 100.0
        
        # Calculate shadow length
        shadow_length = height / math.tan(sun_angle)
        
        return shadow_length * latitude_factor
    
    @staticmethod
    def validate_sun_access(buildings: List[BuildingGeometry], 
                          tolerance: float = 0.1) -> bool:
        """Validate that buildings have adequate sun access"""
        # Simplified validation
        for i, building1 in enumerate(buildings):
            for j, building2 in enumerate(buildings):
                if i != j:
                    # Check distance between buildings
                    # In a full implementation, this would check actual sun angles
                    pass
        return True


# Error handling and validation
class DesignValidation:
    """Validation utilities for design parameters"""
    
    @staticmethod
    def validate_site_parameters(params: SiteParameters) -> List[str]:
        """Validate site parameters and return list of errors"""
        errors = []
        
        if params.density < 0 or params.density > 1:
            errors.append("Density must be between 0 and 1")
        
        if params.site_far < 0 or params.site_far > 10:
            errors.append("FAR must be between 0 and 10")
        
        if params.mix_ratio < 0 or params.mix_ratio > 1:
            errors.append("Mix ratio must be between 0 and 1")
        
        if params.site_area <= 0:
            errors.append("Site area must be positive")
        
        return errors
    
    @staticmethod
    def validate_building_configuration(building_type: BuildingType) -> List[str]:
        """Validate building configuration"""
        errors = []
        
        if sum(building_type.floors) <= 0:
            errors.append("Total floors must be positive")
        
        if building_type.area <= 0:
            errors.append("Building area must be positive")
        
        return errors