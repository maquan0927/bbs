from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from django.http import Http404

from module.models import Module
from module.views import ModuleList, ModuleDetail
from common.response import ErrorCode

User = get_user_model()


class ModuleModelTestCase(TestCase):
    """测试板块模型"""

    def test_module_meta_ordering(self):
        """测试板块排序"""
        self.assertEqual(Module._meta.ordering, ['sort_order', '-create_time'])

    def test_module_meta_verbose_name(self):
        """测试板块verbose_name"""
        self.assertEqual(Module._meta.verbose_name, '板块')

    @patch.object(Module, 'posts', new_callable=PropertyMock)
    def test_module_post_count_property(self, mock_posts):
        """测试帖子数量属性"""
        mock_queryset = Mock()
        mock_queryset.filter.return_value.count.return_value = 10
        mock_posts.return_value = mock_queryset

        module = Module()
        result = module.post_count

        self.assertEqual(result, 10)
        mock_queryset.filter.assert_called_with(status=0)

    @patch('django.utils.timezone')
    @patch.object(Module, 'posts', new_callable=PropertyMock)
    def test_module_today_post_count_property(self, mock_posts, mock_timezone):
        """测试今日帖子数属性"""
        mock_date = Mock()
        mock_timezone.now.return_value.date.return_value = mock_date

        mock_queryset = Mock()
        mock_queryset.filter.return_value.count.return_value = 5
        mock_posts.return_value = mock_queryset

        module = Module()
        result = module.today_post_count

        self.assertEqual(result, 5)


class ModuleListViewTestCase(TestCase):
    """测试板块列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleList()

    @patch.object(Module.objects, 'filter')
    def test_get_queryset_active_only(self, mock_filter):
        """测试只获取启用的板块"""
        mock_queryset = Mock()
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        self.view.request = request

        result = self.view.get_queryset()

        mock_filter.assert_called_with(is_active=True)

    def test_serializer_class(self):
        """测试序列化器类"""
        from module.serializers import ModuleSerializer
        self.assertEqual(self.view.serializer_class, ModuleSerializer)

    def test_pagination_class_is_none(self):
        """测试分页器为None"""
        self.assertIsNone(self.view.pagination_class)


class ModuleDetailViewTestCase(TestCase):
    """测试板块详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ModuleDetail()

    @patch.object(Module.objects, 'get')
    def test_get_object_not_found(self, mock_get):
        """测试获取不存在的板块"""
        mock_get.side_effect = Module.DoesNotExist

        self.view.kwargs = {'id': 999}

        with self.assertRaises(Http404):
            self.view.get_object()

    @patch.object(Module.objects, 'get')
    def test_get_object_success(self, mock_get):
        """测试成功获取板块"""
        mock_module = Mock()
        mock_get.return_value = mock_module

        self.view.kwargs = {'id': 1}

        result = self.view.get_object()

        self.assertEqual(result, mock_module)
        mock_get.assert_called_with(id=1)

    @patch.object(ModuleDetail, 'get_serializer')
    @patch.object(ModuleDetail, 'get_object')
    def test_get_returns_api_response(self, mock_get_object, mock_get_serializer):
        """测试GET请求返回api_response"""
        mock_module = Mock()
        mock_get_object.return_value = mock_module

        mock_serializer = Mock()
        mock_serializer.data = {'id': 1, 'name': 'Test'}
        mock_get_serializer.return_value = mock_serializer

        request = self.factory.get('/')
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], 0)
        self.assertEqual(response.data['data'], {'id': 1, 'name': 'Test'})

    @patch.object(ModuleDetail, 'get_object')
    def test_delete_soft_delete(self, mock_get_object):
        """测试软删除板块"""
        mock_module = Mock()
        mock_module.is_active = True
        mock_get_object.return_value = mock_module

        request = self.factory.delete('/')
        self.view.request = request

        response = self.view.delete(request)

        self.assertFalse(mock_module.is_active)
        mock_module.save.assert_called_once()
        self.assertEqual(response.data['message'], '删除成功')
