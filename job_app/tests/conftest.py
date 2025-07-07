import pytest
from django.contrib.auth import get_user_model
from job_app.models import Company, Job, Application

from uuid import uuid4


@pytest.fixture
def user_factory():
    def create_user(**kwargs):
        defaults = {
            'username': f"testuser_{uuid4().hex[:8]}",
            'email': f"test_{uuid4().hex[:8]}@example.com",
            'password': 'testpassword',
            'user_type': 'candidate'
        }
        defaults.update(kwargs)
        return get_user_model().objects.create_user(**defaults)
    return create_user

@pytest.fixture
def employer_factory(user_factory, company_factory):
    def create_employer(**kwargs):
        defaults = {
            'user_type': 'employer'
        }
        defaults.update(kwargs)
        employer = user_factory(**defaults)
        # Ensure employer has an associated company
        if employer.company is None:
            employer.company = company_factory()
            employer.save()
        return employer
    return create_employer

@pytest.fixture
def company_factory():
    def create_company(**kwargs):
        defaults = {
            'name': 'Test Company',
            'description': 'Test company description'
        }
        # Ensure uniqueness in case 'Test Company' already exists
        if Company.objects.filter(name=defaults['name']).exists():
            defaults['name'] = f"Test Company {uuid4().hex[:8]}"
        defaults.update(kwargs)
        return Company.objects.create(**defaults)
    return create_company

@pytest.fixture
def job_factory(user_factory, company_factory):
    def create_job(**kwargs):
        defaults = {
            'title': 'Test Job',
            'job_type': 'FT',
            'description': 'Test job description',
            'location': 'Test Location',
            'salary': 50000,
            'posted_by': user_factory(user_type='employer')
        }
        if 'company' not in kwargs:
            defaults['company'] = company_factory()
        defaults.update(kwargs)
        return Job.objects.create(**defaults)
    return create_job

@pytest.fixture
def application_factory(user_factory, job_factory):
    def create_application(**kwargs):
        defaults = {
            'candidate': user_factory(user_type='candidate'),
            'job': job_factory()
        }
        defaults.update(kwargs)
        return Application.objects.create(**defaults)
    return create_application
