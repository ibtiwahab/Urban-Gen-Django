# planning_api/urls.py
from django.urls import path
from planning_api.views import *

urlpatterns = [
    path('main/generateplan/', GeneratePlanView.as_view(), name='generate_plan'),
    # Add other API endpoints here as needed
]