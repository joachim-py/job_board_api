import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from job_app.models import User, Job, Application

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestJobViews:
    def test_job_list(self, api_client, job_factory):
        for _ in range(3):
            job_factory()
        url = reverse('job-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_job_create(self, api_client, employer_factory):
        employer = employer_factory()
        api_client.force_authenticate(user=employer)
        
        data = {
            'title': 'Test Job',
            'job_type': 'FT',
            'description': 'Test description',
            'location': 'Test Location',
            'salary': 50000,
            'company': employer.company_id
        }
        
        url = reverse('job-list')
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Job.objects.count() == 1

    def test_job_update(self, api_client, employer_factory, job_factory):
        employer = employer_factory()
        job = job_factory(posted_by=employer)
        api_client.force_authenticate(user=employer)
        
        url = reverse('job-detail', args=[job.id])
        data = {'title': 'Updated Title'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert Job.objects.get(id=job.id).title == 'Updated Title'

@pytest.mark.django_db
class TestApplicationViews:
    def test_apply_to_job(self, api_client, user_factory, job_factory):
        candidate = user_factory(user_type='candidate')
        api_client.force_authenticate(user=candidate)
        job = job_factory()
        url = reverse('application-list')
        data = {
            'job': job.id,
            'cover_letter': 'I am interested.'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Application.objects.count() == 1

    def test_duplicate_application(self, api_client, application_factory):
        app = application_factory()
        api_client.force_authenticate(user=app.candidate)
        url = reverse('application-list')
        response = api_client.post(url, {'job': app.job.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
