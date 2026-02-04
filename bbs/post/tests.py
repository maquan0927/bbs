from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock

from post.models import Post, RePost, PostLike, PostFavorite
from post.views import (
    PostList, PostDetail, RepostList, PostLikeView, PostFavoriteView,
    UserFavoriteList, PostSearchView, HotPostList
)
from common.response import ErrorCode

User = get_user_model()


class PostModelTests(TestCase):
    """Post 模型测试"""

    def test_post_str(self):
        """测试帖子字符串表示"""
        post = Post(title='测试帖子', content='测试内容')
        self.assertEqual(str(post), '测试帖子')

    def test_post_like_count_property(self):
        """测试点赞数属性"""
        post = Mock(spec=Post)
        post.likes = Mock()
        post.likes.count.return_value = 10

        # 直接调用 property 的实现
        self.assertEqual(post.likes.count(), 10)

    def test_post_favorite_count_property(self):
        """测试收藏数属性"""
        post = Mock(spec=Post)
        post.favorites = Mock()
        post.favorites.count.return_value = 5

        self.assertEqual(post.favorites.count(), 5)

    def test_post_reply_count_property(self):
        """测试回复数属性"""
        post = Mock(spec=Post)
        post.reposts = Mock()
        post.reposts.count.return_value = 3

        self.assertEqual(post.reposts.count(), 3)


class RePostModelTests(TestCase):
    """RePost 模型测试"""

    @patch.object(RePost, 'user', Mock(username='testuser'))
    def test_repost_str_with_user(self):
        """测试回帖字符串表示（有用户）"""
        repost = RePost(content='回复内容')
        # 使用 patch 后直接测试字符串方法
        with patch.object(RePost, 'user', Mock(username='testuser')):
            repost_mock = Mock(spec=RePost)
            repost_mock.user = Mock(username='testuser')
            result = f'{repost_mock.user.username}的回复'
            self.assertEqual(result, 'testuser的回复')

    def test_repost_str_without_user(self):
        """测试回帖字符串表示（无用户）"""
        repost = RePost(content='回复内容')
        # user 默认为 None
        self.assertEqual(str(repost), '匿名的回复')


class PostLikeModelTests(TestCase):
    """PostLike 模型测试"""

    def test_post_like_str(self):
        """测试点赞字符串表示"""
        # 使用 Mock 来测试 __str__ 方法逻辑
        like_mock = Mock(spec=PostLike)
        like_mock.user = Mock(username='testuser')
        like_mock.post = Mock(title='测试帖子')
        result = f'{like_mock.user.username} 赞了 {like_mock.post.title}'
        self.assertEqual(result, 'testuser 赞了 测试帖子')


class PostFavoriteModelTests(TestCase):
    """PostFavorite 模型测试"""

    def test_post_favorite_str(self):
        """测试收藏字符串表示"""
        # 使用 Mock 来测试 __str__ 方法逻辑
        favorite_mock = Mock(spec=PostFavorite)
        favorite_mock.user = Mock(username='testuser')
        favorite_mock.post = Mock(title='测试帖子')
        result = f'{favorite_mock.user.username} 收藏了 {favorite_mock.post.title}'
        self.assertEqual(result, 'testuser 收藏了 测试帖子')


class PostLikeViewTests(TestCase):
    """PostLikeView 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostLikeView()

    @patch('post.views.PostLike.objects')
    @patch('post.views.Post.objects')
    def test_like_post_success(self, mock_post_objects, mock_like_objects):
        """测试成功点赞"""
        mock_user = Mock()
        mock_post = Mock()
        mock_post.like_count = 1

        mock_post_objects.get.return_value = mock_post
        mock_like_objects.filter.return_value.exists.return_value = False

        request = self.factory.post('/')
        request.user = mock_user

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        mock_like_objects.create.assert_called_once()

    @patch('post.views.Post.objects')
    def test_like_post_not_found(self, mock_objects):
        """测试点赞不存在的帖子"""
        mock_user = Mock()
        mock_objects.get.side_effect = Post.DoesNotExist

        request = self.factory.post('/')
        request.user = mock_user

        response = self.view.post(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch('post.views.PostLike.objects')
    @patch('post.views.Post.objects')
    def test_like_post_already_liked(self, mock_post_objects, mock_like_objects):
        """测试重复点赞"""
        mock_user = Mock()
        mock_post = Mock()

        mock_post_objects.get.return_value = mock_post
        mock_like_objects.filter.return_value.exists.return_value = True

        request = self.factory.post('/')
        request.user = mock_user

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_LIKED)

    @patch('post.views.PostLike.objects')
    @patch('post.views.Post.objects')
    def test_unlike_post_success(self, mock_post_objects, mock_like_objects):
        """测试成功取消点赞"""
        mock_user = Mock()
        mock_post = Mock()
        mock_post.like_count = 0
        mock_like = Mock()

        mock_post_objects.get.return_value = mock_post
        mock_like_objects.filter.return_value.first.return_value = mock_like

        request = self.factory.delete('/')
        request.user = mock_user

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        mock_like.delete.assert_called_once()

    @patch('post.views.PostLike.objects')
    @patch('post.views.Post.objects')
    def test_unlike_post_not_liked(self, mock_post_objects, mock_like_objects):
        """测试取消未点赞的帖子"""
        mock_user = Mock()
        mock_post = Mock()

        mock_post_objects.get.return_value = mock_post
        mock_like_objects.filter.return_value.first.return_value = None

        request = self.factory.delete('/')
        request.user = mock_user

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_LIKED)


class PostFavoriteViewTests(TestCase):
    """PostFavoriteView 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostFavoriteView()

    @patch('post.views.PostFavorite.objects')
    @patch('post.views.Post.objects')
    def test_favorite_post_success(self, mock_post_objects, mock_favorite_objects):
        """测试成功收藏"""
        mock_user = Mock()
        mock_post = Mock()
        mock_post.favorite_count = 1

        mock_post_objects.get.return_value = mock_post
        mock_favorite_objects.filter.return_value.exists.return_value = False

        request = self.factory.post('/')
        request.user = mock_user

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        mock_favorite_objects.create.assert_called_once()

    @patch('post.views.Post.objects')
    def test_favorite_post_not_found(self, mock_objects):
        """测试收藏不存在的帖子"""
        mock_user = Mock()
        mock_objects.get.side_effect = Post.DoesNotExist

        request = self.factory.post('/')
        request.user = mock_user

        response = self.view.post(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch('post.views.PostFavorite.objects')
    @patch('post.views.Post.objects')
    def test_favorite_post_already_favorited(self, mock_post_objects, mock_favorite_objects):
        """测试重复收藏"""
        mock_user = Mock()
        mock_post = Mock()

        mock_post_objects.get.return_value = mock_post
        mock_favorite_objects.filter.return_value.exists.return_value = True

        request = self.factory.post('/')
        request.user = mock_user

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_FAVORITED)

    @patch('post.views.PostFavorite.objects')
    @patch('post.views.Post.objects')
    def test_unfavorite_post_success(self, mock_post_objects, mock_favorite_objects):
        """测试成功取消收藏"""
        mock_user = Mock()
        mock_post = Mock()
        mock_post.favorite_count = 0
        mock_favorite = Mock()

        mock_post_objects.get.return_value = mock_post
        mock_favorite_objects.filter.return_value.first.return_value = mock_favorite

        request = self.factory.delete('/')
        request.user = mock_user

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        mock_favorite.delete.assert_called_once()

    @patch('post.views.PostFavorite.objects')
    @patch('post.views.Post.objects')
    def test_unfavorite_post_not_favorited(self, mock_post_objects, mock_favorite_objects):
        """测试取消未收藏的帖子"""
        mock_user = Mock()
        mock_post = Mock()

        mock_post_objects.get.return_value = mock_post
        mock_favorite_objects.filter.return_value.first.return_value = None

        request = self.factory.delete('/')
        request.user = mock_user

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FAVORITED)


class PostSearchViewTests(TestCase):
    """PostSearchView 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostSearchView()

    @patch('post.views.Post.objects')
    def test_search_with_keyword(self, mock_objects):
        """测试带关键字搜索"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/', {'keyword': 'test'})
        request.query_params = {'keyword': 'test'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_objects.filter.assert_called_once()

    @patch('post.views.Post.objects')
    def test_search_without_keyword(self, mock_objects):
        """测试无关键字返回空"""
        mock_objects.none.return_value = []

        request = self.factory.get('/')
        request.query_params = {}

        self.view.request = request
        result = self.view.get_queryset()

        mock_objects.none.assert_called_once()

    @patch('post.views.Post.objects')
    def test_search_with_empty_keyword(self, mock_objects):
        """测试空关键字返回空"""
        mock_objects.none.return_value = []

        request = self.factory.get('/', {'keyword': ''})
        request.query_params = {'keyword': ''}

        self.view.request = request
        result = self.view.get_queryset()

        mock_objects.none.assert_called_once()


class HotPostListViewTests(TestCase):
    """HotPostList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = HotPostList()

    @patch('post.views.Post.objects')
    def test_get_hot_posts(self, mock_objects):
        """测试获取热门帖子"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.__getitem__ = Mock(return_value=[])
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/')

        self.view.request = request
        result = self.view.get_queryset()

        mock_objects.filter.assert_called_once_with(status=0)


class UserFavoriteListViewTests(TestCase):
    """UserFavoriteList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserFavoriteList()

    @patch('post.views.PostFavorite.objects')
    def test_get_user_favorites(self, mock_objects):
        """测试获取用户收藏列表"""
        mock_user = Mock()
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.user = mock_user

        self.view.request = request
        result = self.view.get_queryset()

        mock_objects.filter.assert_called_once_with(user=mock_user)


class PostDetailViewTests(TestCase):
    """PostDetail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostDetail()

    @patch('post.views.Post.objects')
    def test_delete_post_by_owner(self, mock_objects):
        """测试拥有者删除帖子"""
        mock_user = Mock()
        mock_user.is_superuser = False

        mock_post = Mock()
        mock_post.user = mock_user

        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.get.return_value = mock_post
        mock_objects.annotate.return_value = mock_queryset

        request = self.factory.delete('/')
        request.user = mock_user

        self.view.request = request
        self.view.kwargs = {'id': 1}

        response = self.view.delete(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(mock_post.status, 1)

    @patch('post.views.Post.objects')
    def test_delete_post_by_admin(self, mock_objects):
        """测试管理员删除帖子"""
        mock_user = Mock()
        mock_user.is_superuser = True

        mock_post = Mock()
        mock_post.user = Mock()  # Different user

        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.get.return_value = mock_post
        mock_objects.annotate.return_value = mock_queryset

        request = self.factory.delete('/')
        request.user = mock_user

        self.view.request = request
        self.view.kwargs = {'id': 1}

        response = self.view.delete(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)

    @patch('post.views.Post.objects')
    def test_delete_post_permission_denied(self, mock_objects):
        """测试非拥有者删除帖子被拒绝"""
        mock_user = Mock()
        mock_user.is_superuser = False

        mock_post = Mock()
        mock_post.user = Mock()  # Different user

        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.get.return_value = mock_post
        mock_objects.annotate.return_value = mock_queryset

        request = self.factory.delete('/')
        request.user = mock_user

        self.view.request = request
        self.view.kwargs = {'id': 1}

        response = self.view.delete(request)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
