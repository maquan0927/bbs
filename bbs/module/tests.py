from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import Http404
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from module.models import Module
from module.views import ModuleList, ModuleDetail

User = get_user_model()


class ModuleModelTest(TestCase):
    """Module 模型测试"""

    def test_module_str_method(self):
        """测试 Module 的 __str__ 方法"""
        module = Module()
        module.name = '测试板块'

        self.assertEqual(str(module), '测试板块')

    def test_module_default_values(self):
        """测试 Module 的默认值"""
        module = Module()

        self.assertEqual(module.description, '')
        self.assertEqual(module.icon, '')
        self.assertEqual(module.sort_order, 0)
        self.assertTrue(module.is_active)

    @patch.object(Module, 'posts', create=True)
    def test_post_count_property(self, mock_posts):
        """测试帖子数量属性"""
        mock_filter = MagicMock()
        mock_filter.count.return_value = 15
        mock_posts.filter.return_value = mock_filter

        module = Module()
        count = module.post_count

        mock_posts.filter.assert_called_with(status=0)
        self.assertEqual(count, 15)

    @patch.object(Module, 'posts', create=True)
    @patch('django.utils.timezone.now')
    def test_today_post_count_property(self, mock_now, mock_posts):
        """测试今日帖子数属性"""
        from datetime import date
        mock_date = date(2026, 2, 4)
        mock_now.return_value.date.return_value = mock_date

        mock_filter = MagicMock()
        mock_filter.count.return_value = 3
        mock_posts.filter.return_value = mock_filter

        module = Module()
        count = module.today_post_count

        mock_posts.filter.assert_called_with(status=0, create_time__date=mock_date)
        self.assertEqual(count, 3)


class ModuleListViewTest(TestCase):
    """ModuleList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True
        self.user.is_superuser = False

    @patch('module.views.Module.objects.filter')
    def test_get_queryset_returns_active_modules(self, mock_filter):
        """测试获取激活状态的板块"""
        mock_queryset = MagicMock()
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/api/module/')
        request.user = self.user

        view = ModuleList()
        view.request = request

        view.get_queryset()
        mock_filter.assert_called_with(is_active=True)


class ModuleDetailViewTest(TestCase):
    """ModuleDetail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True
        self.user.is_superuser = True

    @patch('module.views.Module.objects.get')
    def test_get_object_success(self, mock_get):
        """测试成功获取板块"""
        mock_module = Mock()
        mock_module.id = 1
        mock_module.name = '测试板块'
        mock_get.return_value = mock_module

        view = ModuleDetail()
        view.kwargs = {'id': 1}

        result = view.get_object()
        self.assertEqual(result, mock_module)
        mock_get.assert_called_with(id=1)

    @patch('module.views.Module.objects.get')
    def test_get_object_not_found(self, mock_get):
        """测试板块不存在"""
        mock_get.side_effect = Module.DoesNotExist()

        view = ModuleDetail()
        view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            view.get_object()

    @patch('module.views.ModuleSerializer')
    @patch('module.views.Module.objects.get')
    def test_get_module_detail(self, mock_get, mock_serializer):
        """测试获取板块详情"""
        mock_module = Mock()
        mock_module.id = 1
        mock_get.return_value = mock_module
        mock_serializer.return_value.data = {'id': 1, 'name': '测试板块'}

        request = self.factory.get('/api/module/1/')
        request.user = self.user

        view = ModuleDetail()
        view.request = request
        view.kwargs = {'id': 1}
        view.format_kwarg = None
        # Mock the get_serializer method
        view.get_serializer = lambda instance: mock_serializer(instance)

        response = view.get(request)

        self.assertEqual(response.data['code'], 0)

    @patch('module.views.Module.objects.get')
    def test_delete_module_soft_delete(self, mock_get):
        """测试软删除板块"""
        mock_module = Mock()
        mock_module.id = 1
        mock_module.is_active = True
        mock_get.return_value = mock_module

        request = self.factory.delete('/api/module/1/')
        request.user = self.user

        view = ModuleDetail()
        view.request = request
        view.kwargs = {'id': 1}

        response = view.delete(request)

        self.assertFalse(mock_module.is_active)
        mock_module.save.assert_called_once()
        self.assertEqual(response.data['message'], '删除成功')

    @patch('module.views.Module.objects.get')
    def test_delete_module_not_found(self, mock_get):
        """测试删除不存在的板块"""
        mock_get.side_effect = Module.DoesNotExist()

        request = self.factory.delete('/api/module/999/')
        request.user = self.user

        view = ModuleDetail()
        view.request = request
        view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            view.delete(request)
