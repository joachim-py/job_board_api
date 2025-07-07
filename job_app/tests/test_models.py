import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from job_app.models import User, Company, Job, Application

@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self, user_factory):
        user = user_factory()
        assert User.objects.count() == 1
        assert user.is_active
        assert user.user_type == 'candidate'
        
    def test_user_soft_delete(self, user_factory):
        user = user_factory()
        user.delete()
        assert User.objects.count() == 1
        assert not User.objects.get().is_active
        


@pytest.mark.django_db
class TestCompanyModel:
    def test_company_creation(self, company_factory):
        company = company_factory()
        assert Company.objects.count() == 1
        assert company.name == 'Test Company'
        
    def test_company_name_unique(self, company_factory):
        company1 = company_factory()
        with pytest.raises(Exception):
            company_factory(name=company1.name)

@pytest.mark.django_db
class TestJobModel:
    def test_job_creation(self, job_factory):
        job = job_factory()
        assert Job.objects.count() == 1
        assert job.is_active
        assert job.salary >= 0
        
    def test_job_validation(self, job_factory):
        job = job_factory(salary=-100)
        with pytest.raises(ValidationError):
            job.full_clean()
        
    def test_job_ordering(self, job_factory):
        job1 = job_factory()
        job2 = job_factory()
        assert list(Job.objects.all()) == [job2, job1]

@pytest.mark.django_db
class TestApplicationModel:
    def test_application_creation(self, application_factory):
        app = application_factory()
        assert Application.objects.count() == 1
        assert app.status == 'APP'
        
    def test_unique_application(self, application_factory):
        app = application_factory()
        with pytest.raises(Exception):
            application_factory(candidate=app.candidate, job=app.job)
        
    def test_application_ordering(self, application_factory):
        app1 = application_factory()
        app2 = application_factory()
        assert list(Application.objects.all()) == [app2, app1]
