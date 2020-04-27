from rest_framework import serializers
from post.models import Post
from module.serializers import ModuleSerializer
from user.serializers import UserSerializer
from common.datetime_serializer import DateTimeFieldWihTZ

class PostSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M")
    update_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Post
        fields = '__all__'
