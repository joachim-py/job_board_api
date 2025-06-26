# management/commands/seed_companies.py
from django.core.management.base import BaseCommand
from job_app.models import Company
from faker import Faker
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Seeds the database with realistic companies'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()
        self.industries = [
            "Technology", "Finance", "Healthcare", 
            "Manufacturing", "Retail", "Education"
        ]

    def handle(self, *args, **options):
        self.stdout.write("Seeding companies...")
        
        # Create media directory if it doesn't exist
        logo_dir = os.path.join(settings.MEDIA_ROOT, 'company_logos')
        os.makedirs(logo_dir, exist_ok=True)
        
        for i in range(20):  # Generate 20 companies
            company = self.create_company(i)
            self.stdout.write(f"Created {company.name}")
            
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded 20 companies')
        )

    def create_company(self, index):
        # Generate realistic company description
        industry = self.fake.random_element(self.industries)
        description = (
            f"{self.fake.catch_phrase()}. "
            f"Specializing in {industry.lower()} solutions with offices in "
            f"{self.fake.city()}, {self.fake.country()}. "
            f"{self.fake.paragraph()}"
        )
        
        # Create the company
        return Company.objects.create(
            name=self.fake.unique.company(),
            description=description,
            website=f"https://{self.fake.domain_name()}",
            # For actual logo files, you would need to create them
            # This just generates a path string
            logo=f"company_logos/logo_{index}.png" if self.fake.boolean(50) else None
        )