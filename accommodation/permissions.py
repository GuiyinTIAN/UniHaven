from rest_framework import permissions

class UniversityAccessPermission(permissions.BasePermission):
    """
    控制大学系统只能访问与其关联的数据
    """
    def has_permission(self, request, view):
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not hasattr(request.user, 'id'):
            return False
            
        if hasattr(obj, 'affiliated_universities'):
            return (
                obj.affiliated_universities.filter(id=request.user.id).exists() or 
                not obj.affiliated_universities.exists()
            )
        return False
