from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSelfOrAdmin(BasePermission):
    """
        Full access to admins (is_staff=True)
        Users to access their own data
        Read-only access to others
    """
    def has_permission(self, request, view):
        if view.action == 'create':
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Allow all for admin users
        if request.user.is_staff:
            return True

        # Allow access (read or write) only to the owner of the object
        return obj == request.user

class IsEmployerOrRecruiterForCompany(BasePermission):
    """Allow job modifications only for associated company employers/recruiters"""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return request.user.user_type == 'employer'
            
        user = request.user
        return (
            user.is_staff or
            (user.user_type == 'employer' and obj.company == user.company) or
            (user.user_type == 'recruiter' and obj.company in user.companies.all())
        )

class IsEmployerForApplications(BasePermission):
    """Allow employers to view applications for their jobs"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'employer'

class IsEmployerOrReadOnly(BasePermission):
    """Allow employers to create/update jobs, everyone can read"""
    def has_permission(self, request, view):
        """Grant access only to authenticated employers. Both read and write operations are restricted to employers."""
        return (
            request.user.is_authenticated and
            request.user.user_type == 'employer'
        )

class IsCandidateForApplications(BasePermission):
    """Allow candidates to create applications"""
    def has_permission(self, request, view):
        """Only authenticated candidates are granted any access to the endpoint."""
        return request.user.is_authenticated and request.user.user_type == 'candidate'

class IsSelfOrReadOnly(BasePermission):
    """Allow users to only edit their own profile"""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user