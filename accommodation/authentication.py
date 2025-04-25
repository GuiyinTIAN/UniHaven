from django.utils import timezone
from rest_framework import authentication
from rest_framework import exceptions
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from .models import UniversityAPIKey

class UniversityAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    基于API密钥的认证系统，用于区分不同大学系统的请求
    """
    def authenticate(self, request):
        # 从请求头获取API密钥
        api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
        
        if not api_key:
            # 没有提供API密钥，返回None表示使用其他认证方法
            return None
            
        try:
            # 查找对应的API密钥记录
            api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
            university = api_key_obj.university
            
            # 更新最后使用时间
            api_key_obj.last_used = timezone.now()
            api_key_obj.save(update_fields=['last_used'])
            
            # 返回(user, auth)元组，这里我们用university作为user
            return (university, api_key_obj)
        except UniversityAPIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')

# 添加DRF Spectacular的认证扩展类
class UniversityAPIKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    """OpenAPI扩展类，告诉Swagger UI如何处理API密钥认证"""
    target_class = 'accommodation.authentication.UniversityAPIKeyAuthentication'
    name = 'UniversityAPIKey'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'The key is used to identify the university system and can be provided in the request header or query parameters'
        }
