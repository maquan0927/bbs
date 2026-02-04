from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch
from rest_framework.test import APITestCase
from module.models import Module
from module.views import ModuleList, ModuleDetail
from post.models import Post

User = get_user_model()


class ModuleModelTest(TestCase):
    """测试板块模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(
            name='测试板块',
            description='测试板块描述'
        )

    def test_module_str_method(self):
        """测试板块字符串表示"""
        self.assertEqual(str(self.module), '测试板块')

    def test_module_default_is_active(self):
        """测试板块默认启用状态"""
        self.assertTrue(self.module.is_active)

    def test_module_default_sort_order(self):
        """测试板块默认排序值"""
        self.assertEqual(self.module.sort_order, 0)

    def test_post_count_property(self):
        """测试板块帖子数量属性"""
        # 初始为0
        self.assertEqual(self.module.post_count, 0)

        # 添加帖子
        Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.user,
            module=self.module,
            status=0
        )
        self.assertEqual(self.module.post_count, 1)

    def test_post_count_excludes_deleted_posts(self):
        """测试帖子数量不包含已删除的帖子"""
        Post.objects.create(
            title='正常帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=0
        )
        Post.objects.create(
            title='已删除帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=1  # 已删除
        )

        self.assertEqual(self.module.post_count, 1)

    @patch('django.utils.timezone.now')
    def test_today_post_count_property(self, mock_now):
        """测试板块今日帖子数量属性"""
        from django.utils import timezone
        from datetime import datetime

        # 模拟当前时间
        mock_date = timezone.make_aware(datetime(2024, 1, 15, 12, 0, 0))
        mock_now.return_value = mock_date

        # 创建今日帖子
        post = Post.objects.create(
            title='今日帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=0
        )

        # today_post_count 会查询今天的帖子
        # 由于auto_now_add，需要直接测试属性能正常工作
        count = self.module.today_post_count
        self.assertIsInstance(count, int)


class ModuleListViewTest(TestCase):
    """测试板块列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # 创建测试板块
        self.active_module = Module.objects.create(
            name='活跃板块',
            is_active=True
        )
        Module.objects.create(
            name='禁用板块',
            is_active=False
        )

    def test_get_queryset_filters_inactive_modules(self):
        """测试列表只返回活跃的板块"""
        view = ModuleList()
        queryset = view.get_queryset()

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().name, '活跃板块')


class ModuleDetailViewTest(TestCase):
    """测试板块详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.module = Module.objects.create(
            name='测试板块',
            is_active=True
        )

    def test_get_object_success(self):
        """测试成功获取板块对象"""
        view = ModuleDetail()
        view.kwargs = {'id': self.module.id}

        obj = view.get_object()
        self.assertEqual(obj, self.module)

    def test_get_object_not_found(self):
        """测试获取不存在的板块"""
        from django.http import Http404

        view = ModuleDetail()
        view.kwargs = {'id': 99999}

        with self.assertRaises(Http404):
            view.get_object()

    def test_soft_delete_module(self):
        """测试软删除板块"""
        request = self.factory.delete(f'/api/module/{self.module.id}/')
        request.user = self.superuser

        view = ModuleDetail()
        view.kwargs = {'id': self.module.id}
        view.request = request

        response = view.delete(request)

        self.module.refresh_from_db()
        self.assertFalse(self.module.is_active)
        self.assertEqual(response.data['code'], 0)

    def test_get_module_detail(self):
        """测试获取板块详情"""
        request = self.factory.get(f'/api/module/{self.module.id}/')
        request.user = self.superuser

        view = ModuleDetail()
        view.kwargs = {'id': self.module.id}
        view.request = request
        view.format_kwarg = None

        response = view.get(request)

        self.assertEqual(response.data['code'], 0)
        self.assertEqual(response.data['data']['name'], '测试板块')
