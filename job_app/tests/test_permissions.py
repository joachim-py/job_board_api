import pytest
from rest_framework import permissions
from job_app.permissions import (
    IsEmployerOrReadOnly,
    IsCandidateForApplications,
    IsSelfOrAdmin as IsSelfOrAdminPermission,
)
from job_app.models import User

@pytest.mark.django_db
class TestIsEmployerOrReadOnlyPermission:
    def test_has_permission_employer(self, employer_factory, rf):
        employer = employer_factory()
        permission = IsEmployerOrReadOnly()
        request = rf.get('/')
        request.user = employer
        assert permission.has_permission(request, view=None)

    def test_has_permission_candidate(self, user_factory, rf):
        candidate = user_factory(user_type='candidate')
        permission = IsEmployerOrReadOnly()
        request = rf.get('/')
        request.user = candidate
        assert not permission.has_permission(request, view=None)

@pytest.mark.django_db
class TestIsCandidateForApplicationsPermission:
    def test_has_permission_candidate(self, user_factory, rf):
        candidate = user_factory(user_type='candidate')
        permission = IsCandidateForApplications()
        request = rf.get('/')
        request.user = candidate
        assert permission.has_permission(request, view=None)

    def test_has_permission_employer(self, employer_factory, rf):
        employer = employer_factory()
        permission = IsCandidateForApplications()
        request = rf.get('/')
        request.user = employer
        assert not permission.has_permission(request, view=None)

@pytest.mark.django_db
class TestIsSelfOrAdminPermission:
    def test_has_object_permission_self(self, user_factory):
        user = user_factory()
        permission = IsSelfOrAdminPermission()
        request = type('req', (), {'user': user, 'method': 'GET'})
        assert permission.has_object_permission(request, view=None, obj=user)

    def test_has_object_permission_admin(self, user_factory):
        admin = user_factory(is_staff=True)
        other_user = user_factory()
        permission = IsSelfOrAdminPermission()
        request = type('req', (), {'user': admin, 'method': 'GET'})
        assert permission.has_object_permission(request, view=None, obj=other_user)

    def test_has_object_permission_other(self, user_factory):
        user1 = user_factory()
        user2 = user_factory()
        permission = IsSelfOrAdminPermission()
        request = type('req', (), {'user': user1, 'method': 'GET'})
        assert not permission.has_object_permission(request, view=None, obj=user2)
