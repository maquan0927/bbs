from rest_framework import serializers
from post.models import Post, RePost
from module.serializers import ModuleSerializer
from user.serializers import UserSerializer
from common.datetime_serializer import DateTimeFieldWihTZ

class RepostSerializer(serializers.ModelSerializer):

    user_info = serializers.SerializerMethodField(read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)

    def get_user_info(self, obj):
        return obj.user.username

    class Meta:
        model = RePost
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    reposts = RepostSerializer(many=True, read_only=True)
    module_detail = ModuleSerializer(source='module', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    update_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Post
        fields = '__all__'
