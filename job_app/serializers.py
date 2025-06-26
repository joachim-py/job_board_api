from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Company, Job, Application

# User Serializers
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    email = serializers.EmailField(required=True)
    user_type = serializers.ChoiceField(
        choices=User.USER_TYPES, 
        required=True
    )
    
    class Meta:
        model = User
        fields = ['email', 'password', 'user_type', 'first_name', 'last_name', 'phone']
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            password=make_password(validated_data['password']),
            user_type=validated_data['user_type'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', '')
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'user_type']
        read_only_fields = ['id', 'email', 'user_type']

# Company Serializers
class CompanySerializer(serializers.ModelSerializer):
    jobs_count = serializers.IntegerField(source='jobs.count', read_only=True)
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'website', 'logo', 'jobs_count']
        read_only_fields = ['id']

    def validate_name(self, value):
        """Case-insensitive uniqueness check"""
        if Company.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value

# Nested serializers for job details
class EmployerDetailSerializer(serializers.ModelSerializer):
    """Serializer for employer information in job listings"""
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'first_name', 'last_name', 'email']

class CompanyDetailSerializer(serializers.ModelSerializer):
    """Serializer for company information in job listings"""
    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'website', 'logo']
        read_only_fields = ['id', 'name', 'description', 'website', 'logo']

# Job Serializers
class JobListSerializer(serializers.ModelSerializer):
    company = CompanyDetailSerializer(read_only=True)
    posted_by = EmployerDetailSerializer(read_only=True)
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    applications_count = serializers.IntegerField(source='applications.count', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'job_type', 'job_type_display', 
            'location', 'salary', 'company', 'posted_by', 
            'applications_count', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'posted_by']

class JobDetailSerializer(JobListSerializer):
    """Extended job serializer with full details"""
    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + [
            'description', 'updated_at'
        ]
        read_only_fields = JobListSerializer.Meta.read_only_fields + ['updated_at']

class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating jobs (without nested objects)"""
    class Meta:
        model = Job
        fields = [
            'title', 'job_type', 'description', 'location', 
            'salary', 'company', 'is_active'
        ]
    
    def validate_company(self, value):
        """Ensure the user can only post jobs for their own company"""
        request = self.context.get('request')
        if request and request.user.company != value:
            raise serializers.ValidationError("You can only post jobs for your own company.")
        return value

# Application Serializers
class ApplicationListSerializer(serializers.ModelSerializer):
    """Application serializer with nested job and candidate details"""
    job = JobListSerializer(read_only=True)
    candidate = UserProfileSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'job', 'candidate', 'cover_letter', 
            'status', 'status_display', 'applied_at'
        ]
        read_only_fields = ['id', 'applied_at', 'job', 'candidate']

class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications"""
    class Meta:
        model = Application
        fields = ['job', 'cover_letter']
    
    def validate_job(self, value):
        """Validation for job applications"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("No user in request context")
        
        # Ensure candidates can't apply to their own jobs
        if value.posted_by == request.user:
            raise serializers.ValidationError("You cannot apply to your own job posting.")
        
        # Ensure job is active
        if not value.is_active:
            raise serializers.ValidationError("This job posting is no longer active.")
        
        # Check for duplicate applications
        if Application.objects.filter(job=value, candidate=request.user).exists():
            raise serializers.ValidationError("You have already applied to this job.")
        
        return value

class ApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating application status (employer use)"""
    class Meta:
        model = Application
        fields = ['status']
    
    def validate_status(self, value):
        """Ensure only valid status transitions"""
        instance = self.instance
        if instance and instance.status == 'REJ' and value != 'REJ':
            raise serializers.ValidationError("Cannot change status of rejected application.")
        return value