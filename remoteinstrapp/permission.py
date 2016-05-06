__author__ = 'macastro'


from django.conf import settings
from rest_framework import authentication
from rest_framework import permissions



class GivingPermissions(permissions.BasePermission):
    """
    Custom permission to allow all the using of API
    """
    def has_permission(self, request, view):
        return request.META.get('HTTP_API_KEY') == settings.API_KEY




class SimpleAuthentication(authentication.BaseAuthentication):
    """
    There is no policy about the authentication yet. It is posssible in the future...
    """
    def authenticate(self, request):
        pass

