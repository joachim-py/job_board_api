# management/commands/seed_jobs.py
from django.core.management.base import BaseCommand
from job_app.models import Job, Company, User
from faker import Faker
import random
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seeds the database with realistic job postings'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()
        self.tech_skills = [
            'Python', 'Django', 'JavaScript', 'React', 'AWS',
            'Docker', 'PostgreSQL', 'Machine Learning', 'DevOps'
        ]
        
    def handle(self, *args, **options):
        self.stdout.write("Seeding jobs...")
        
        # Get all companies and users
        companies = Company.objects.all()
        users = User.objects.filter(user_type='employer')
        
        if not companies.exists():
            self.stdout.write(self.style.ERROR('No companies found. Run seed_companies first.'))
            return
            
        if not users.exists():
            self.stdout.write(self.style.ERROR('No employer users found. Create some users first.'))
            return
            
        for i in range(50):  # Generate 50 jobs
            job = self.create_job(
                company=random.choice(companies),
                posted_by=random.choice(users)
            )
            self.stdout.write(f"Created {job.title} at {job.company.name}")
            
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded 50 job postings')
        )
    
    def create_job(self, company, posted_by):
        # Generate job-specific data
        job_type = random.choice(['FT', 'PT', 'INT', 'CON', 'REM'])
        title = self.generate_job_title()
        description = self.generate_job_description()
        
        # Salary based on position and type
        base_salary = self.get_base_salary(job_type, title)
        salary = Decimal(random.randint(
            int(base_salary * 0.9),  # 10% below base
            int(base_salary * 1.1)   # 10% above base
        ))
        
        return Job.objects.create(
            title=title,
            job_type=job_type,
            description=description,
            location=self.get_location(job_type, company),
            salary=salary,
            company=company,
            posted_by=posted_by,
            is_active=random.choices([True, False], weights=[80, 20])[0]
        )
    
    def generate_job_title(self):
        levels = ['Junior', 'Mid-level', 'Senior', 'Lead', 'Principal']
        specialties = ['Backend', 'Frontend', 'Full Stack', 'DevOps', 'Data']
        return f"{random.choice(levels)} {random.choice(specialties)} Developer"
    
    def generate_job_description(self):
        requirements = "\n".join(
            f"- {random.choice(self.tech_skills)} experience" 
            for _ in range(random.randint(3, 6))
        )
        
        return (
            f"## About the Role\n{self.fake.paragraph()}\n\n"
            f"## Requirements\n{requirements}\n\n"
            f"## Benefits\n{self.fake.paragraph()}"
        )
    
    def get_base_salary(self, job_type, title):
        """Return appropriate base salary based on role"""
        level_multiplier = 1.0
        if 'Junior' in title:
            level_multiplier = 0.7
        elif 'Senior' in title or 'Lead' in title or 'Principal' in title:
            level_multiplier = 1.5
            
        type_multiplier = {
            'FT': 1.0,
            'PT': 0.6,
            'INT': 0.4,
            'CON': 1.2,
            'REM': 1.1
        }.get(job_type, 1.0)
        
        return 50000 * level_multiplier * type_multiplier
    
    def get_location(self, job_type, company):
        if job_type == 'REM':
            return "Remote"
        return f"{company.name.split()[0]} {self.fake.city()}"  # e.g., "Google Berlin"