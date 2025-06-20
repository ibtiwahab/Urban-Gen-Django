# planning_api/geometry/vector3d_addon.py
import math
from .utils import Vector3D
from .constants import Constants


class Vector3DAddOn:
    """Enhanced Vector3D operations similar to C# Vector3dAddOn"""
    
    @staticmethod
    def is_parallel_to(vector1: Vector3D, vector2: Vector3D) -> int:
        """
        Check if two vectors are parallel
        Returns:
            0 - not parallel
            1 - parallel same direction
            -1 - parallel opposite direction
        """
        if vector1 is None:
            raise ValueError("First vector is null")
        if vector2 is None:
            raise ValueError("Second vector is null")
        
        if vector1.length() == 0 or vector2.length() == 0:
            return 0
        
        # Normalize vectors
        v1 = vector1.normalize()
        v2 = vector2.normalize()
        
        # Check if same direction
        x_diff = abs(v1.x - v2.x)
        y_diff = abs(v1.y - v2.y)
        z_diff = abs(v1.z - v2.z)
        
        if (x_diff <= Constants.TOLERANCE and 
            y_diff <= Constants.TOLERANCE and 
            z_diff <= Constants.TOLERANCE):
            return 1
        
        # Check if opposite direction
        x_diff = abs(v1.x + v2.x)
        y_diff = abs(v1.y + v2.y)
        z_diff = abs(v1.z + v2.z)
        
        if (x_diff <= Constants.TOLERANCE and 
            y_diff <= Constants.TOLERANCE and 
            z_diff <= Constants.TOLERANCE):
            return -1
        
        return 0
    
    @staticmethod
    def rotate(vector: Vector3D, angle: float, axis: Vector3D) -> Vector3D:
        """
        Rotate vector around axis by angle (in radians)
        Uses Rodrigues' rotation formula
        """
        if vector is None:
            raise ValueError("Vector is null")
        if axis is None:
            raise ValueError("Axis is null")
        
        if axis.length() == 0:
            return Vector3D(vector.x, vector.y, vector.z)
        
        # Normalize axis
        k = axis.normalize()
        
        # Rodrigues' rotation formula
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        
        # v_rot = v*cos(θ) + (k × v)*sin(θ) + k*(k·v)*(1-cos(θ))
        k_cross_v = k.cross(vector)
        k_dot_v = k.dot(vector)
        
        rotated = Vector3D(
            vector.x * cos_angle + k_cross_v.x * sin_angle + k.x * k_dot_v * (1 - cos_angle),
            vector.y * cos_angle + k_cross_v.y * sin_angle + k.y * k_dot_v * (1 - cos_angle),
            vector.z * cos_angle + k_cross_v.z * sin_angle + k.z * k_dot_v * (1 - cos_angle)
        )
        
        return rotated