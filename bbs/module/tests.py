from django.test import TestCase
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from rest_framework.test import force_authenticate
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from django.utils import timezone

from module.models import Module
from module.views import ModuleList, ModuleDetail
from common.response import ErrorCode

User = get_user_model()


class ModuleModelTests(TestCase):
    """Module 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.module = Module.objects.create(
            name='测试板块',
            description='测试板块描述',
            is_active=True
        )

    def tearDown(self):
        # 清理时需要先删除 Post，避免外键约束问题
        from post.models import Post
        Post.objects.all().delete()
        Module.objects.all().delete()
        User.objects.all().delete()

    def test_module_str_representation(self):
        """测试板块字符串表示"""
        self.assertEqual(str(self.module), '测试板块')

    def test_module_default_values(self):
        """测试板块默认值"""
        module = Module.objects.create(name='新板块')
        self.assertEqual(module.description, '')
        self.assertEqual(module.icon, '')
        self.assertEqual(module.sort_order, 0)
        self.assertTrue(module.is_active)

    def test_post_count_property(self):
        """测试帖子数量属性"""
        from post.models import Post
        # 初始没有帖子
        self.assertEqual(self.module.post_count, 0)

        # 创建正常帖子
        Post.objects.create(
            title='测试帖子1',
            content='内容1',
            user=self.user,
            module=self.module,
            status=0  # 正常状态
        )
        Post.objects.create(
            title='测试帖子2',
            content='内容2',
            user=self.user,
            module=self.module,
            status=0
        )
        # 创建已删除帖子（不应该被统计）
        Post.objects.create(
            title='已删除帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=1  # 已删除
        )

        self.assertEqual(self.module.post_count, 2)

    def test_today_post_count_property(self):
        """测试今日帖子数属性"""
        from post.models import Post
        # 初始没有帖子
        self.assertEqual(self.module.today_post_count, 0)

        # 创建今日帖子
        Post.objects.create(
            title='今日帖子',
            content='内容',
            user=self.user,
            module=self.module,
            status=0
        )

        self.assertEqual(self.module.today_post_count, 1)

    def test_module_ordering(self):
        """测试板块排序"""
        module1 = Module.objects.create(name='板块A', sort_order=2)
        module2 = Module.objects.create(name='板块B', sort_order=1)
        module3 = Module.objects.create(name='板块C', sort_order=1)  # 相同排序，按创建时间倒序

        modules = list(Module.objects.all())
        # sort_order 升序
        self.assertEqual(modules[0].sort_order, 0)  # self.module
        self.assertEqual(modules[1].sort_order, 1)

    def test_module_unique_name(self):
        """测试板块名称唯一性"""
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Module.objects.create(name='测试板块')  # 已存在的名称


class ModuleListViewTests(TestCase):
    """ModuleList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.normal_user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='normalpass123'
        )
        # 创建测试板块
        self.active_module = Module.objects.create(
            name='活跃板块',
            description='活跃描述',
            is_active=True
        )
        self.inactive_module = Module.objects.create(
            name='禁用板块',
            description='禁用描述',
            is_active=False
        )

    def tearDown(self):
        from post.models import Post
        Post.objects.all().delete()
        Module.objects.all().delete()
        User.objects.all().delete()

    def test_get_queryset_only_active_modules(self):
        """测试只返回启用的板块"""
        view = ModuleList()
        request = self.factory.get('/api/module/')
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().name, '活跃板块')

    def test_list_modules_anonymous(self):
        """测试匿名用户可以获取板块列表"""
        view = ModuleList.as_view()
        request = self.factory.get('/api/module/')

        response = view(request)
        # ListAPIView 返回列表
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModuleDetailViewTests(TestCase):
    """ModuleDetail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.normal_user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='normalpass123'
        )
        self.module = Module.objects.create(
            name='测试板块',
            description='测试描述',
            is_active=True
        )

    def tearDown(self):
        from post.models import Post
        Post.objects.all().delete()
        Module.objects.all().delete()
        User.objects.all().delete()

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
        view.kwargs = {'id': 9999}

        with self.assertRaises(Http404):
            view.get_object()

    def test_get_module_detail(self):
        """测试获取板块详情"""
        view = ModuleDetail.as_view()
        request = self.factory.get(f'/api/module/{self.module.id}/')
        force_authenticate(request, user=self.admin_user)

        response = view(request, id=self.module.id)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['name'], '测试板块')

    def test_soft_delete_module(self):
        """测试软删除板块"""
        view = ModuleDetail.as_view()
        request = self.factory.delete(f'/api/module/{self.module.id}/')
        force_authenticate(request, user=self.admin_user)

        # 验证初始状态
        self.assertTrue(self.module.is_active)

        response = view(request, id=self.module.id)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        # 刷新数据库
        self.module.refresh_from_db()
        self.assertFalse(self.module.is_active)

    def test_module_admin_many_to_many(self):
        """测试板块管理员多对多关系"""
        self.module.admin.add(self.admin_user)
        self.module.admin.add(self.normal_user)

        admins = list(self.module.admin.all())
        self.assertEqual(len(admins), 2)
        self.assertIn(self.admin_user, admins)
        self.assertIn(self.normal_user, admins)
