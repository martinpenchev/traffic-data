from rest_framework import permissions
from django.contrib.auth import get_user_model

class HasToken(permissions.BasePermission):

    def has_permission(self, request, view):
        token = request.META.get('HTTP_X_API_TOKEN', False)
        if token == False:
            return False
        else:
            return get_user_model().objects.filter(token=str(token)).exists()