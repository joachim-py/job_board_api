from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

# User model
class User(AbstractUser):
    USER_TYPES = (
        ('employer', 'Employer'),
        ('candidate', 'Candidate'),
        
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True)
    
    def delete(self, *args, **kwargs):
        """Soft delete implementation"""
        self.is_active = False
        self.save()
    
    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email', 'user_type']),
        ]
    def __str__(self):
        return f"{self.email}"

# Company model
class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']
        
    def __str__(self):
        return self.name

# Job model
class Job(models.Model):
    JOB_TYPES = (
        ('FT', 'Full-time'),
        ('PT', 'Part-time'),
        ('INT', 'Internship'),
        ('CON', 'Contract'),
        ('REM', 'Remote'),
    )
    
    title = models.CharField(max_length=100)
    job_type = models.CharField(max_length=3, choices=JOB_TYPES)
    description = models.TextField()
    location = models.CharField(max_length=100)
    salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title', 'job_type', 'location']),
        ]
        
    def __str__(self):
        return f"{self.title} at {self.company.name}"

# Application model
class Application(models.Model):
    STATUS_CHOICES = (
        ('APP', 'Applied'),
        ('REV', 'Under Review'),
        ('INT', 'Interview'),
        ('OFF', 'Offer'),
        ('REJ', 'Rejected'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='APP')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['job', 'candidate']  # Prevent duplicate applications
        ordering = ['-applied_at']
        
    def __str__(self):
        return f"{self.candidate.email} → {self.job.title}"