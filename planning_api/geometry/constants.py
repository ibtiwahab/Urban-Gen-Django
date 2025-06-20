# planning_api/geometry/constants.py
"""
Constants for geometry operations
"""

class Constants:
    """Constants used throughout the geometry package"""
    TOLERANCE = 1e-8  # 0.00000001
    DEFAULT_TOLERANCE = 1e-6
    
    # Angle constants
    PI = 3.141592653589793
    TWO_PI = 2 * PI
    HALF_PI = PI / 2
    
    # Distance constants
    MIN_DISTANCE = 1e-10
    MAX_DISTANCE = 1e10
    
    # Iteration limits
    MAX_ITERATIONS = 1000
    MAX_SUBDIVISION_COUNT = 100