from django.test import TestCase
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from rest_framework.test import force_authenticate
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from post.models import Post, RePost, PostLike, PostFavorite
from module.models import Module
from common.response import ErrorCode

User = get_user_model()


class PostModelTests(TestCase):
    """Post 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(
            name='测试板块',
            is_active=True
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module,
            status=0
        )

    def tearDown(self):
        PostLike.objects.all().delete()
        PostFavorite.objects.all().delete()
        RePost.objects.all().delete()
        Post.objects.all().delete()
        Module.objects.all().delete()
        User.objects.all().delete()

    def test_post_str_representation(self):
        """测试帖子字符串表示"""
        self.assertEqual(str(self.post), '测试帖子')

    def test_post_default_values(self):
        """测试帖子默认值"""
        post = Post.objects.create(
            title='新帖子',
            content='内容',
            user=self.user
        )
        self.assertEqual(post.view_count, 0)
        self.assertFalse(post.is_top)
        self.assertFalse(post.is_essence)
        self.assertEqual(post.status, 0)

    def test_like_count_property(self):
        """测试点赞数属性"""
        self.assertEqual(self.post.like_count, 0)

        # 添加点赞
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        PostLike.objects.create(user=self.user, post=self.post)
        PostLike.objects.create(user=user2, post=self.post)

        self.assertEqual(self.post.like_count, 2)

    def test_favorite_count_property(self):
        """测试收藏数属性"""
        self.assertEqual(self.post.favorite_count, 0)

        # 添加收藏
        PostFavorite.objects.create(user=self.user, post=self.post)

        self.assertEqual(self.post.favorite_count, 1)

    def test_reply_count_property(self):
        """测试回复数属性"""
        self.assertEqual(self.post.reply_count, 0)

        # 添加回复
        RePost.objects.create(
            content='回复内容1',
            user=self.user,
            post=self.post
        )
        RePost.objects.create(
            content='回复内容2',
            user=self.user,
            post=self.post
        )

        self.assertEqual(self.post.reply_count, 2)

    def test_post_ordering(self):
        """测试帖子排序（置顶优先，时间倒序）"""
        post2 = Post.objects.create(
            title='普通帖子',
            content='内容',
            user=self.user,
            is_top=False
        )
        post3 = Post.objects.create(
            title='置顶帖子',
            content='内容',
            user=self.user,
            is_top=True
        )

        posts = list(Post.objects.all())
        # 置顶帖子应该在最前面
        self.assertTrue(posts[0].is_top)


class RePostModelTests(TestCase):
    """RePost 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user
        )

    def tearDown(self):
        RePost.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_repost_str_representation(self):
        """测试回帖字符串表示"""
        repost = RePost.objects.create(
            content='回复内容',
            user=self.user,
            post=self.post
        )
        self.assertIn(self.user.username, str(repost))

    def test_repost_str_anonymous(self):
        """测试匿名回帖字符串表示"""
        repost = RePost.objects.create(
            content='回复内容',
            user=None,
            post=self.post
        )
        self.assertIn('匿名', str(repost))

    def test_repost_nested_reply(self):
        """测试嵌套回复"""
        parent = RePost.objects.create(
            content='父回复',
            user=self.user,
            post=self.post
        )
        child = RePost.objects.create(
            content='子回复',
            user=self.user,
            post=self.post,
            parent=parent
        )

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())


class PostLikeModelTests(TestCase):
    """PostLike 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user
        )

    def tearDown(self):
        PostLike.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_like_str_representation(self):
        """测试点赞字符串表示"""
        like = PostLike.objects.create(user=self.user, post=self.post)
        self.assertIn(self.user.username, str(like))
        self.assertIn(self.post.title, str(like))

    def test_like_unique_together(self):
        """测试用户对同一帖子只能点赞一次"""
        PostLike.objects.create(user=self.user, post=self.post)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PostLike.objects.create(user=self.user, post=self.post)


class PostFavoriteModelTests(TestCase):
    """PostFavorite 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user
        )

    def tearDown(self):
        PostFavorite.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_favorite_str_representation(self):
        """测试收藏字符串表示"""
        fav = PostFavorite.objects.create(user=self.user, post=self.post)
        self.assertIn(self.user.username, str(fav))
        self.assertIn(self.post.title, str(fav))

    def test_favorite_unique_together(self):
        """测试用户对同一帖子只能收藏一次"""
        PostFavorite.objects.create(user=self.user, post=self.post)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PostFavorite.objects.create(user=self.user, post=self.post)


class PostBusinessLogicTests(TestCase):
    """Post 业务逻辑测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            status=0
        )

    def tearDown(self):
        PostLike.objects.all().delete()
        PostFavorite.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_soft_delete_post(self):
        """测试软删除帖子"""
        self.assertEqual(self.post.status, 0)
        self.post.status = 1
        self.post.save()
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 1)

    def test_view_count_increment(self):
        """测试浏览量增加"""
        initial_count = self.post.view_count
        self.post.view_count += 1
        self.post.save()
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, initial_count + 1)

    def test_post_filter_by_status(self):
        """测试按状态筛选帖子"""
        deleted_post = Post.objects.create(
            title='已删除帖子',
            content='内容',
            user=self.user,
            status=1
        )

        active_posts = Post.objects.filter(status=0)
        self.assertEqual(active_posts.count(), 1)
        self.assertEqual(active_posts.first().title, '测试帖子')

    def test_post_top_and_essence(self):
        """测试置顶和精华帖子"""
        top_post = Post.objects.create(
            title='置顶帖子',
            content='内容',
            user=self.user,
            is_top=True
        )
        essence_post = Post.objects.create(
            title='精华帖子',
            content='内容',
            user=self.user,
            is_essence=True
        )

        top_posts = Post.objects.filter(is_top=True)
        essence_posts = Post.objects.filter(is_essence=True)

        self.assertEqual(top_posts.count(), 1)
        self.assertEqual(essence_posts.count(), 1)


class PostSearchTests(TestCase):
    """帖子搜索测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post1 = Post.objects.create(
            title='Python 入门教程',
            content='学习 Python 编程',
            user=self.user,
            status=0
        )
        self.post2 = Post.objects.create(
            title='Django 开发指南',
            content='Web 开发框架',
            user=self.user,
            status=0
        )
        self.post3 = Post.objects.create(
            title='已删除的帖子',
            content='这是一个包含 Python 的已删除帖子',
            user=self.user,
            status=1
        )

    def tearDown(self):
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_search_by_title(self):
        """测试按标题搜索"""
        posts = Post.objects.filter(title__icontains='Python', status=0)
        self.assertEqual(posts.count(), 1)
        self.assertEqual(posts.first().title, 'Python 入门教程')

    def test_search_by_content(self):
        """测试按内容搜索"""
        posts = Post.objects.filter(content__icontains='Web', status=0)
        self.assertEqual(posts.count(), 1)
        self.assertEqual(posts.first().title, 'Django 开发指南')

    def test_search_excludes_deleted_posts(self):
        """测试搜索结果不包含已删除帖子"""
        posts = Post.objects.filter(content__icontains='Python', status=0)
        # 已删除的帖子虽然包含 Python，但不应该出现在结果中
        for post in posts:
            self.assertEqual(post.status, 0)


class HotPostTests(TestCase):
    """热门帖子测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post1 = Post.objects.create(
            title='热门帖子',
            content='内容',
            user=self.user,
            status=0,
            view_count=100
        )
        self.post2 = Post.objects.create(
            title='普通帖子',
            content='内容',
            user=self.user,
            status=0,
            view_count=10
        )
        self.post3 = Post.objects.create(
            title='超热门帖子',
            content='内容',
            user=self.user,
            status=0,
            view_count=1000
        )

    def tearDown(self):
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_hot_posts_ordered_by_view_count(self):
        """测试热门帖子按浏览量排序"""
        posts = Post.objects.filter(status=0).order_by('-view_count')
        view_counts = [post.view_count for post in posts]
        self.assertEqual(view_counts, sorted(view_counts, reverse=True))

    def test_hot_posts_limit(self):
        """测试热门帖子数量限制"""
        # 创建更多帖子
        for i in range(15):
            Post.objects.create(
                title=f'帖子{i}',
                content='内容',
                user=self.user,
                status=0,
                view_count=i * 10
            )

        posts = Post.objects.filter(status=0).order_by('-view_count')[:10]
        self.assertLessEqual(posts.count(), 10)
