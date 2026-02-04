from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from post.models import Post, RePost, PostLike, PostFavorite
from post.views import (
    PostList, PostDetail, RepostList, PostLikeView, PostFavoriteView,
    UserFavoriteList, PostSearchView, HotPostList
)
from post.serializers import PostSerializer, RepostSerializer
from module.models import Module

User = get_user_model()


class PostModelTest(TestCase):
    """测试帖子模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module
        )

    def test_post_str_method(self):
        """测试帖子字符串表示"""
        self.assertEqual(str(self.post), '测试帖子')

    def test_post_default_status(self):
        """测试帖子默认状态为正常"""
        self.assertEqual(self.post.status, 0)

    def test_post_default_view_count(self):
        """测试帖子默认浏览量为0"""
        self.assertEqual(self.post.view_count, 0)

    def test_post_like_count_property(self):
        """测试帖子点赞数属性"""
        # 初始为0
        self.assertEqual(self.post.like_count, 0)

        # 添加点赞
        PostLike.objects.create(user=self.user, post=self.post)
        self.assertEqual(self.post.like_count, 1)

    def test_post_favorite_count_property(self):
        """测试帖子收藏数属性"""
        # 初始为0
        self.assertEqual(self.post.favorite_count, 0)

        # 添加收藏
        PostFavorite.objects.create(user=self.user, post=self.post)
        self.assertEqual(self.post.favorite_count, 1)

    def test_post_reply_count_property(self):
        """测试帖子回复数属性"""
        # 初始为0
        self.assertEqual(self.post.reply_count, 0)

        # 添加回复
        RePost.objects.create(content='测试回复', user=self.user, post=self.post)
        self.assertEqual(self.post.reply_count, 1)


class RePostModelTest(TestCase):
    """测试回帖模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module
        )

    def test_repost_str_method(self):
        """测试回帖字符串表示"""
        repost = RePost.objects.create(
            content='测试回复',
            user=self.user,
            post=self.post
        )
        self.assertEqual(str(repost), f'{self.user.username}的回复')

    def test_repost_str_without_user(self):
        """测试无用户的回帖字符串表示"""
        repost = RePost.objects.create(
            content='匿名回复',
            user=None,
            post=self.post
        )
        self.assertEqual(str(repost), '匿名的回复')

    def test_repost_parent_child_relationship(self):
        """测试回帖的父子关系"""
        parent_repost = RePost.objects.create(
            content='父回复',
            user=self.user,
            post=self.post
        )
        child_repost = RePost.objects.create(
            content='子回复',
            user=self.user,
            post=self.post,
            parent=parent_repost
        )

        self.assertEqual(parent_repost.children.count(), 1)
        self.assertEqual(child_repost.parent, parent_repost)


class PostLikeModelTest(TestCase):
    """测试帖子点赞模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module
        )

    def test_post_like_str_method(self):
        """测试点赞字符串表示"""
        like = PostLike.objects.create(user=self.user, post=self.post)
        self.assertEqual(str(like), f'{self.user.username} 赞了 {self.post.title}')

    def test_unique_constraint(self):
        """测试用户对同一帖子只能点赞一次"""
        PostLike.objects.create(user=self.user, post=self.post)

        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            PostLike.objects.create(user=self.user, post=self.post)


class PostFavoriteModelTest(TestCase):
    """测试帖子收藏模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module
        )

    def test_post_favorite_str_method(self):
        """测试收藏字符串表示"""
        favorite = PostFavorite.objects.create(user=self.user, post=self.post)
        self.assertEqual(str(favorite), f'{self.user.username} 收藏了 {self.post.title}')


class PostListViewTest(TestCase):
    """测试帖子列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')

        # 创建测试帖子
        self.post1 = Post.objects.create(
            title='帖子1',
            content='内容1',
            user=self.user,
            module=self.module,
            status=0,
            is_essence=True
        )
        self.post2 = Post.objects.create(
            title='帖子2',
            content='内容2',
            user=self.user,
            module=self.module,
            status=0
        )
        # 已删除的帖子
        Post.objects.create(
            title='已删除帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=1
        )

    def test_get_queryset_filters_deleted_posts(self):
        """测试列表只返回正常状态的帖子"""
        request = self.factory.get('/')
        request.user = self.user
        request.query_params = {}

        view = PostList()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)

    def test_get_queryset_filter_by_module(self):
        """测试按板块筛选帖子"""
        request = self.factory.get('/', {'module': self.module.id})
        request.user = self.user
        request.query_params = {'module': str(self.module.id)}

        view = PostList()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)

    def test_get_queryset_filter_by_user(self):
        """测试按用户筛选帖子"""
        request = self.factory.get('/', {'user': self.user.id})
        request.user = self.user
        request.query_params = {'user': str(self.user.id)}

        view = PostList()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)

    def test_get_queryset_filter_by_essence(self):
        """测试筛选精华帖"""
        request = self.factory.get('/', {'is_essence': 'true'})
        request.user = self.user
        request.query_params = {'is_essence': 'true'}

        view = PostList()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        # 使用 values_list 获取 ID 再查询原始对象
        post_ids = list(queryset.values_list('id', flat=True))
        post = Post.objects.get(id=post_ids[0])
        self.assertTrue(post.is_essence)


class PostLikeViewTest(TestCase):
    """测试点赞视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module,
            status=0
        )

    def test_like_post_success(self):
        """测试成功点赞帖子"""
        request = self.factory.post(f'/api/post/{self.post.id}/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.post(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 0)
        self.assertTrue(PostLike.objects.filter(user=self.user, post=self.post).exists())

    def test_like_nonexistent_post(self):
        """测试点赞不存在的帖子"""
        request = self.factory.post('/api/post/99999/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.post(request, post_id=99999)

        self.assertEqual(response.data['code'], 3001)  # POST_NOT_FOUND

    def test_like_already_liked_post(self):
        """测试重复点赞"""
        PostLike.objects.create(user=self.user, post=self.post)

        request = self.factory.post(f'/api/post/{self.post.id}/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.post(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 3002)  # ALREADY_LIKED

    def test_unlike_post_success(self):
        """测试成功取消点赞"""
        PostLike.objects.create(user=self.user, post=self.post)

        request = self.factory.delete(f'/api/post/{self.post.id}/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.delete(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 0)
        self.assertFalse(PostLike.objects.filter(user=self.user, post=self.post).exists())

    def test_unlike_not_liked_post(self):
        """测试取消未点赞的帖子"""
        request = self.factory.delete(f'/api/post/{self.post.id}/like/')
        request.user = self.user

        view = PostLikeView()
        response = view.delete(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 3003)  # NOT_LIKED


class PostFavoriteViewTest(TestCase):
    """测试收藏视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module,
            status=0
        )

    def test_favorite_post_success(self):
        """测试成功收藏帖子"""
        request = self.factory.post(f'/api/post/{self.post.id}/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.post(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 0)
        self.assertTrue(PostFavorite.objects.filter(user=self.user, post=self.post).exists())

    def test_favorite_nonexistent_post(self):
        """测试收藏不存在的帖子"""
        request = self.factory.post('/api/post/99999/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.post(request, post_id=99999)

        self.assertEqual(response.data['code'], 3001)  # POST_NOT_FOUND

    def test_favorite_already_favorited_post(self):
        """测试重复收藏"""
        PostFavorite.objects.create(user=self.user, post=self.post)

        request = self.factory.post(f'/api/post/{self.post.id}/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.post(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 3004)  # ALREADY_FAVORITED

    def test_unfavorite_post_success(self):
        """测试成功取消收藏"""
        PostFavorite.objects.create(user=self.user, post=self.post)

        request = self.factory.delete(f'/api/post/{self.post.id}/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.delete(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 0)
        self.assertFalse(PostFavorite.objects.filter(user=self.user, post=self.post).exists())

    def test_unfavorite_not_favorited_post(self):
        """测试取消未收藏的帖子"""
        request = self.factory.delete(f'/api/post/{self.post.id}/favorite/')
        request.user = self.user

        view = PostFavoriteView()
        response = view.delete(request, post_id=self.post.id)

        self.assertEqual(response.data['code'], 3005)  # NOT_FAVORITED


class PostSearchViewTest(TestCase):
    """测试帖子搜索视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')

        Post.objects.create(
            title='Python教程',
            content='学习Python',
            user=self.user,
            module=self.module,
            status=0
        )
        Post.objects.create(
            title='Java教程',
            content='学习Java',
            user=self.user,
            module=self.module,
            status=0
        )

    def test_search_by_title(self):
        """测试按标题搜索"""
        request = self.factory.get('/', {'keyword': 'Python'})
        request.user = self.user
        request.query_params = {'keyword': 'Python'}

        view = PostSearchView()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        # 使用 values_list 获取 ID 再查询原始对象
        post_ids = list(queryset.values_list('id', flat=True))
        post = Post.objects.get(id=post_ids[0])
        self.assertEqual(post.title, 'Python教程')

    def test_search_by_content(self):
        """测试按内容搜索"""
        request = self.factory.get('/', {'keyword': '学习'})
        request.user = self.user
        request.query_params = {'keyword': '学习'}

        view = PostSearchView()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)

    def test_search_without_keyword(self):
        """测试无关键词搜索返回空"""
        request = self.factory.get('/')
        request.user = self.user
        request.query_params = {}

        view = PostSearchView()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 0)


class HotPostListViewTest(TestCase):
    """测试热门帖子列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')

        # 创建帖子，设置不同浏览量
        self.hot_post = Post.objects.create(
            title='热门帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=0,
            view_count=100
        )
        Post.objects.create(
            title='普通帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=0,
            view_count=10
        )

    def test_hot_posts_order_by_view_count(self):
        """测试热门帖子按浏览量排序"""
        request = self.factory.get('/')
        request.user = self.user

        view = HotPostList()
        view.request = request

        queryset = view.get_queryset()
        # 使用 values_list 获取 ID 再查询原始对象
        post_ids = list(queryset.values_list('id', flat=True))
        post = Post.objects.get(id=post_ids[0])
        self.assertEqual(post.title, '热门帖子')


class PostSerializerTest(TestCase):
    """测试帖子序列化器"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module
        )

    def test_get_is_liked_authenticated_user(self):
        """测试认证用户的点赞状态"""
        PostLike.objects.create(user=self.user, post=self.post)

        # 使用完整的 Mock 对象
        request = Mock()
        request.user = self.user

        serializer = PostSerializer(self.post, context={'request': request})
        self.assertTrue(serializer.data['is_liked'])

    def test_get_is_liked_anonymous_user(self):
        """测试匿名用户的点赞状态"""
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        serializer = PostSerializer(self.post, context={'request': request})
        self.assertFalse(serializer.data['is_liked'])

    def test_get_is_favorited_authenticated_user(self):
        """测试认证用户的收藏状态"""
        PostFavorite.objects.create(user=self.user, post=self.post)

        # 使用完整的 Mock 对象
        request = Mock()
        request.user = self.user

        serializer = PostSerializer(self.post, context={'request': request})
        self.assertTrue(serializer.data['is_favorited'])


class RepostSerializerTest(TestCase):
    """测试回帖序列化器"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(name='测试板块')
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module
        )
        self.repost = RePost.objects.create(
            content='测试回复',
            user=self.user,
            post=self.post
        )

    def test_get_user_info_with_user(self):
        """测试有用户的回帖用户信息"""
        serializer = RepostSerializer(self.repost)
        user_info = serializer.data['user_info']

        self.assertEqual(user_info['id'], self.user.id)
        self.assertEqual(user_info['username'], self.user.username)

    def test_get_user_info_without_user(self):
        """测试无用户的回帖用户信息"""
        repost = RePost.objects.create(
            content='匿名回复',
            user=None,
            post=self.post
        )
        serializer = RepostSerializer(repost)

        self.assertIsNone(serializer.data['user_info'])

    def test_get_children_with_nested_replies(self):
        """测试获取嵌套回复"""
        child_repost = RePost.objects.create(
            content='子回复',
            user=self.user,
            post=self.post,
            parent=self.repost
        )

        serializer = RepostSerializer(self.repost)
        children = serializer.data['children']

        self.assertEqual(len(children), 1)
        self.assertEqual(children[0]['content'], '子回复')
