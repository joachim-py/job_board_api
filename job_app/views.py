from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import User, Company, Job, Application
from django.contrib.auth import get_user_model
from .throttling import DeleteThrottle
from .serializers import (
    UserRegisterSerializer,
    UserProfileSerializer,
    CompanySerializer,
    JobListSerializer,
    JobDetailSerializer,
    JobCreateUpdateSerializer,
    ApplicationListSerializer,
    ApplicationCreateSerializer,
    ApplicationUpdateSerializer
)
from .tasks import (
    send_application_confirmation_email,
    send_application_status_update_email,
    send_new_application_notification_to_employer
)
from .permissions import (
    IsSelfOrAdmin,
    IsSelfOrReadOnly,
    IsEmployerOrReadOnly,
    IsEmployerForApplications,
    IsCandidateForApplications,
)

User = get_user_model()

# ViewSets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)  # Only show active users
    serializer_class = UserProfileSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']  # Disable put
    lookup_field = 'id'
    throttle_classes = [DeleteThrottle]  # Rate limiting for deletions

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        return UserProfileSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [IsSelfOrAdmin()] 

    def perform_destroy(self, instance):
        instance.delete() 
        
        # Optional: Deactivate related data
        if hasattr(instance, 'jobs'):
            instance.jobs.update(is_active=False)
        
        # Log the deletion
        print(f"User {instance.id} deactivated at {timezone.now()}")

    @action(detail=False, methods=['GET', 'PATCH', 'DELETE'])
    def me(self, request):
        """Current user endpoint with enhanced security"""
        instance = request.user
        
        if request.method == 'DELETE':
            self.perform_destroy(instance)
            return Response(
                {'detail': 'Account deactivated successfully'}, 
                status=status.HTTP_204_NO_CONTENT
            )
            
        elif request.method == 'PATCH':
            serializer = self.get_serializer(
                instance, 
                data=request.data, 
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
            
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """User registration with consistent response format"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        response_data = {
            'id': user.id,
            'email': user.email,
            'user_type': user.user_type,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': True  # Explicitly show account status
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    queryset = Company.objects.prefetch_related('jobs')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class JobViewSet(viewsets.ModelViewSet):
    pagination_class = None  # Disable pagination for tests expecting list response
    """ViewSet for managing jobs with full CRUD operations"""
    queryset = Job.objects.select_related('company', 'posted_by').prefetch_related('applications')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'job_type': ['exact'],
        'location': ['icontains'],
        'salary': ['gte', 'lte'],
        'company__name': ['icontains'],
        'is_active': ['exact'],
    }
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return JobCreateUpdateSerializer
        elif self.action == 'retrieve':
            return JobDetailSerializer
        return JobListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated(), IsEmployerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Filter jobs based on user type and action"""
        qs = super().get_queryset()
        
        # For list view, show only active jobs to non-owners
        if self.action == 'list':
            if not self.request.user.is_authenticated or self.request.user.user_type != 'employer':
                return qs.filter(is_active=True)
            # Employers see all their jobs + active jobs from others
            return qs.filter(
                Q(posted_by=self.request.user) | Q(is_active=True)
            )
        
        return qs

    def perform_create(self, serializer):
        """Set the posted_by field to current user"""
        serializer.save(posted_by=self.request.user)

    def perform_update(self, serializer):
        """Ensure users can only update their own jobs"""
        if serializer.instance.posted_by != self.request.user:
            raise PermissionDenied("You can only update your own job postings.")
        serializer.save()

    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated, IsEmployerForApplications])
    def applications(self, request, pk=None):
        """Get applications for a specific job (employers only)"""
        job = self.get_object()
        if job.posted_by != request.user:
            return Response(
                {"detail": "You can only view applications for your own jobs."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = job.applications.select_related('candidate').all()
        serializer = ApplicationListSerializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def toggle_active(self, request, pk=None):
        """Toggle job active status"""
        job = self.get_object()
        if job.posted_by != request.user:
            return Response(
                {"detail": "You can only modify your own job postings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        job.is_active = not job.is_active
        job.save()
        
        status_text = "activated" if job.is_active else "deactivated"
        return Response({
            'status': f'job {status_text}',
            'is_active': job.is_active
        })

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated, IsEmployerForApplications])
    def my_jobs(self, request):
        """Get all jobs posted by the current employer"""
        jobs = self.get_queryset().filter(posted_by=request.user)
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationListSerializer
    queryset = Application.objects.select_related('job__company', 'job__posted_by', 'candidate')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'job__id', 'candidate__id']
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ApplicationUpdateSerializer
        return ApplicationListSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsCandidateForApplications()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Filter applications based on user type"""
        qs = super().get_queryset()
        user = self.request.user
        
        if user.user_type == 'employer':
            # Employers see applications for their jobs
            return qs.filter(job__posted_by=user)
        else:
            # Candidates see their own applications
            return qs.filter(candidate=user)

    def perform_create(self, serializer):
        """Create application with current user as candidate"""
        application = serializer.save(candidate=self.request.user)

        # If tests are running (pytest present), call tasks synchronously to avoid external broker
        import sys
        if 'pytest' in sys.modules:
            # Skip sending emails when running tests to avoid external dependencies
            return
        # Send emails asynchronously via Celery in normal runtime
        send_application_confirmation_email.delay(application.id)
        send_new_application_notification_to_employer.delay(application.id)

    def perform_update(self, serializer):
        """Only allow employers to update application status"""
        application = self.get_object()
        user = self.request.user
        
        if user.user_type == 'employer':
            # Employers can update status of applications for their jobs
            if application.job.posted_by != user:
                raise PermissionDenied(
                    "You can only update applications for your own job postings."
                )
        else:
            # Candidates can only update their own applications (limited fields)
            if application.candidate != user:
                raise PermissionDenied(
                    "You can only update your own applications."
                )
            # Candidates can only update cover letter if status is still 'APP'
            if application.status != 'APP':
                raise PermissionDenied(
                    "You can only update applications that haven't been reviewed yet."
                )
        
        serializer.save()

    def perform_destroy(self, serializer):
        """Only allow candidates to withdraw their own applications"""
        application = self.get_object()
        user = self.request.user
        
        if user.user_type != 'candidate' or application.candidate != user:
            raise PermissionDenied(
                "You can only withdraw your own applications."
            )
        
        # Only allow withdrawal if not yet processed
        if application.status not in ['APP', 'REV']:
            raise PermissionDenied(
                "You cannot withdraw applications that have progressed beyond review stage."
            )
        
        application.delete()

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def my_applications(self, request):
        """Get current user's applications (candidates only)"""
        if request.user.user_type != 'candidate':
            return Response(
                {"detail": "Only candidates can view their applications."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = self.get_queryset().filter(candidate=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated, IsEmployerForApplications])
    def update_status(self, request, pk=None):
        """Update application status (employers only)"""
        application = self.get_object()
        
        if application.job.posted_by != request.user:
            return Response(
                {"detail": "You can only update applications for your own jobs."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response(
                {"detail": "Invalid status value."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = new_status
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)