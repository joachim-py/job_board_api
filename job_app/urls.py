from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from .views import (
    UserViewSet,
    CompanyViewSet,
    JobViewSet,
    ApplicationViewSet,
)

# Initialize Router
router = DefaultRouter()
# router = DefaultRouter(trailing_slash=False)

# Register ViewSets
router.register(r'users', UserViewSet, basename='user')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')

# Versioned URL Patterns
urlpatterns = [
    # API v1 
    path('', include(router.urls)),
    
    # Health Check
    path('health/', lambda request: JsonResponse({'status': 'ok'})),
]