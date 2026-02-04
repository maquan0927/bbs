from django.test import TestCase, RequestFactory
from django.http import Http404
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock, PropertyMock

from post.models import Post, RePost, PostLike, PostFavorite
from post.views import (
    PostList, PostDetail, PostLikeView, PostFavoriteView,
    UserFavoriteList, PostSearchView, HotPostList, RepostList
)
from post.serializers import PostSerializer, RepostSerializer
from common.response import ErrorCode


class PostModelTests(TestCase):
    """测试帖子模型"""

    @patch.object(Post, 'likes', create=True)
    def test_like_count_property(self, mock_likes):
        """测试点赞数属性"""
        mock_likes.count.return_value = 15

        post = Post()
        count = post.like_count

        self.assertEqual(count, 15)

    @patch.object(Post, 'favorites', create=True)
    def test_favorite_count_property(self, mock_favorites):
        """测试收藏数属性"""
        mock_favorites.count.return_value = 8

        post = Post()
        count = post.favorite_count

        self.assertEqual(count, 8)

    @patch.object(Post, 'reposts', create=True)
    def test_reply_count_property(self, mock_reposts):
        """测试回复数属性"""
        mock_reposts.count.return_value = 20

        post = Post()
        count = post.reply_count

        self.assertEqual(count, 20)

    def test_post_str(self):
        """测试帖子字符串表示"""
        post = Post(title='测试帖子')
        self.assertEqual(str(post), '测试帖子')

    def test_post_status_options(self):
        """测试帖子状态选项"""
        status_options = dict(Post.status_options)
        self.assertEqual(status_options[0], '正常')
        self.assertEqual(status_options[1], '已删除')
        self.assertEqual(status_options[2], '待审核')


class RePostModelTests(TestCase):
    """测试回帖模型"""

    def test_repost_str_with_user(self):
        """测试回帖字符串表示-有用户"""
        mock_user = Mock()
        mock_user.username = 'testuser'

        repost = RePost()
        repost.user = mock_user

        self.assertEqual(str(repost), 'testuser的回复')

    def test_repost_str_without_user(self):
        """测试回帖字符串表示-匿名"""
        repost = RePost()
        repost.user = None

        self.assertEqual(str(repost), '匿名的回复')


class PostLikeModelTests(TestCase):
    """测试帖子点赞模型"""

    def test_post_like_str(self):
        """测试点赞字符串表示"""
        mock_user = Mock()
        mock_user.username = 'testuser'

        mock_post = Mock()
        mock_post.title = '测试帖子'

        like = PostLike()
        like.user = mock_user
        like.post = mock_post

        self.assertEqual(str(like), 'testuser 赞了 测试帖子')


class PostFavoriteModelTests(TestCase):
    """测试帖子收藏模型"""

    def test_post_favorite_str(self):
        """测试收藏字符串表示"""
        mock_user = Mock()
        mock_user.username = 'testuser'

        mock_post = Mock()
        mock_post.title = '测试帖子'

        favorite = PostFavorite()
        favorite.user = mock_user
        favorite.post = mock_post

        self.assertEqual(str(favorite), 'testuser 收藏了 测试帖子')


class PostListViewTests(TestCase):
    """测试帖子列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostList()

    @patch.object(Post.objects, 'filter')
    def test_get_queryset_basic(self, mock_filter):
        """测试获取基本帖子列表"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.query_params = {}
        self.view.request = request

        result = self.view.get_queryset()

        mock_filter.assert_called_once_with(status=0)

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

        request = self.factory.get('/', {'user': '2'})
        request.query_params = {'user': '2'}
        self.view.request = request

        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(user_id='2')

    @patch.object(Post.objects, 'filter')
    def test_get_queryset_filter_essence(self, mock_filter):
        """测试精华帖筛选"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'is_essence': 'true'})
        request.query_params = {'is_essence': 'true'}
        self.view.request = request

        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(is_essence=True)


class PostDetailViewTests(TestCase):
    """测试帖子详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostDetail()

    @patch.object(Post.objects, 'annotate')
    def test_get_object_success(self, mock_annotate):
        """测试成功获取帖子对象"""
        mock_post = Mock()
        mock_queryset = Mock()
        mock_queryset.get.return_value = mock_post
        mock_annotate.return_value = mock_queryset

        self.view.kwargs = {'id': 1}
        result = self.view.get_object()

        self.assertEqual(result, mock_post)

    @patch.object(Post.objects, 'annotate')
    def test_get_object_not_found(self, mock_annotate):
        """测试帖子不存在抛出404"""
        mock_queryset = Mock()
        mock_queryset.get.side_effect = Post.DoesNotExist()
        mock_annotate.return_value = mock_queryset

        self.view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            self.view.get_object()

    @patch.object(Post.objects, 'filter')
    @patch('post.views.PostSerializer')
    @patch.object(PostDetail, 'get_object')
    def test_get_increments_view_count(self, mock_get_object, mock_serializer, mock_filter):
        """测试获取帖子详情增加浏览量"""
        mock_post = Mock()
        mock_post.id = 1
        mock_post.view_count = 10
        mock_get_object.return_value = mock_post
        mock_serializer.return_value.data = {'id': 1}

        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True

        self.view.request = request
        self.view.format_kwarg = None
        self.view.kwargs = {'id': 1}

        response = self.view.get(request)

        mock_filter.assert_called_with(id=1)

    @patch.object(PostDetail, 'get_object')
    def test_delete_soft_deletes_post(self, mock_get_object):
        """测试软删除帖子"""
        mock_post = Mock()
        mock_post.status = 0
        mock_user = Mock()
        mock_post.user = mock_user
        mock_get_object.return_value = mock_post

        request = self.factory.delete('/')
        request.user = mock_user

        self.view.request = request
        self.view.kwargs = {'id': 1}

        response = self.view.delete(request)

        self.assertEqual(mock_post.status, 1)
        mock_post.save.assert_called_once()
        self.assertEqual(response.data['message'], '删除成功')

    @patch.object(PostDetail, 'get_object')
    def test_delete_permission_denied(self, mock_get_object):
        """测试删除帖子无权限"""
        mock_post = Mock()
        mock_post.user = Mock()
        mock_get_object.return_value = mock_post

        request = self.factory.delete('/')
        request.user = Mock()
        request.user.is_superuser = False

        self.view.request = request
        self.view.kwargs = {'id': 1}

        response = self.view.delete(request)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)


class PostLikeViewTests(TestCase):
    """测试帖子点赞视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostLikeView()

    @patch.object(Post.objects, 'get')
    def test_like_post_not_found(self, mock_get):
        """测试点赞-帖子不存在"""
        mock_get.side_effect = Post.DoesNotExist()

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

        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_LIKED)

    @patch.object(PostLike.objects, 'create')
    @patch.object(PostLike.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_like_success(self, mock_get, mock_filter, mock_create):
        """测试点赞成功"""
        mock_post = Mock()
        mock_post.like_count = 10
        mock_get.return_value = mock_post

        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        request = self.factory.post('/')
        mock_user = Mock()
        request.user = mock_user

        response = self.view.post(request, post_id=1)

        mock_create.assert_called_once_with(user=mock_user, post=mock_post)
        self.assertEqual(response.data['message'], '点赞成功')

    @patch.object(Post.objects, 'get')
    def test_unlike_post_not_found(self, mock_get):
        """测试取消点赞-帖子不存在"""
        mock_get.side_effect = Post.DoesNotExist()

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch.object(PostLike.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_unlike_not_liked(self, mock_get, mock_filter):
        """测试取消点赞-未点赞"""
        mock_post = Mock()
        mock_get.return_value = mock_post

        mock_queryset = Mock()
        mock_queryset.first.return_value = None
        mock_filter.return_value = mock_queryset

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_LIKED)

    @patch.object(PostLike.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_unlike_success(self, mock_get, mock_filter):
        """测试取消点赞成功"""
        mock_post = Mock()
        mock_post.like_count = 9
        mock_get.return_value = mock_post

        mock_like = Mock()
        mock_queryset = Mock()
        mock_queryset.first.return_value = mock_like
        mock_filter.return_value = mock_queryset

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=1)

        mock_like.delete.assert_called_once()
        self.assertEqual(response.data['message'], '取消点赞成功')


class PostFavoriteViewTests(TestCase):
    """测试帖子收藏视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostFavoriteView()

    @patch.object(Post.objects, 'get')
    def test_favorite_post_not_found(self, mock_get):
        """测试收藏-帖子不存在"""
        mock_get.side_effect = Post.DoesNotExist()

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

        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset

        request = self.factory.post('/')
        request.user = Mock()

        response = self.view.post(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.ALREADY_FAVORITED)

    @patch.object(PostFavorite.objects, 'create')
    @patch.object(PostFavorite.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_favorite_success(self, mock_get, mock_filter, mock_create):
        """测试收藏成功"""
        mock_post = Mock()
        mock_post.favorite_count = 5
        mock_get.return_value = mock_post

        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        request = self.factory.post('/')
        mock_user = Mock()
        request.user = mock_user

        response = self.view.post(request, post_id=1)

        mock_create.assert_called_once_with(user=mock_user, post=mock_post)
        self.assertEqual(response.data['message'], '收藏成功')

    @patch.object(Post.objects, 'get')
    def test_unfavorite_post_not_found(self, mock_get):
        """测试取消收藏-帖子不存在"""
        mock_get.side_effect = Post.DoesNotExist()

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=999)

        self.assertEqual(response.data['code'], ErrorCode.POST_NOT_FOUND)

    @patch.object(PostFavorite.objects, 'filter')
    @patch.object(Post.objects, 'get')
    def test_unfavorite_not_favorited(self, mock_get, mock_filter):
        """测试取消收藏-未收藏"""
        mock_post = Mock()
        mock_get.return_value = mock_post

        mock_queryset = Mock()
        mock_queryset.first.return_value = None
        mock_filter.return_value = mock_queryset

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, post_id=1)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FAVORITED)


class UserFavoriteListViewTests(TestCase):
    """测试用户收藏列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserFavoriteList()

    @patch.object(PostFavorite.objects, 'filter')
    def test_get_queryset(self, mock_filter):
        """测试获取用户收藏列表"""
        mock_queryset = Mock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        mock_user = Mock()
        request.user = mock_user
        self.view.request = request

        result = self.view.get_queryset()

        mock_filter.assert_called_once_with(user=mock_user)


class PostSearchViewTests(TestCase):
    """测试帖子搜索视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = PostSearchView()

    @patch.object(Post.objects, 'none')
    def test_get_queryset_empty_keyword(self, mock_none):
        """测试空关键词返回空结果"""
        mock_none.return_value = []

        request = self.factory.get('/', {'keyword': ''})
        request.query_params = {'keyword': ''}
        self.view.request = request

        result = self.view.get_queryset()

        mock_none.assert_called_once()

    @patch.object(Post.objects, 'filter')
    def test_get_queryset_with_keyword(self, mock_filter):
        """测试带关键词搜索"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'keyword': '测试'})
        request.query_params = {'keyword': '测试'}
        self.view.request = request

        result = self.view.get_queryset()

        mock_filter.assert_called_once()


class HotPostListViewTests(TestCase):
    """测试热门帖子列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = HotPostList()

    @patch.object(Post.objects, 'filter')
    def test_get_queryset(self, mock_filter):
        """测试获取热门帖子"""
        mock_queryset = Mock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value.__getitem__ = Mock(return_value=[])
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        self.view.request = request

        result = self.view.get_queryset()

        mock_filter.assert_called_once_with(status=0)


class PostSerializerTests(TestCase):
    """测试帖子序列化器"""

    def test_get_is_liked_unauthenticated(self):
        """测试未认证用户返回False"""
        serializer = PostSerializer()
        serializer.context = {'request': None}

        mock_post = Mock()
        result = serializer.get_is_liked(mock_post)

        self.assertFalse(result)

    @patch.object(PostLike.objects, 'filter')
    def test_get_is_liked_authenticated_liked(self, mock_filter):
        """测试已认证用户已点赞"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset

        mock_request = Mock()
        mock_request.user.is_authenticated = True

        serializer = PostSerializer()
        serializer.context = {'request': mock_request}

        mock_post = Mock()
        result = serializer.get_is_liked(mock_post)

        self.assertTrue(result)

    def test_get_is_favorited_unauthenticated(self):
        """测试未认证用户返回False"""
        serializer = PostSerializer()
        serializer.context = {'request': None}

        mock_post = Mock()
        result = serializer.get_is_favorited(mock_post)

        self.assertFalse(result)

    @patch.object(PostFavorite.objects, 'filter')
    def test_get_is_favorited_authenticated_favorited(self, mock_filter):
        """测试已认证用户已收藏"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset

        mock_request = Mock()
        mock_request.user.is_authenticated = True

        serializer = PostSerializer()
        serializer.context = {'request': mock_request}

        mock_post = Mock()
        result = serializer.get_is_favorited(mock_post)

        self.assertTrue(result)


class RepostSerializerTests(TestCase):
    """测试回帖序列化器"""

    def test_get_user_info_with_user(self):
        """测试获取用户信息-有用户"""
        serializer = RepostSerializer()

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = None

        mock_repost = Mock()
        mock_repost.user = mock_user

        result = serializer.get_user_info(mock_repost)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['username'], 'testuser')
        self.assertIsNone(result['avatar'])

    def test_get_user_info_without_user(self):
        """测试获取用户信息-无用户"""
        serializer = RepostSerializer()

        mock_repost = Mock()
        mock_repost.user = None

        result = serializer.get_user_info(mock_repost)

        self.assertIsNone(result)

    @patch.object(RepostSerializer, '__init__', lambda x, *args, **kwargs: None)
    def test_get_children_empty(self):
        """测试获取子回复-空"""
        serializer = RepostSerializer()

        mock_repost = Mock()
        mock_children = Mock()
        mock_children.all.return_value = []
        mock_repost.children = mock_children

        result = serializer.get_children(mock_repost)

        self.assertEqual(result, [])
