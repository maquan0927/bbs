from rest_framework import serializers
from user.models import User


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    post_count = serializers.SerializerMethodField(read_only=True)

    def get_post_count(self, obj):
        """获取用户发帖数"""
        return obj.posts.count() if hasattr(obj, 'posts') else 0

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_staff = True
        user.save()
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'birthday', 'sex',
                  'is_superuser', 'avatar', 'bio', 'phone', 'post_count',
                  'date_joined', 'last_login')
        extra_kwargs = {
            'password': {'write_only': True},
            'date_joined': {'read_only': True},
            'last_login': {'read_only': True}
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """用户简要信息序列化器，用于帖子等关联展示"""
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar', 'bio')
        read_only_fields = fields
