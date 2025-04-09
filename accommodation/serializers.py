from rest_framework import serializers
from .models import Accommodation

class AccommodationSerializer(serializers.ModelSerializer):
    """用于创建和更新住宿信息的序列化器"""
    # 添加自定义字段用于接收表单中的地址信息
    address = serializers.CharField(write_only=True)
    formatted_address = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'type', 'price', 'beds', 'bedrooms', 
                 'available_from', 'available_to', 'address', 'formatted_address',
                 'reserved', 'userID', 'building_name', 'region', 
                 'contact_phone', 'contact_email']  # 添加联系方式字段
        read_only_fields = ['id', 'latitude', 'longitude', 'building_name', 
                           'estate_name', 'street_name', 'building_no', 'district', 
                           'region', 'formatted_address']
    
    def get_formatted_address(self, obj):
        return obj.formatted_address()

class AccommodationDetailSerializer(serializers.ModelSerializer):
    """用于显示住宿详情的序列化器"""
    formatted_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'type', 'price', 'beds', 'bedrooms', 
                 'available_from', 'available_to', 'region', 'reserved', 'formatted_address',
                 'building_name', 'userID', 'contact_phone', 'contact_email']  # 添加联系方式字段
    
    def get_formatted_address(self, obj):
        return obj.formatted_address()

class AccommodationListSerializer(serializers.ModelSerializer):
    """用于列出住宿信息的序列化器"""
    distance = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'building_name', 'description', 'type', 'price', 'beds', 'bedrooms',
                 'available_from', 'available_to', 'region', 'distance', 'reserved', 'contact_phone', 'contact_email']
