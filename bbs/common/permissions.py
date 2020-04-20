from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class IsLogin(BasePermission):

    def has_permission(self, request, view):
        if request.method in ['patch', 'post', 'delete']:
            return request.user
        return True
