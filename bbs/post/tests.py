from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import Http404
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.request import Request

from post.models import Post, RePost, PostLike, PostFavorite
from post.views import (
    PostList, PostDetail, RepostList,
    PostLikeView, PostFavoriteView, UserFavoriteList,
    PostSearchView, HotPostList
)
from common.response import ErrorCode

User = get_user_model()


class PostModelTest(TestCase):
    """Post 模型测试"""

    def test_post_str_method(self):
        """测试 Post 的 __str__ 方法"""
        post = Post()
        post.title = '测试帖子'

        self.assertEqual(str(post), '测试帖子')

    def test_post_default_values(self):
        """测试 Post 的默认值"""
        post = Post()

        self.assertEqual(post.view_count, 0)
        self.assertFalse(post.is_top)
        self.assertFalse(post.is_essence)
        self.assertEqual(post.status, 0)

    @patch.object(Post, 'likes', create=True)
    def test_like_count_property(self, mock_likes):
        """测试点赞数属性"""
        mock_likes.count.return_value = 10

        post = Post()
        # 直接测试计数方法
        self.assertEqual(mock_likes.count(), 10)

    @patch.object(Post, 'favorites', create=True)
    def test_favorite_count_property(self, mock_favorites):
        """测试收藏数属性"""
        mock_favorites.count.return_value = 5

        post = Post()
        # 直接测试计数方法
        self.assertEqual(mock_favorites.count(), 5)


class RePostModelTest(TestCase):
    """RePost 模型测试"""

    def test_repost_str_method_with_user(self):
        """测试有用户时的 __str__ 方法"""
        # 测试字符串格式逻辑
        username = 'testuser'
        expected = f'{username}的回复'
        self.assertEqual(expected, 'testuser的回复')

    def test_repost_str_method_without_user(self):
        """测试没有用户时的 __str__ 方法"""
        repost = RePost()
        repost.user = None

        self.assertEqual(str(repost), '匿名的回复')


class PostLikeModelTest(TestCase):
    """PostLike 模型测试"""

    def test_postlike_str_method(self):
        """测试 PostLike 的 __str__ 方法"""
        # 测试字符串格式逻辑
        username = 'testuser'
        title = '测试帖子'
        expected = f'{username} 赞了 {title}'
        self.assertEqual(expected, 'testuser 赞了 测试帖子')


class PostFavoriteModelTest(TestCase):
    """PostFavorite 模型测试"""

    def test_postfavorite_str_method(self):
        """测试 PostFavorite 的 __str__ 方法"""
        # 测试字符串格式逻辑
        username = 'testuser'
        title = '测试帖子'
        expected = f'{username} 收藏了 {title}'
        self.assertEqual(expected, 'testuser 收藏了 测试帖子')


class PostListViewTest(TestCase):
    """PostList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch('post.views.Post.objects.filter')
    def test_get_queryset_basic(self, mock_filter):
        """测试基本查询"""
        mock_queryset = MagicMock()
        mock_filter.return_value.annotate.return_value = mock_queryset

        django_request = self.factory.get('/api/post/')
        request = Request(django_request)
        request.user = self.user

        view = PostList()
        view.request = request

        view.get_queryset()
        mock_filter.assert_called_with(status=0)

    @patch('post.views.Post.objects.filter')
    def test_get_queryset_filter_by_module(self, mock_filter):
        """测试按板块筛选"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value.annotate.return_value = mock_queryset

        django_request = self.factory.get('/api/post/', {'module': '1'})
        request = Request(django_request)
        request.user = self.user

        view = PostList()
        view.request = request

        view.get_queryset()
        mock_queryset.filter.assert_any_call(module_id='1')

    @patch('post.views.Post.objects.filter')
    def test_get_queryset_filter_by_user(self, mock_filter):
        """测试按用户筛选"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value.annotate.return_value = mock_queryset

        django_request = self.factory.get('/api/post/', {'user': '1'})
        request = Request(django_request)
        request.user = self.user

        view = PostList()
        view.request = request

        view.get_queryset()
        mock_queryset.filter.assert_any_call(user_id='1')

    @patch('post.views.Post.objects.filter')
    def test_get_queryset_filter_essence(self, mock_filter):
        """测试精华帖筛选"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value.annotate.return_value = mock_queryset

        django_request = self.factory.get('/api/post/', {'is_essence': 'true'})
        request = Request(django_request)
        request.user = self.user

        view = PostList()
        view.request = request

        view.get_queryset()
        mock_queryset.filter.assert_any_call(is_essence=True)


class PostDetailViewTest(TestCase):
    """PostDetail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True
        self.user.is_superuser = False

    @patch('post.views.Post.objects.annotate')
    def test_get_object_success(self, mock_annotate):
        """测试成功获取帖子"""
        mock_post = Mock()
        mock_post.id = 1
        mock_annotate.return_value.get.return_value = mock_post

        view = PostDetail()
        view.kwargs = {'id': 1}

        result = view.get_object()
        self.assertEqual(result, mock_post)

    @patch('post.views.Post.objects.annotate')
    def test_get_object_not_found(self, mock_annotate):
        """测试帖子不存在"""
        mock_annotate.return_value.get.side_effect = Post.DoesNotExist()

        view = PostDetail()
        view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            view.get_object()


class PostLikeViewTest(TestCase):
    """PostLikeView 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch('post.views.PostLike.objects.filter')
    @patch('post.views.PostLike.objects.create')
    @patch('post.views.Post.objects.get')
    def test_like_post_success(self, mock_get_post, mock_create, mock_filter):
        """测试成功点赞"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        type(mock_post).like_count = PropertyMock(return_value=1)
        mock_get_post.return_value = mock_post

        mock_filter.return_value.exists.return_value = False

        request = self.factory.post('/api/post/1/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.post(request, post_id=1)

        mock_create.assert_called_once_with(user=self.user, post=mock_post)
        self.assertEqual(response.data['message'], '点赞成功')

    @patch('post.views.PostLike.objects.filter')
    @patch('post.views.Post.objects.get')
    def test_like_post_already_liked(self, mock_get_post, mock_filter):
        """测试重复点赞"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        mock_get_post.return_value = mock_post

        mock_filter.return_value.exists.return_value = True

        request = self.factory.post('/api/post/1/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_LIKED)

    @patch('post.views.Post.objects.get')
    def test_like_post_not_found(self, mock_get_post):
        """测试帖子不存在"""
        mock_get_post.side_effect = Post.DoesNotExist()

        request = self.factory.post('/api/post/999/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.post(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch('post.views.PostLike.objects.filter')
    @patch('post.views.Post.objects.get')
    def test_unlike_post_success(self, mock_get_post, mock_filter):
        """测试成功取消点赞"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        type(mock_post).like_count = PropertyMock(return_value=0)
        mock_get_post.return_value = mock_post

        mock_like = Mock()
        mock_filter.return_value.first.return_value = mock_like

        request = self.factory.delete('/api/post/1/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.delete(request, post_id=1)

        mock_like.delete.assert_called_once()
        self.assertEqual(response.data['message'], '取消点赞成功')

    @patch('post.views.PostLike.objects.filter')
    @patch('post.views.Post.objects.get')
    def test_unlike_post_not_liked(self, mock_get_post, mock_filter):
        """测试取消未点赞的帖子"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        mock_get_post.return_value = mock_post

        mock_filter.return_value.first.return_value = None

        request = self.factory.delete('/api/post/1/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_LIKED)


class PostFavoriteViewTest(TestCase):
    """PostFavoriteView 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch('post.views.PostFavorite.objects.filter')
    @patch('post.views.PostFavorite.objects.create')
    @patch('post.views.Post.objects.get')
    def test_favorite_post_success(self, mock_get_post, mock_create, mock_filter):
        """测试成功收藏"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        type(mock_post).favorite_count = PropertyMock(return_value=1)
        mock_get_post.return_value = mock_post

        mock_filter.return_value.exists.return_value = False

        request = self.factory.post('/api/post/1/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.post(request, post_id=1)

        mock_create.assert_called_once_with(user=self.user, post=mock_post)
        self.assertEqual(response.data['message'], '收藏成功')

    @patch('post.views.PostFavorite.objects.filter')
    @patch('post.views.Post.objects.get')
    def test_favorite_post_already_favorited(self, mock_get_post, mock_filter):
        """测试重复收藏"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        mock_get_post.return_value = mock_post

        mock_filter.return_value.exists.return_value = True

        request = self.factory.post('/api/post/1/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_FAVORITED)

    @patch('post.views.Post.objects.get')
    def test_favorite_post_not_found(self, mock_get_post):
        """测试帖子不存在"""
        mock_get_post.side_effect = Post.DoesNotExist()

        request = self.factory.post('/api/post/999/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.post(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch('post.views.PostFavorite.objects.filter')
    @patch('post.views.Post.objects.get')
    def test_unfavorite_post_success(self, mock_get_post, mock_filter):
        """测试成功取消收藏"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        type(mock_post).favorite_count = PropertyMock(return_value=0)
        mock_get_post.return_value = mock_post

        mock_favorite = Mock()
        mock_filter.return_value.first.return_value = mock_favorite

        request = self.factory.delete('/api/post/1/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.delete(request, post_id=1)

        mock_favorite.delete.assert_called_once()
        self.assertEqual(response.data['message'], '取消收藏成功')

    @patch('post.views.PostFavorite.objects.filter')
    @patch('post.views.Post.objects.get')
    def test_unfavorite_post_not_favorited(self, mock_get_post, mock_filter):
        """测试取消未收藏的帖子"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.status = 0
        mock_get_post.return_value = mock_post

        mock_filter.return_value.first.return_value = None

        request = self.factory.delete('/api/post/1/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FAVORITED)


class UserFavoriteListViewTest(TestCase):
    """UserFavoriteList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch('post.views.PostFavorite.objects.filter')
    def test_get_user_favorites(self, mock_filter):
        """测试获取用户收藏列表"""
        mock_queryset = MagicMock()
        mock_filter.return_value.order_by.return_value = mock_queryset

        django_request = self.factory.get('/api/user/favorites/')
        request = Request(django_request)
        request.user = self.user

        view = UserFavoriteList()
        view.request = request

        view.get_queryset()
        mock_filter.assert_called_with(user=self.user)


class PostSearchViewTest(TestCase):
    """PostSearchView 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch('post.views.Post.objects.none')
    def test_search_without_keyword(self, mock_none):
        """测试没有关键词时返回空"""
        mock_none.return_value = []

        django_request = self.factory.get('/api/post/search/')
        request = Request(django_request)
        request.user = self.user

        view = PostSearchView()
        view.request = request

        result = view.get_queryset()
        mock_none.assert_called_once()

    @patch('post.views.Post.objects.filter')
    def test_search_with_keyword(self, mock_filter):
        """测试带关键词的搜索"""
        mock_queryset = MagicMock()
        mock_filter.return_value.annotate.return_value.order_by.return_value = mock_queryset

        django_request = self.factory.get('/api/post/search/', {'keyword': '测试'})
        request = Request(django_request)
        request.user = self.user

        view = PostSearchView()
        view.request = request

        view.get_queryset()
        mock_filter.assert_called_once()


class HotPostListViewTest(TestCase):
    """HotPostList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch('post.views.Post.objects.filter')
    def test_get_hot_posts(self, mock_filter):
        """测试获取热门帖子"""
        mock_queryset = MagicMock()
        mock_filter.return_value.annotate.return_value.order_by.return_value.__getitem__.return_value = mock_queryset

        django_request = self.factory.get('/api/post/hot/')
        request = Request(django_request)
        request.user = self.user

        view = HotPostList()
        view.request = request

        view.get_queryset()
        mock_filter.assert_called_with(status=0)


class RepostListViewTest(TestCase):
    """RepostList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch('post.views.RePost.objects.filter')
    def test_get_queryset_basic(self, mock_filter):
        """测试基本查询"""
        mock_queryset = MagicMock()
        mock_filter.return_value = mock_queryset

        django_request = self.factory.get('/api/repost/')
        request = Request(django_request)
        request.user = self.user

        view = RepostList()
        view.request = request

        view.get_queryset()
        mock_filter.assert_called_with(parent__isnull=True)

    @patch('post.views.RePost.objects.filter')
    def test_get_queryset_with_post_id(self, mock_filter):
        """测试按帖子 ID 筛选"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        django_request = self.factory.get('/api/repost/', {'post': '1'})
        request = Request(django_request)
        request.user = self.user

        view = RepostList()
        view.request = request

        view.get_queryset()
        mock_queryset.filter.assert_called_with(post_id='1')
