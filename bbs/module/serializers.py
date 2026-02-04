from rest_framework import serializers
from module.models import Module


class ModuleSerializer(serializers.ModelSerializer):
    """板块序列化器"""
    post_count = serializers.IntegerField(read_only=True)
    today_post_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Module
        fields = '__all__'
