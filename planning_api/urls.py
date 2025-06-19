# planning_api/urls.py
from django.urls import path
from planning_api.views import GeneratePlanView, GeometryAnalysisView

urlpatterns = [
    path('main/generateplan/', GeneratePlanView.as_view(), name='generate_plan'),
    path('geometry/analyze/', GeometryAnalysisView.as_view(), name='geometry_analysis'),
    # Add other API endpoints here as needed
]