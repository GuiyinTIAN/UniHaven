from rest_framework import permissions

class UniversityAccessPermission(permissions.BasePermission):
    """
    控制大学系统只能访问与其关联的数据
    """
    def has_permission(self, request, view):
        # 允许访问视图，具体对象级权限在has_object_permission中处理
        return True
    
    def has_object_permission(self, request, view, obj):
        # 如果请求未经过认证，拒绝访问
        if not request.user or not hasattr(request.user, 'id'):
            return False
            
        # 检查对象是否与大学关联
        if hasattr(obj, 'affiliated_universities'):
            return (
                obj.affiliated_universities.filter(id=request.user.id).exists() or 
                not obj.affiliated_universities.exists()  # 如果没有关联任何大学，允许所有认证系统访问
            )
        return False
