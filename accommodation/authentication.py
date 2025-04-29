from django.utils import timezone
from rest_framework import authentication
from rest_framework import exceptions
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from .models import UniversityAPIKey

class UniversityAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    An authentication system based on API keys, used to distinguish requests from different university systems
    """
    def authenticate(self, request):
        # Get the API key from the request header or query parameters
        api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
        
        if not api_key:
            return None
            
        try:
            # Search for the corresponding API key record
            api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
            university = api_key_obj.university
            
            # Update the last used time of the API key
            api_key_obj.last_used = timezone.now()
            api_key_obj.save(update_fields=['last_used'])
            
            # Return the (user, auth) tuple. Here we use university as the user
            return (university, api_key_obj)
        except UniversityAPIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')

# 添加DRF Spectacular的认证扩展类
class UniversityAPIKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    """OpenAPI extension class, telling Swagger UI how to handle API key authentication"""
    target_class = 'accommodation.authentication.UniversityAPIKeyAuthentication'
    name = 'UniversityAPIKey'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'The key is used to identify the university system and can be provided in the request header or query parameters'
        }
