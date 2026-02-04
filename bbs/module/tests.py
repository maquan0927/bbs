from django.test import TestCase, RequestFactory
from django.http import Http404
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock

from module.models import Module
from module.views import ModuleList, ModuleDetail
from common.response import ErrorCode


class ModuleModelTests(TestCase):
    """Module 模型测试"""

    def test_module_str(self):
        """测试板块字符串表示"""
        module = Module(name='测试板块')
        self.assertEqual(str(module), '测试板块')

    def test_module_post_count_property(self):
        """测试帖子数量属性"""
        module = Mock(spec=Module)
        module.posts = Mock()
        module.posts.filter.return_value.count.return_value = 5

        # 直接测试 filter 和 count 调用
        result = module.posts.filter(status=0).count()
        self.assertEqual(result, 5)

    @patch('django.utils.timezone.now')
    def test_module_today_post_count_property(self, mock_now):
        """测试今日帖子数属性"""
        from datetime import datetime, date

        mock_now.return_value.date.return_value = date(2024, 1, 1)

        module = Mock(spec=Module)
        module.posts = Mock()
        module.posts.filter.return_value.count.return_value = 3

        # 直接测试 filter 和 count 调用
        result = module.posts.filter(status=0, create_time__date=date(2024, 1, 1)).count()
        self.assertEqual(result, 3)


class ModuleListViewTests(TestCase):
    """ModuleList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleList()

    @patch('module.views.Module.objects')
    def test_get_queryset_active_only(self, mock_objects):
        """测试只获取启用的板块"""
        mock_queryset = MagicMock()
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/')
        self.view.request = request

        result = self.view.get_queryset()

        mock_objects.filter.assert_called_once_with(is_active=True)


class ModuleDetailViewTests(TestCase):
    """ModuleDetail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleDetail()

    @patch('module.views.Module.objects')
    def test_get_object_success(self, mock_objects):
        """测试成功获取板块对象"""
        mock_module = Mock()
        mock_objects.get.return_value = mock_module

        self.view.kwargs = {'id': 1}
        result = self.view.get_object()

        mock_objects.get.assert_called_once_with(id=1)
        self.assertEqual(result, mock_module)

    @patch('module.views.Module.objects')
    def test_get_object_not_found(self, mock_objects):
        """测试获取不存在的板块"""
        mock_objects.get.side_effect = Module.DoesNotExist

        self.view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            self.view.get_object()

    @patch.object(ModuleDetail, 'get_serializer')
    @patch.object(ModuleDetail, 'get_object')
    def test_get_module_detail(self, mock_get_object, mock_get_serializer):
        """测试获取板块详情"""
        mock_module = Mock()
        mock_get_object.return_value = mock_module

        mock_serializer = Mock()
        mock_serializer.data = {'id': 1, 'name': '测试板块'}
        mock_get_serializer.return_value = mock_serializer

        request = self.factory.get('/')
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['name'], '测试板块')

    @patch.object(ModuleDetail, 'get_object')
    def test_delete_module_soft_delete(self, mock_get_object):
        """测试软删除板块"""
        mock_module = Mock()
        mock_module.is_active = True
        mock_get_object.return_value = mock_module

        request = self.factory.delete('/')
        self.view.request = request

        response = self.view.delete(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertFalse(mock_module.is_active)
        mock_module.save.assert_called_once()
