from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.http import JsonResponse

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# API Health Check
def api_health_check(request):
    return JsonResponse({
        'status': 'ok',
        'version': 'v1',
        'message': 'Job Board API is running'
    })

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    
    # API Health Check (Root level)
    path('api/health/', api_health_check, name='api_health'),
    
    # API URLs (versioned)
    path('api/v1/', include('job_app.urls')),
    
    # Authentication Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),    
        
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Catch-all for undefined API routes
    path('', lambda request: JsonResponse({
        'error': 'API endpoint not found',
        'available_endpoints': [
            '/api/v1/ - Main API endpoints',
            '/api/token/ - Authentication endpoints', 
            '/api/schema/ - API schema',
            '/api/health/ - Health check'
        ]
    }, status=404)),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Development URL patterns (only in DEBUG mode)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns