from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from job_app.models import User, Company, Job, Application

# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'company', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined', 'company')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    # Customize the fieldsets for add/edit forms
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'resume', 'company'),
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'company'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')

# Company Admin
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'jobs_count', 'logo_preview')
    search_fields = ('name', 'description')
    list_filter = ('name',)
    ordering = ('name',)
    
    def jobs_count(self, obj):
        """Display count of jobs for this company"""
        count = obj.jobs.count()
        if count > 0:
            url = reverse('admin:job_app_job_changelist') + f'?company__id__exact={obj.id}'
            return format_html('<a href="{}">{} jobs</a>', url, count)
        return '0 jobs'
    jobs_count.short_description = 'Jobs Posted'
    
    def logo_preview(self, obj):
        """Display logo preview in admin"""
        if obj.logo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                obj.logo.url
            )
        return '-'
    logo_preview.short_description = 'Logo'

# Job Admin
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'location', 'salary', 'is_active', 'applications_count', 'posted_by', 'created_at')
    list_filter = ('job_type', 'is_active', 'created_at', 'company', 'location')
    search_fields = ('title', 'description', 'location', 'company__name', 'posted_by__email')
    readonly_fields = ('created_at', 'updated_at', 'applications_count')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'job_type', 'description', 'location', 'salary')
        }),
        ('Company & Employer', {
            'fields': ('company', 'posted_by')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def applications_count(self, obj):
        """Display count of applications for this job"""
        count = obj.applications.count()
        if count > 0:
            url = reverse('admin:job_app_application_changelist') + f'?job__id__exact={obj.id}'
            return format_html('<a href="{}">{} applications</a>', url, count)
        return '0 applications'
    applications_count.short_description = 'Applications'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'posted_by')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "posted_by":
            kwargs["queryset"] = User.objects.filter(user_type='employer')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Application Admin  
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate_name', 'job_title', 'company_name', 'status', 'applied_at')
    list_filter = ('status', 'applied_at', 'job__company', 'job__job_type')
    search_fields = ('candidate__email', 'candidate__first_name', 'candidate__last_name', 'job__title', 'job__company__name')
    readonly_fields = ('applied_at',)
    ordering = ('-applied_at',)
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job', 'candidate', 'cover_letter', 'status')
        }),
        ('Timeline', {
            'fields': ('applied_at',),
            'classes': ('collapse',)
        }),
    )
    
    def candidate_name(self, obj):
        """Display candidate's full name"""
        return f"{obj.candidate.first_name} {obj.candidate.last_name}" if obj.candidate.first_name else obj.candidate.email
    candidate_name.short_description = 'Candidate'
    candidate_name.admin_order_field = 'candidate__first_name'
    
    def job_title(self, obj):
        """Display job title with link"""
        url = reverse('admin:job_app_job_change', args=[obj.job.id])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_title.short_description = 'Job'
    job_title.admin_order_field = 'job__title'
    
    def company_name(self, obj):
        """Display company name"""
        return obj.job.company.name
    company_name.short_description = 'Company'
    company_name.admin_order_field = 'job__company__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job__company', 'candidate')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "candidate":
            kwargs["queryset"] = User.objects.filter(user_type='candidate')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Customize admin site headers
admin.site.site_header = "Job Board Administration"
admin.site.site_title = "Job Board Admin"
admin.site.index_title = "Welcome to Job Board Administration"

# Custom admin actions
@admin.action(description='Activate selected jobs')
def make_jobs_active(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description='Deactivate selected jobs')
def make_jobs_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.action(description='Mark applications as reviewed')
def mark_applications_reviewed(modeladmin, request, queryset):
    queryset.update(status='REV')

# Add custom actions to respective admins
JobAdmin.actions = [make_jobs_active, make_jobs_inactive]
ApplicationAdmin.actions = [mark_applications_reviewed]