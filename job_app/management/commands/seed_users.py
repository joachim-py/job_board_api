# management/commands/seed_users.py
from django.core.management.base import BaseCommand
from job_app.models import User, Company
from faker import Faker
import os, random
from django.conf import settings
from django.core.files import File
from io import BytesIO
import requests

class Command(BaseCommand):
    help = 'Seeds the database with 50 candidates and 50 employers'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()
        self.candidate_skills = [
            'Python', 'Django', 'JavaScript', 'React', 'AWS',
            'Docker', 'PostgreSQL', 'Machine Learning', 'DevOps',
            'Flask', 'FastAPI', 'Vue.js', 'Angular', 'Node.js'
        ]
        
    def handle(self, *args, **options):
        self.stdout.write("Seeding users...")
        
        # Create media directories
        self.create_media_dirs()
        
        # Get all companies
        companies = list(Company.objects.all())
        
        if not companies:
            self.stdout.write(self.style.ERROR('No companies found. Run seed_companies first.'))
            return
            
        # Seed 50 employers
        for i in range(50):
            user = self.create_user(
                user_type='employer',
                company=companies[i % len(companies)],  # Distribute across companies
                is_staff=False
            )
            self.stdout.write(f"Created employer: {user.email}")
        
        # Seed 50 candidates
        for i in range(50):
            user = self.create_user(
                user_type='candidate',
                company=None,
                is_staff=False
            )
            self.stdout.write(f"Created candidate: {user.email}")
            
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded 100 users (50 employers, 50 candidates)')
        )
    
    def create_media_dirs(self):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'resumes'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'profile_pics'), exist_ok=True)
    
    def create_user(self, user_type, company, is_staff):
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password='testpass123',  # Default password for all seeded users
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            company=company,
            is_staff=is_staff
        )
        
        # Add candidate-specific fields
        if user_type == 'candidate':
            user.phone = self.fake.phone_number()[:15]
            
            # Add mock resume (30% chance)
            if self.fake.boolean(30):
                self.add_mock_resume(user)
        
        return user
    
    def add_mock_resume(self, user):
        try:
            # Generate a mock PDF resume text
            resume_content = f"""
            {user.get_full_name()}
            {user.email} | {user.phone}
            
            SUMMARY
            {self.fake.paragraph()}
            
            SKILLS
            {', '.join(random.sample(self.candidate_skills, random.randint(3, 6)))}
            
            EXPERIENCE
            {self.fake.job()} at {self.fake.company()} ({self.fake.date()})
            - {self.fake.sentence()}
            - {self.fake.sentence()}
            
            EDUCATION
            {self.fake.university()} - {self.fake.word().title()} Degree
            """
            
            # Create a mock file
            from tempfile import NamedTemporaryFile
            with NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
                tmp.write(resume_content.encode('utf-8'))
                tmp.flush()
                user.resume.save(
                    f"resume_{user.id}.txt",
                    File(open(tmp.name, 'rb'))
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Couldn't create resume for {user.email}: {str(e)}"))