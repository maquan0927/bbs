from rest_framework import serializers
from message.models import Message
from user.serializers import UserProfileSerializer
from common.datetime_serializer import DateTimeFieldWihTZ


class MessageSerializer(serializers.ModelSerializer):
    """消息序列化器"""
    sender_detail = UserProfileSerializer(source='sender', read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
