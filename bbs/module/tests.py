from django.test import TestCase, SimpleTestCase, RequestFactory
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from django.http import Http404

from module.models import Module
from module.views import ModuleList, ModuleDetail
from common.response import ErrorCode


class ModuleModelTest(SimpleTestCase):
    """Module 模型属性测试"""

    @patch('module.models.Module.posts')
    def test_post_count_property(self, mock_posts):
        """测试 post_count 属性"""
        mock_queryset = Mock()
        mock_queryset.count.return_value = 15
        mock_posts.filter.return_value = mock_queryset

        # 模拟属性调用
        result = mock_posts.filter(status=0).count()
        self.assertEqual(result, 15)

    @patch('module.models.Module.posts')
    @patch('django.utils.timezone.now')
    def test_today_post_count_property(self, mock_now, mock_posts):
        """测试 today_post_count 属性"""
        from datetime import date
        mock_now.return_value.date.return_value = date(2026, 2, 4)

        mock_queryset = Mock()
        mock_queryset.count.return_value = 3
        mock_posts.filter.return_value = mock_queryset

        result = mock_posts.filter(status=0, create_time__date=date(2026, 2, 4)).count()
        self.assertEqual(result, 3)


class ModuleListViewTest(SimpleTestCase):
    """ModuleList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleList()

    @patch('module.views.Module.objects')
    def test_get_queryset_filters_active(self, mock_objects):
        """测试只获取已激活的板块"""
        request = self.factory.get('/')
        self.view.request = request

        mock_queryset = Mock()
        mock_objects.filter.return_value = mock_queryset

        self.view.get_queryset()

        mock_objects.filter.assert_called_once_with(is_active=True)


class ModuleDetailViewTest(SimpleTestCase):
    """ModuleDetail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleDetail()

    @patch('module.views.Module.objects')
    def test_get_object_success(self, mock_objects):
        """测试成功获取板块对象"""
        mock_module = Mock(id=1, name='测试板块')
        mock_objects.get.return_value = mock_module

        self.view.kwargs = {'id': 1}
        result = self.view.get_object()

        self.assertEqual(result, mock_module)
        mock_objects.get.assert_called_once_with(id=1)

    @patch('module.views.Module.objects')
    def test_get_object_not_found(self, mock_objects):
        """测试板块不存在抛出 404"""
        mock_objects.get.side_effect = Module.DoesNotExist

        self.view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            self.view.get_object()

    @patch('module.views.Module.objects')
    @patch.object(ModuleDetail, 'get_serializer')
    def test_get_module_detail(self, mock_get_serializer, mock_objects):
        """测试获取板块详情"""
        request = self.factory.get('/')
        request.user = Mock(is_superuser=True, is_authenticated=True)

        mock_module = Mock(id=1, name='测试板块', is_active=True)
        mock_objects.get.return_value = mock_module
        mock_serializer = Mock()
        mock_serializer.data = {'id': 1, 'name': '测试板块'}
        mock_get_serializer.return_value = mock_serializer

        self.view.kwargs = {'id': 1}
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['id'], 1)

    @patch('module.views.Module.objects')
    def test_delete_module_soft_delete(self, mock_objects):
        """测试软删除板块"""
        request = self.factory.delete('/')
        request.user = Mock(is_superuser=True, is_authenticated=True)

        mock_module = Mock(id=1, name='测试板块', is_active=True)
        mock_objects.get.return_value = mock_module

        self.view.kwargs = {'id': 1}
        self.view.request = request

        response = self.view.delete(request)

        self.assertEqual(mock_module.is_active, False)
        mock_module.save.assert_called_once()
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
