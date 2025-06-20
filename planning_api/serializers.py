# planning_api/serializers.py - Complete with all required serializers
from rest_framework import serializers

class PlanParametersSerializer(serializers.Serializer):
    site_type = serializers.IntegerField(required=False)
    far = serializers.FloatField(required=False)
    density = serializers.FloatField(required=False)
    mix_ratio = serializers.FloatField(required=False)
    building_style = serializers.IntegerField(required=False)
    orientation = serializers.FloatField(required=False)

class GeneratePlanRequestSerializer(serializers.Serializer):
    plan_flattened_vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False
    )
    plan_parameters = PlanParametersSerializer(required=False)
    
    def validate_plan_flattened_vertices(self, value):
        """Validate that vertices count is divisible by 3 and at least 9 elements"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value

class GeneratePlanResponseSerializer(serializers.Serializer):
    buildingLayersHeights = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        default=list
    )
    buildingLayersVertices = serializers.ListField(
        child=serializers.ListField(
            child=serializers.ListField(child=serializers.FloatField())
        ),
        default=list
    )
    subSiteVertices = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        default=list
    )
    subSiteSetbackVertices = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        default=list
    )

# New serializers for geometry validation
class GeometryValidationSerializer(serializers.Serializer):
    vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="Flattened array of vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    tolerance = serializers.FloatField(default=1e-6, help_text="Validation tolerance")
    check_closure = serializers.BooleanField(default=True, help_text="Check if polygon is closed")
    check_self_intersection = serializers.BooleanField(default=True, help_text="Check for self-intersections")
    check_planarity = serializers.BooleanField(default=True, help_text="Check if polygon is planar")
    
    def validate_vertices(self, value):
        """Validate vertices array"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value


class GeometryValidationResponseSerializer(serializers.Serializer):
    """Serializer for geometry validation responses"""
    is_valid = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField(), default=list)
    warnings = serializers.ListField(child=serializers.CharField(), default=list)
    polygon_area = serializers.FloatField()
    polygon_perimeter = serializers.FloatField()
    is_closed = serializers.BooleanField()
    is_planar = serializers.BooleanField()
    self_intersects = serializers.BooleanField()


class OffsetOperationSerializer(serializers.Serializer):
    """Serializer for polygon offset requests"""
    vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="Flattened array of vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    offset_distance = serializers.FloatField(help_text="Offset distance (positive for inward)")
    offset_type = serializers.ChoiceField(
        choices=['inward', 'outward'],
        default='inward',
        help_text="Direction of offset"
    )
    tolerance = serializers.FloatField(default=1e-6, help_text="Operation tolerance")
    
    def validate_vertices(self, value):
        """Validate vertices array"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value


class OffsetOperationResponseSerializer(serializers.Serializer):
    """Serializer for polygon offset responses"""
    success = serializers.BooleanField()
    offset_vertices = serializers.ListField(
        child=serializers.FloatField(),
        default=list,
        help_text="Flattened array of offset vertices"
    )
    error_message = serializers.CharField(required=False, allow_blank=True)


class IntersectionTestSerializer(serializers.Serializer):
    """Serializer for polygon intersection test requests"""
    polygon_a_vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="First polygon vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    polygon_b_vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="Second polygon vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    tolerance = serializers.FloatField(default=1e-6, help_text="Intersection tolerance")
    
    def validate_polygon_a_vertices(self, value):
        """Validate first polygon vertices"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value
    
    def validate_polygon_b_vertices(self, value):
        """Validate second polygon vertices"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value


class IntersectionTestResponseSerializer(serializers.Serializer):
    """Serializer for polygon intersection test responses"""
    intersects = serializers.BooleanField()
    intersection_type = serializers.ChoiceField(
        choices=[
            'separate', 'overlap', 'a_inside_b', 'b_inside_a', 
            'edge_intersection', 'invalid'
        ],
        default='separate'
    )
    intersection_points = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        default=list,
        help_text="List of intersection points [[x1,y1,z1], [x2,y2,z2], ...]"
    )


class CurveAnalysisSerializer(serializers.Serializer):
    """Serializer for curve analysis requests"""
    vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="Flattened array of vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    operation = serializers.ChoiceField(
        choices=['area', 'length', 'centroid', 'closest_point', 'contains'],
        help_text="Type of analysis to perform"
    )
    test_point = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        help_text="Test point for closest_point or contains operations [x,y,z]"
    )
    tolerance = serializers.FloatField(default=1e-6, help_text="Operation tolerance")
    approx = serializers.BooleanField(default=True, help_text="Allow approximation")
    
    def validate_vertices(self, value):
        """Validate vertices array"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value
    
    def validate_test_point(self, value):
        """Validate test point"""
        if value is not None and len(value) != 3:
            raise serializers.ValidationError("Test point must have exactly 3 coordinates [x,y,z]")
        return value


class CurveAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for curve analysis responses"""
    success = serializers.BooleanField()
    result = serializers.JSONField(help_text="Analysis result (varies by operation type)")
    error_message = serializers.CharField(required=False, allow_blank=True)


class BooleanOperationSerializer(serializers.Serializer):
    """Serializer for boolean operation requests"""
    polygon_a_vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="First polygon vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    polygon_b_vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="Second polygon vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    operation = serializers.ChoiceField(
        choices=['union', 'intersection', 'difference'],
        help_text="Boolean operation type"
    )
    tolerance = serializers.FloatField(default=1e-6, help_text="Operation tolerance")
    approx = serializers.BooleanField(default=True, help_text="Allow approximation")
    
    def validate_polygon_a_vertices(self, value):
        """Validate first polygon vertices"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value
    
    def validate_polygon_b_vertices(self, value):
        """Validate second polygon vertices"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value


class BooleanOperationResponseSerializer(serializers.Serializer):
    """Serializer for boolean operation responses"""
    success = serializers.BooleanField()
    result_polygons = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        default=list,
        help_text="List of result polygons as flattened vertex arrays"
    )
    error_message = serializers.CharField(required=False, allow_blank=True)


class TriangulationSerializer(serializers.Serializer):
    """Serializer for triangulation requests"""
    vertices = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="Flattened array of vertices [x1,y1,z1,x2,y2,z2,...]"
    )
    tolerance = serializers.FloatField(default=1e-6, help_text="Triangulation tolerance")
    
    def validate_vertices(self, value):
        """Validate vertices array"""
        if len(value) % 3 != 0:
            raise serializers.ValidationError("Vertices must be in groups of 3 (x, y, z)")
        if len(value) < 9:
            raise serializers.ValidationError("At least 3 vertices (9 values) required")
        return value


class TriangulationResponseSerializer(serializers.Serializer):
    """Serializer for triangulation responses"""
    success = serializers.BooleanField()
    triangles = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        default=list,
        help_text="List of triangles as flattened vertex arrays [x1,y1,z1,x2,y2,z2,x3,y3,z3]"
    )
    triangle_count = serializers.IntegerField(default=0, help_text="Number of triangles generated")
    error_message = serializers.CharField(required=False, allow_blank=True)


class LineOperationSerializer(serializers.Serializer):
    """Serializer for line operation requests"""
    line_start = serializers.ListField(
        child=serializers.FloatField(),
        help_text="Line start point [x,y,z]"
    )
    line_end = serializers.ListField(
        child=serializers.FloatField(),
        help_text="Line end point [x,y,z]"
    )
    operation = serializers.ChoiceField(
        choices=['length', 'direction', 'midpoint', 'offset', 'project'],
        help_text="Type of line operation"
    )
    direction_point = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        help_text="Direction point for offset operation [x,y,z]"
    )
    distance = serializers.FloatField(required=False, help_text="Distance for offset operation")
    target_plane = serializers.DictField(required=False, help_text="Target plane for projection")
    
    def validate_line_start(self, value):
        """Validate line start point"""
        if len(value) != 3:
            raise serializers.ValidationError("Line start must have exactly 3 coordinates [x,y,z]")
        return value
    
    def validate_line_end(self, value):
        """Validate line end point"""
        if len(value) != 3:
            raise serializers.ValidationError("Line end must have exactly 3 coordinates [x,y,z]")
        return value
    
    def validate_direction_point(self, value):
        """Validate direction point"""
        if value is not None and len(value) != 3:
            raise serializers.ValidationError("Direction point must have exactly 3 coordinates [x,y,z]")
        return value


class LineOperationResponseSerializer(serializers.Serializer):
    """Serializer for line operation responses"""
    success = serializers.BooleanField()
    result = serializers.JSONField(help_text="Operation result (varies by operation type)")
    error_message = serializers.CharField(required=False, allow_blank=True)