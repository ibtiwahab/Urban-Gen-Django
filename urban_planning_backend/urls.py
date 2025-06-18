# urban_planning_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('planning_api.urls')),  # API routes
]

# Serve static files during development (equivalent to your FileServer)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    # Serve index.html at root
    from django.views.generic import TemplateView
    urlpatterns.append(path('', TemplateView.as_view(template_name='index.html')))