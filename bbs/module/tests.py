from django.test import TestCase, RequestFactory
from django.http import Http404
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock, PropertyMock

from module.models import Module
from module.views import ModuleList, ModuleDetail
from common.response import ErrorCode


class ModuleModelTests(TestCase):
    """测试板块模型"""

    @patch.object(Module, 'posts', create=True)
    def test_post_count_property(self, mock_posts):
        """测试帖子数量属性"""
        mock_queryset = Mock()
        mock_queryset.count.return_value = 10
        mock_posts.filter.return_value = mock_queryset

        module = Module()
        count = module.post_count

        mock_posts.filter.assert_called_once_with(status=0)
        self.assertEqual(count, 10)

    @patch('module.models.timezone')
    @patch.object(Module, 'posts', create=True)
    def test_today_post_count_property(self, mock_posts, mock_timezone):
        """测试今日帖子数属性"""
        from datetime import date
        mock_today = date(2026, 2, 4)
        mock_now = Mock()
        mock_now.date.return_value = mock_today
        mock_timezone.now.return_value = mock_now

        mock_queryset = Mock()
        mock_queryset.count.return_value = 5
        mock_posts.filter.return_value = mock_queryset

        module = Module()
        count = module.today_post_count

        mock_posts.filter.assert_called_once_with(status=0, create_time__date=mock_today)
        self.assertEqual(count, 5)

    def test_module_str(self):
        """测试模型字符串表示"""
        module = Module(name='测试板块')
        self.assertEqual(str(module), '测试板块')


class ModuleListViewTests(TestCase):
    """测试板块列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleList()

    @patch.object(Module.objects, 'filter')
    def test_get_queryset_returns_active_modules(self, mock_filter):
        """测试获取启用的板块"""
        mock_queryset = Mock()
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        self.view.request = request
        result = self.view.get_queryset()

        mock_filter.assert_called_once_with(is_active=True)


class ModuleDetailViewTests(TestCase):
    """测试板块详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleDetail()

    @patch.object(Module.objects, 'get')
    def test_get_object_success(self, mock_get):
        """测试成功获取板块对象"""
        mock_module = Mock()
        mock_get.return_value = mock_module

        self.view.kwargs = {'id': 1}
        result = self.view.get_object()

        mock_get.assert_called_once_with(id=1)
        self.assertEqual(result, mock_module)

    @patch.object(Module.objects, 'get')
    def test_get_object_not_found(self, mock_get):
        """测试板块不存在抛出404"""
        mock_get.side_effect = Module.DoesNotExist()

        self.view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            self.view.get_object()

    @patch('module.views.ModuleSerializer')
    @patch.object(ModuleDetail, 'get_object')
    def test_get_returns_api_response(self, mock_get_object, mock_serializer):
        """测试获取板块详情返回统一响应"""
        mock_module = Mock()
        mock_get_object.return_value = mock_module
        mock_serializer.return_value.data = {'id': 1, 'name': '测试板块'}

        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_superuser = True
        request.user.is_authenticated = True

        self.view.request = request
        self.view.format_kwarg = None
        self.view.kwargs = {'id': 1}

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertIsNotNone(response.data['data'])

    @patch.object(ModuleDetail, 'get_object')
    def test_delete_soft_deletes_module(self, mock_get_object):
        """测试软删除板块"""
        mock_module = Mock()
        mock_module.is_active = True
        mock_get_object.return_value = mock_module

        request = self.factory.delete('/')
        request.user = Mock()
        request.user.is_superuser = True
        request.user.is_authenticated = True

        self.view.request = request
        self.view.kwargs = {'id': 1}

        response = self.view.delete(request)

        self.assertFalse(mock_module.is_active)
        mock_module.save.assert_called_once()
        self.assertEqual(response.data['message'], '删除成功')
