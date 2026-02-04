from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from common.permissions import IsLogin, IsOwnerOrReadOnly
from common.response import api_response, ErrorCode
from post.serializers import (
    PostSerializer, PostListSerializer, RepostSerializer,
    PostFavoriteSerializer
)
from post.models import Post, RePost, PostLike, PostFavorite
from django.http import Http404
from django.db.models import Count, Q


class PostList(ListCreateAPIView):
    """帖子列表"""

    serializer_class = PostListSerializer
    permission_classes = (IsLogin,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['create_time', 'view_count', 'like_count']
    ordering = ['-is_top', '-create_time']

    def get_queryset(self):
        queryset = Post.objects.filter(status=0).annotate(
            like_count=Count('likes', distinct=True),
            favorite_count=Count('favorites', distinct=True),
            reply_count=Count('reposts', distinct=True)
        )

        # 按板块筛选
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module_id=module)

        # 按用户筛选
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # 精华帖筛选
        is_essence = self.request.query_params.get('is_essence')
        if is_essence == 'true':
            queryset = queryset.filter(is_essence=True)

        return queryset

    def post(self, request, *args, **kwargs):
        """创建帖子"""
        request.data['user'] = request.user.id
        return self.create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostSerializer
        return PostListSerializer


class PostDetail(RetrieveUpdateDestroyAPIView):
    """帖子详情"""

    serializer_class = PostSerializer
    permission_classes = (IsLogin, IsOwnerOrReadOnly)

    def get_object(self):
        try:
            post = Post.objects.annotate(
                like_count=Count('likes', distinct=True),
                favorite_count=Count('favorites', distinct=True),
                reply_count=Count('reposts', distinct=True)
            ).get(id=self.kwargs['id'], status=0)
            return post
        except Post.DoesNotExist:
            raise Http404

    def get(self, request, *args, **kwargs):
        """获取帖子详情，同时增加浏览量"""
        post = self.get_object()
        # 增加浏览量
        Post.objects.filter(id=post.id).update(view_count=post.view_count + 1)
        serializer = self.get_serializer(post)
        return api_response(data=serializer.data)

    def delete(self, request, *args, **kwargs):
        """软删除帖子"""
        post = self.get_object()
        if post.user != request.user and not request.user.is_superuser:
            return api_response(code=ErrorCode.PERMISSION_DENIED, message='无权删除此帖子')
        post.status = 1
        post.save()
        return api_response(message='删除成功')


class RepostList(ListCreateAPIView):
    """回帖列表"""

    serializer_class = RepostSerializer
    permission_classes = (IsLogin,)

    def get_queryset(self):
        post_id = self.request.query_params.get('post')
        queryset = RePost.objects.filter(parent__isnull=True)
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def post(self, request, *args, **kwargs):
        """创建回帖"""
        request.data['user'] = request.user.id
        return self.create(request, *args, **kwargs)


class PostLikeView(APIView):
    """帖子点赞"""

    permission_classes = (IsLogin,)

    def post(self, request, post_id):
        """点赞"""
        try:
            post = Post.objects.get(id=post_id, status=0)
        except Post.DoesNotExist:
            return api_response(code=ErrorCode.POST_NOT_FOUND)

        if PostLike.objects.filter(user=request.user, post=post).exists():
            return api_response(code=ErrorCode.ALREADY_LIKED)

        PostLike.objects.create(user=request.user, post=post)
        return api_response(message='点赞成功', data={'like_count': post.like_count})

    def delete(self, request, post_id):
        """取消点赞"""
        try:
            post = Post.objects.get(id=post_id, status=0)
        except Post.DoesNotExist:
            return api_response(code=ErrorCode.POST_NOT_FOUND)

        like = PostLike.objects.filter(user=request.user, post=post).first()
        if not like:
            return api_response(code=ErrorCode.NOT_LIKED)

        like.delete()
        return api_response(message='取消点赞成功', data={'like_count': post.like_count})


class PostFavoriteView(APIView):
    """帖子收藏"""

    permission_classes = (IsLogin,)

    def post(self, request, post_id):
        """收藏"""
        try:
            post = Post.objects.get(id=post_id, status=0)
        except Post.DoesNotExist:
            return api_response(code=ErrorCode.POST_NOT_FOUND)

        if PostFavorite.objects.filter(user=request.user, post=post).exists():
            return api_response(code=ErrorCode.ALREADY_FAVORITED)

        PostFavorite.objects.create(user=request.user, post=post)
        return api_response(message='收藏成功', data={'favorite_count': post.favorite_count})

    def delete(self, request, post_id):
        """取消收藏"""
        try:
            post = Post.objects.get(id=post_id, status=0)
        except Post.DoesNotExist:
            return api_response(code=ErrorCode.POST_NOT_FOUND)

        favorite = PostFavorite.objects.filter(user=request.user, post=post).first()
        if not favorite:
            return api_response(code=ErrorCode.NOT_FAVORITED)

        favorite.delete()
        return api_response(message='取消收藏成功', data={'favorite_count': post.favorite_count})


class UserFavoriteList(ListCreateAPIView):
    """用户收藏列表"""

    serializer_class = PostFavoriteSerializer
    permission_classes = (IsLogin,)

    def get_queryset(self):
        return PostFavorite.objects.filter(user=self.request.user).order_by('-create_time')


class PostSearchView(ListCreateAPIView):
    """帖子搜索"""

    serializer_class = PostListSerializer
    permission_classes = (IsLogin,)

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword', '')
        if not keyword:
            return Post.objects.none()

        return Post.objects.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword),
            status=0
        ).annotate(
            like_count=Count('likes', distinct=True),
            favorite_count=Count('favorites', distinct=True),
            reply_count=Count('reposts', distinct=True)
        ).order_by('-create_time')


class HotPostList(ListCreateAPIView):
    """热门帖子列表"""

    serializer_class = PostListSerializer
    permission_classes = (IsLogin,)
    pagination_class = None

    def get_queryset(self):
        return Post.objects.filter(status=0).annotate(
            like_count=Count('likes', distinct=True),
            favorite_count=Count('favorites', distinct=True),
            reply_count=Count('reposts', distinct=True)
        ).order_by('-view_count', '-like_count')[:10]
