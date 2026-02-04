from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from rest_framework import status
from django.http import Http404

from post.models import Post, RePost, PostLike, PostFavorite
from post.views import (
    PostList, PostDetail, RepostList, PostLikeView,
    PostFavoriteView, UserFavoriteList, PostSearchView, HotPostList
)
from post.serializers import PostSerializer, RepostSerializer, PostListSerializer
from common.response import ErrorCode

User = get_user_model()


class PostModelTestCase(TestCase):
    """测试帖子模型"""

    def test_post_status_options(self):
        """测试帖子状态选项"""
        status_options = Post.status_options
        self.assertEqual(len(status_options), 3)
        self.assertEqual(status_options[0], (0, '正常'))
        self.assertEqual(status_options[1], (1, '已删除'))
        self.assertEqual(status_options[2], (2, '待审核'))

    def test_post_meta_ordering(self):
        """测试帖子排序"""
        self.assertEqual(Post._meta.ordering, ['-is_top', '-create_time'])

    def test_post_meta_verbose_name(self):
        """测试帖子verbose_name"""
        self.assertEqual(Post._meta.verbose_name, '帖子')

    @patch.object(Post, 'likes', new_callable=PropertyMock)
    def test_post_like_count_property(self, mock_likes):
        """测试点赞数属性"""
        mock_likes.return_value.count.return_value = 10
        post = Post()
        self.assertEqual(post.like_count, 10)

    @patch.object(Post, 'favorites', new_callable=PropertyMock)
    def test_post_favorite_count_property(self, mock_favorites):
        """测试收藏数属性"""
        mock_favorites.return_value.count.return_value = 5
        post = Post()
        self.assertEqual(post.favorite_count, 5)

    @patch.object(Post, 'reposts', new_callable=PropertyMock)
    def test_post_reply_count_property(self, mock_reposts):
        """测试回复数属性"""
        mock_reposts.return_value.count.return_value = 3
        post = Post()
        self.assertEqual(post.reply_count, 3)


class RePostModelTestCase(TestCase):
    """测试回帖模型"""

    def test_repost_meta_ordering(self):
        """测试回帖排序"""
        self.assertEqual(RePost._meta.ordering, ['create_time'])

    def test_repost_meta_verbose_name(self):
        """测试回帖verbose_name"""
        self.assertEqual(RePost._meta.verbose_name, '回帖')


class PostLikeModelTestCase(TestCase):
    """测试点赞模型"""

    def test_postlike_meta_unique_together(self):
        """测试点赞唯一约束"""
        self.assertEqual(PostLike._meta.unique_together, (('user', 'post'),))

    def test_postlike_meta_verbose_name(self):
        """测试点赞verbose_name"""
        self.assertEqual(PostLike._meta.verbose_name, '帖子点赞')


class PostFavoriteModelTestCase(TestCase):
    """测试收藏模型"""

    def test_postfavorite_meta_unique_together(self):
        """测试收藏唯一约束"""
        self.assertEqual(PostFavorite._meta.unique_together, (('user', 'post'),))

    def test_postfavorite_meta_verbose_name(self):
        """测试收藏verbose_name"""
        self.assertEqual(PostFavorite._meta.verbose_name, '帖子收藏')


class PostLikeViewTestCase(TestCase):
    """测试点赞视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostLikeView()

    @patch.object(Post.objects, 'get')
    def test_like_post_not_found(self, mock_get):
        """测试点赞不存在的帖子"""
        mock_get.side_effect = Post.DoesNotExist

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch.object(PostLike.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_like_already_liked(self, mock_get, mock_filter):
        """测试重复点赞"""
        mock_post = Mock()
        mock_get.return_value = mock_post
        mock_filter.return_value.exists.return_value = True

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_LIKED)

    @patch.object(PostLike.objects, 'create')
    @patch.object(PostLike.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_like_success(self, mock_get, mock_filter, mock_create):
        """测试成功点赞"""
        mock_post = Mock()
        mock_post.like_count = 1
        mock_get.return_value = mock_post
        mock_filter.return_value.exists.return_value = False

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=1)

        mock_create.assert_called_once()
        self.assertEqual(response.data['message'], '点赞成功')
        self.assertEqual(response.data['data']['like_count'], 1)

    @patch.object(Post.objects, 'get')
    def test_unlike_post_not_found(self, mock_get):
        """测试取消点赞不存在的帖子"""
        mock_get.side_effect = Post.DoesNotExist

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch.object(PostLike.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_unlike_not_liked(self, mock_get, mock_filter):
        """测试取消未点过的赞"""
        mock_post = Mock()
        mock_get.return_value = mock_post
        mock_filter.return_value.first.return_value = None

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_LIKED)

    @patch.object(PostLike.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_unlike_success(self, mock_get, mock_filter):
        """测试成功取消点赞"""
        mock_post = Mock()
        mock_post.like_count = 0
        mock_get.return_value = mock_post
        mock_like = Mock()
        mock_filter.return_value.first.return_value = mock_like

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=1)

        mock_like.delete.assert_called_once()
        self.assertEqual(response.data['message'], '取消点赞成功')


class PostFavoriteViewTestCase(TestCase):
    """测试收藏视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostFavoriteView()

    @patch.object(Post.objects, 'get')
    def test_favorite_post_not_found(self, mock_get):
        """测试收藏不存在的帖子"""
        mock_get.side_effect = Post.DoesNotExist

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch.object(PostFavorite.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_favorite_already_favorited(self, mock_get, mock_filter):
        """测试重复收藏"""
        mock_post = Mock()
        mock_get.return_value = mock_post
        mock_filter.return_value.exists.return_value = True

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_FAVORITED)

    @patch.object(PostFavorite.objects, 'create')
    @patch.object(PostFavorite.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_favorite_success(self, mock_get, mock_filter, mock_create):
        """测试成功收藏"""
        mock_post = Mock()
        mock_post.favorite_count = 1
        mock_get.return_value = mock_post
        mock_filter.return_value.exists.return_value = False

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=1)

        mock_create.assert_called_once()
        self.assertEqual(response.data['message'], '收藏成功')
        self.assertEqual(response.data['data']['favorite_count'], 1)

    @patch.object(Post.objects, 'get')
    def test_unfavorite_post_not_found(self, mock_get):
        """测试取消收藏不存在的帖子"""
        mock_get.side_effect = Post.DoesNotExist

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch.object(PostFavorite.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_unfavorite_not_favorited(self, mock_get, mock_filter):
        """测试取消未收藏的"""
        mock_post = Mock()
        mock_get.return_value = mock_post
        mock_filter.return_value.first.return_value = None

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FAVORITED)

    @patch.object(PostFavorite.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_unfavorite_success(self, mock_get, mock_filter):
        """测试成功取消收藏"""
        mock_post = Mock()
        mock_post.favorite_count = 0
        mock_get.return_value = mock_post
        mock_favorite = Mock()
        mock_filter.return_value.first.return_value = mock_favorite

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=1)

        mock_favorite.delete.assert_called_once()
        self.assertEqual(response.data['message'], '取消收藏成功')


class PostSearchViewTestCase(TestCase):
    """测试帖子搜索视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostSearchView()

    @patch.object(Post.objects, 'none')
    def test_search_without_keyword(self, mock_none):
        """测试无关键词搜索"""
        mock_none.return_value = []

        request = self.factory.get('/')
        request.query_params = {}

        self.view.request = request
        result = self.view.get_queryset()

        mock_none.assert_called_once()

    @patch.object(Post.objects, 'filter')
    def test_search_with_keyword(self, mock_filter):
        """测试有关键词搜索"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value.order_by.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'keyword': 'test'})
        request.query_params = {'keyword': 'test'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_filter.assert_called_once()


class UserFavoriteListViewTestCase(TestCase):
    """测试用户收藏列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserFavoriteList()

    @patch.object(PostFavorite.objects, 'filter')
    def test_get_user_favorites(self, mock_filter):
        """测试获取用户收藏列表"""
        mock_queryset = Mock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        mock_user = Mock()
        request.user = mock_user

        self.view.request = request
        result = self.view.get_queryset()

        mock_filter.assert_called_with(user=mock_user)
        mock_queryset.order_by.assert_called_with('-create_time')


class HotPostListViewTestCase(TestCase):
    """测试热门帖子列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = HotPostList()

    @patch.object(Post.objects, 'filter')
    def test_get_hot_posts(self, mock_filter):
        """测试获取热门帖子"""
        mock_queryset = Mock()
        mock_annotate = Mock()
        mock_order_by = MagicMock()  # 使用 MagicMock 支持切片操作
        mock_queryset.annotate.return_value = mock_annotate
        mock_annotate.order_by.return_value = mock_order_by
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        self.view.request = request
        result = self.view.get_queryset()

        mock_filter.assert_called_with(status=0)
        mock_queryset.annotate.assert_called_once()
        mock_annotate.order_by.assert_called_with('-view_count', '-like_count')


class PostListViewTestCase(TestCase):
    """测试帖子列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostList()

    @patch.object(Post.objects, 'filter')
    def test_get_queryset_basic(self, mock_filter):
        """测试基本查询"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.query_params = {}

        self.view.request = request
        result = self.view.get_queryset()

        mock_filter.assert_called_with(status=0)

    @patch.object(Post.objects, 'filter')
    def test_get_queryset_filter_by_module(self, mock_filter):
        """测试按板块筛选"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'module': '1'})
        request.query_params = {'module': '1'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(module_id='1')

    @patch.object(Post.objects, 'filter')
    def test_get_queryset_filter_by_user(self, mock_filter):
        """测试按用户筛选"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'user': '1'})
        request.query_params = {'user': '1'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(user_id='1')

    @patch.object(Post.objects, 'filter')
    def test_get_queryset_filter_essence(self, mock_filter):
        """测试筛选精华帖"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'is_essence': 'true'})
        request.query_params = {'is_essence': 'true'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(is_essence=True)

    def test_get_serializer_class_for_post(self):
        """测试POST请求使用PostSerializer"""
        request = self.factory.post('/')
        self.view.request = request

        result = self.view.get_serializer_class()

        self.assertEqual(result, PostSerializer)

    def test_get_serializer_class_for_get(self):
        """测试GET请求使用PostListSerializer"""
        request = self.factory.get('/')
        self.view.request = request

        result = self.view.get_serializer_class()

        self.assertEqual(result, PostListSerializer)


class PostDetailViewTestCase(TestCase):
    """测试帖子详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostDetail()

    @patch.object(Post.objects, 'annotate')
    def test_get_object_not_found(self, mock_annotate):
        """测试获取不存在的帖子"""
        mock_queryset = Mock()
        mock_queryset.get.side_effect = Post.DoesNotExist
        mock_annotate.return_value = mock_queryset

        self.view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            self.view.get_object()

    @patch.object(Post.objects, 'annotate')
    def test_get_object_success(self, mock_annotate):
        """测试成功获取帖子"""
        mock_post = Mock()
        mock_queryset = Mock()
        mock_queryset.get.return_value = mock_post
        mock_annotate.return_value = mock_queryset

        self.view.kwargs = {'id': 1}

        result = self.view.get_object()

        self.assertEqual(result, mock_post)
        mock_queryset.get.assert_called_with(id=1, status=0)


class PostSerializerTestCase(TestCase):
    """测试帖子序列化器"""

    def test_get_is_liked_unauthenticated(self):
        """测试未认证用户的is_liked"""
        serializer = PostSerializer()
        serializer._context = {'request': None}
        mock_obj = Mock()

        result = serializer.get_is_liked(mock_obj)

        self.assertFalse(result)

    @patch.object(PostLike.objects, 'filter')
    def test_get_is_liked_authenticated(self, mock_filter):
        """测试已认证用户的is_liked"""
        mock_filter.return_value.exists.return_value = True

        serializer = PostSerializer()
        mock_request = Mock()
        mock_request.user.is_authenticated = True
        serializer._context = {'request': mock_request}
        mock_obj = Mock()

        result = serializer.get_is_liked(mock_obj)

        self.assertTrue(result)

    def test_get_is_favorited_unauthenticated(self):
        """测试未认证用户的is_favorited"""
        serializer = PostSerializer()
        serializer._context = {'request': None}
        mock_obj = Mock()

        result = serializer.get_is_favorited(mock_obj)

        self.assertFalse(result)

    @patch.object(PostFavorite.objects, 'filter')
    def test_get_is_favorited_authenticated(self, mock_filter):
        """测试已认证用户的is_favorited"""
        mock_filter.return_value.exists.return_value = True

        serializer = PostSerializer()
        mock_request = Mock()
        mock_request.user.is_authenticated = True
        serializer._context = {'request': mock_request}
        mock_obj = Mock()

        result = serializer.get_is_favorited(mock_obj)

        self.assertTrue(result)


class RepostSerializerTestCase(TestCase):
    """测试回帖序列化器"""

    def test_get_user_info_with_user(self):
        """测试有用户时返回用户信息"""
        serializer = RepostSerializer()
        mock_obj = Mock()
        mock_obj.user = Mock()
        mock_obj.user.id = 1
        mock_obj.user.username = 'testuser'
        mock_obj.user.avatar = None

        result = serializer.get_user_info(mock_obj)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['username'], 'testuser')
        self.assertIsNone(result['avatar'])

    def test_get_user_info_without_user(self):
        """测试无用户时返回None"""
        serializer = RepostSerializer()
        mock_obj = Mock()
        mock_obj.user = None

        result = serializer.get_user_info(mock_obj)

        self.assertIsNone(result)

    def test_get_children_empty(self):
        """测试无子回复时返回空列表"""
        serializer = RepostSerializer()
        mock_obj = Mock()
        mock_obj.children.all.return_value = []

        result = serializer.get_children(mock_obj)

        self.assertEqual(result, [])
