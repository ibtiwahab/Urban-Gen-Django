# planning_api/apps.py
from django.apps import AppConfig


class PlanningApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planning_api'
    verbose_name = 'Urban Planning API'
    
    def ready(self):
        """Initialize the app when Django starts"""
        # Import urban design modules to ensure they're loaded
        try:
            from . import urban_design
            print("Urban Design modules loaded successfully")
        except ImportError as e:
            print(f"Warning: Could not load urban design modules: {e}")