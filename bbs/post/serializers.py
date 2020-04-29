from rest_framework import serializers
from module.models import Module
from user.models import User
from post.models import Post
from module.serializers import ModuleSerializer
from user.serializers import UserSerializer
from common.datetime_serializer import DateTimeFieldWihTZ

class PostSerializer(serializers.ModelSerializer):
    module_detail = ModuleSerializer(source='module', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    update_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Post
        fields = '__all__'
