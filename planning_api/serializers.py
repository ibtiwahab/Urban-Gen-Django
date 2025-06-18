# planning_api/serializers.py
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