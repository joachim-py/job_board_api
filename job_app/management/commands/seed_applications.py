# management/commands/seed_applications.py
from django.core.management.base import BaseCommand
from job_app.models import Application, Job, User
from faker import Faker
import random
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seeds the database with realistic job applications'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()
        
    def handle(self, *args, **options):
        self.stdout.write("Seeding applications...")
        
        # Get active jobs and candidates
        jobs = Job.objects.filter(is_active=True)
        candidates = User.objects.filter(user_type='candidate')
        
        if not jobs.exists():
            self.stdout.write(self.style.ERROR('No active jobs found. Run seed_jobs first.'))
            return
            
        if not candidates.exists():
            self.stdout.write(self.style.ERROR('No candidates found. Run seed_users first.'))
            return
            
        applications_created = 0
        
        # Each candidate applies to 3-10 jobs
        for candidate in candidates:
            num_applications = random.randint(3, 10)
            jobs_to_apply = random.sample(list(jobs), num_applications)
            
            for job in jobs_to_apply:
                # Ensure candidate doesn't apply to their own company's jobs
                if job.posted_by.company != candidate.company:
                    self.create_application(job, candidate)
                    applications_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {applications_created} applications')
        )
    
    def create_application(self, job, candidate):
        # Determine application status with weighted probabilities
        status = random.choices(
            ['APP', 'REV', 'INT', 'OFF', 'REJ'],
            weights=[40, 30, 15, 5, 10]  # 40% Applied, 30% Review, etc.
        )[0]
        
        # Generate realistic application dates (within job posting timeframe)
        days_since_posted = (timezone.now() - job.created_at).days
        applied_at = job.created_at + timedelta(
            days=random.randint(0, min(days_since_posted, 30))
        )
        
        # Create the application with historical timestamp
        application = Application.objects.create(
            job=job,
            candidate=candidate,
            cover_letter=self.generate_cover_letter(job, candidate),
            status=status,
            applied_at=applied_at
        )
        
        # Update status timestamps realistically
        self.update_application_status(application)
        
        self.stdout.write(
            f"{candidate.email} applied to {job.title} ({status})"
        )
    
    def generate_cover_letter(self, job, candidate):
        return f"""
Dear Hiring Manager,

I'm excited to apply for the {job.title} position at {job.company.name}. 
{self.fake.paragraph()}

My skills in {random.choice(['Python', 'Django', 'JavaScript', 'React'])} align well with your requirements. 
{self.fake.paragraph()}

{self.fake.paragraph()}

Sincerely,
{candidate.get_full_name()}
"""
    
    def update_application_status(self, application):
        """Simulate realistic status progression"""
        if application.status in ['REV', 'INT', 'OFF']:
            application.status_updated_at = application.applied_at + timedelta(
                days=random.randint(2, 7)
            )
            application.save()
        
        if application.status in ['INT', 'OFF']:
            # Create interview records if needed
            pass
        
        if application.status == 'OFF':
            # Add offer details if needed
            pass