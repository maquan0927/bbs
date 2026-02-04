from rest_framework import serializers
from post.models import Post, RePost, PostLike, PostFavorite
from module.serializers import ModuleSerializer
from user.serializers import UserProfileSerializer
from common.datetime_serializer import DateTimeFieldWihTZ


class RepostSerializer(serializers.ModelSerializer):
    """回帖序列化器"""
    user_info = serializers.SerializerMethodField(read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    update_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    children = serializers.SerializerMethodField(read_only=True)

    def get_user_info(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'avatar': obj.user.avatar.url if obj.user.avatar else None
            }
        return None

    def get_children(self, obj):
        """获取子回复"""
        children = obj.children.all()
        return RepostSerializer(children, many=True).data if children else []

    class Meta:
        model = RePost
        fields = '__all__'


class PostListSerializer(serializers.ModelSerializer):
    """帖子列表序列化器（简化信息）"""
    module_detail = ModuleSerializer(source='module', read_only=True)
    user_detail = UserProfileSerializer(source='user', read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'title', 'create_time', 'user', 'user_detail', 'module',
                  'module_detail', 'view_count', 'is_top', 'is_essence',
                  'like_count', 'favorite_count', 'reply_count')


class PostSerializer(serializers.ModelSerializer):
    """帖子详情序列化器"""
    reposts = RepostSerializer(many=True, read_only=True)
    module_detail = ModuleSerializer(source='module', read_only=True)
    user_detail = UserProfileSerializer(source='user', read_only=True)
    create_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    update_time = DateTimeFieldWihTZ(format="%Y-%m-%d %H:%M", read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)

    def get_is_liked(self, obj):
        """当前用户是否已点赞"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_is_favorited(self, obj):
        """当前用户是否已收藏"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostFavorite.objects.filter(user=request.user, post=obj).exists()
        return False

    class Meta:
        model = Post
        fields = '__all__'


class PostLikeSerializer(serializers.ModelSerializer):
    """点赞序列化器"""
    class Meta:
        model = PostLike
        fields = '__all__'


class PostFavoriteSerializer(serializers.ModelSerializer):
    """收藏序列化器"""
    post_detail = PostListSerializer(source='post', read_only=True)

    class Meta:
        model = PostFavorite
        fields = '__all__'
