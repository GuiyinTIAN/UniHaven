from django.contrib import admin
from django.contrib import messages
from django.db import connection
from .models import Accommodation, AccommodationRating, University, AccommodationUniversity, UniversityAPIKey

class AccommodationUniversityInline(admin.TabularInline):
    model = AccommodationUniversity
    extra = 1

class UniversityAPIKeyInline(admin.StackedInline):
    model = UniversityAPIKey
    can_delete = False
    max_num = 1
    extra = 0
    readonly_fields = ('created_at', 'last_used')
    fields = ('key', 'is_active', 'created_at', 'last_used')

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'price', 'region', 'reserved', 'get_universities')
    list_filter = ('type', 'region', 'reserved', 'affiliated_universities')
    search_fields = ('title', 'description', 'building_name')
    actions = ['reset_ids']
    inlines = [AccommodationUniversityInline]
    
    def reset_ids(self, request, queryset):
        """重置 ID 自增序列的管理操作"""
        if not request.user.is_superuser:
            messages.error(request, "只有超级用户可以执行此操作")
            return
            
        # 删除所有记录
        Accommodation.objects.all().delete()
        
        # 根据数据库类型重置序列
        db_engine = connection.vendor
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM accommodation_accommodation;")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='accommodation_accommodation';")
                
        messages.success(request, f"ID 序列已重置 (数据库类型: {db_engine})")
    
    reset_ids.short_description = "重置所有记录并将 ID 序列重置为 1"

    def get_universities(self, obj):
        return ", ".join([u.code for u in obj.affiliated_universities.all()])
    get_universities.short_description = "Universities"

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'specialist_email', 'has_api_key')
    search_fields = ('code', 'name')
    inlines = [UniversityAPIKeyInline]
    
    def has_api_key(self, obj):
        return hasattr(obj, 'api_key')
    has_api_key.boolean = True
    has_api_key.short_description = "API Key"

@admin.register(AccommodationRating)
class AccommodationRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'accommodation', 'user_identifier', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user_identifier', 'accommodation__title')

@admin.register(UniversityAPIKey)
class UniversityAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('university', 'key', 'is_active', 'created_at', 'last_used')
    list_filter = ('is_active', 'university')
    search_fields = ('university__name', 'university__code', 'key')
    readonly_fields = ('created_at', 'last_used')
    fieldsets = (
        (None, {
            'fields': ('university', 'key', 'is_active')
        }),
        ('Time Information', {
            'fields': ('created_at', 'last_used'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('university',) 
        return self.readonly_fields

