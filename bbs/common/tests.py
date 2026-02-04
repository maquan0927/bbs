from django.test import TestCase, SimpleTestCase, RequestFactory
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from rest_framework.response import Response

from common.permissions import IsAdmin, IsLogin, IsOwnerOrReadOnly, IsModuleAdmin
from common.response import api_response, ErrorCode, ERROR_MESSAGES
from common.exception_handler import custom_exception_handler


class ErrorCodeTest(SimpleTestCase):
    """错误码常量测试"""

    def test_error_code_values(self):
        """测试错误码值"""
        self.assertEqual(ErrorCode.SUCCESS, 0)
        self.assertEqual(ErrorCode.PARAM_ERROR, 1001)
        self.assertEqual(ErrorCode.NOT_FOUND, 1002)
        self.assertEqual(ErrorCode.PERMISSION_DENIED, 1003)
        self.assertEqual(ErrorCode.USERNAME_EXISTS, 2001)
        self.assertEqual(ErrorCode.EMAIL_EXISTS, 2002)
        self.assertEqual(ErrorCode.CODE_ERROR, 2003)
        self.assertEqual(ErrorCode.POST_NOT_FOUND, 3001)
        self.assertEqual(ErrorCode.ALREADY_LIKED, 3002)
        self.assertEqual(ErrorCode.NOT_LIKED, 3003)
        self.assertEqual(ErrorCode.ALREADY_FAVORITED, 3004)
        self.assertEqual(ErrorCode.NOT_FAVORITED, 3005)

    def test_error_messages_defined(self):
        """测试错误消息已定义"""
        self.assertIn(ErrorCode.SUCCESS, ERROR_MESSAGES)
        self.assertIn(ErrorCode.PARAM_ERROR, ERROR_MESSAGES)
        self.assertIn(ErrorCode.NOT_FOUND, ERROR_MESSAGES)


class ApiResponseTest(SimpleTestCase):
    """api_response 函数测试"""

    def test_success_response_default(self):
        """测试默认成功响应"""
        response = api_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['message'], ERROR_MESSAGES[ErrorCode.SUCCESS])
        self.assertIsNone(response.data['data'])

    def test_success_response_with_data(self):
        """测试带数据的成功响应"""
        test_data = {'key': 'value'}
        response = api_response(data=test_data)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data'], test_data)

    def test_error_response_with_code(self):
        """测试错误响应"""
        response = api_response(code=ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], ERROR_MESSAGES[ErrorCode.NOT_FOUND])

    def test_custom_message(self):
        """测试自定义消息"""
        custom_msg = '自定义错误消息'
        response = api_response(code=ErrorCode.PARAM_ERROR, message=custom_msg)
        self.assertEqual(response.data['message'], custom_msg)

    def test_custom_http_status(self):
        """测试自定义 HTTP 状态码"""
        response = api_response(http_status=status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_error_code_message(self):
        """测试未知错误码的消息"""
        response = api_response(code=99999)
        self.assertEqual(response.data['message'], '未知错误')


class IsAdminPermissionTest(SimpleTestCase):
    """IsAdmin 权限类测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAdmin()

    def test_admin_user_has_permission(self):
        """测试管理员用户有权限"""
        request = self.factory.get('/')
        request.user = Mock(is_authenticated=True, is_superuser=True)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_non_admin_user_no_permission(self):
        """测试非管理员用户无权限"""
        request = self.factory.get('/')
        request.user = Mock(is_authenticated=True, is_superuser=False)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_anonymous_user_no_permission(self):
        """测试匿名用户无权限"""
        request = self.factory.get('/')
        request.user = None
        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_user_no_permission(self):
        """测试未认证用户无权限"""
        request = self.factory.get('/')
        request.user = Mock(is_authenticated=False, is_superuser=True)
        self.assertFalse(self.permission.has_permission(request, None))


class IsLoginPermissionTest(SimpleTestCase):
    """IsLogin 权限类测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsLogin()

    def test_get_request_allows_anonymous(self):
        """测试 GET 请求允许匿名访问"""
        request = self.factory.get('/')
        request.user = None
        self.assertTrue(self.permission.has_permission(request, None))

    def test_head_request_allows_anonymous(self):
        """测试 HEAD 请求允许匿名访问"""
        request = self.factory.head('/')
        request.user = None
        self.assertTrue(self.permission.has_permission(request, None))

    def test_options_request_allows_anonymous(self):
        """测试 OPTIONS 请求允许匿名访问"""
        request = self.factory.options('/')
        request.user = None
        self.assertTrue(self.permission.has_permission(request, None))

    def test_post_request_requires_login(self):
        """测试 POST 请求需要登录"""
        request = self.factory.post('/')
        request.user = Mock(is_authenticated=True)
        self.assertTrue(self.permission.has_permission(request, None))

    def test_post_request_denies_anonymous(self):
        """测试 POST 请求拒绝匿名用户"""
        request = self.factory.post('/')
        request.user = None
        self.assertFalse(self.permission.has_permission(request, None))

    def test_post_request_denies_unauthenticated(self):
        """测试 POST 请求拒绝未认证用户"""
        request = self.factory.post('/')
        request.user = Mock(is_authenticated=False)
        self.assertFalse(self.permission.has_permission(request, None))


class IsOwnerOrReadOnlyPermissionTest(SimpleTestCase):
    """IsOwnerOrReadOnly 权限类测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsOwnerOrReadOnly()

    def test_get_request_allows_all(self):
        """测试 GET 请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock(user=Mock())
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_admin_can_modify_any_object(self):
        """测试管理员可以修改任何对象"""
        request = self.factory.patch('/')
        request.user = Mock(is_superuser=True)
        obj = Mock(user=Mock())
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_owner_can_modify_own_object(self):
        """测试拥有者可以修改自己的对象"""
        request = self.factory.patch('/')
        user = Mock(is_superuser=False)
        request.user = user
        obj = Mock(user=user)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_owner_cannot_modify_object(self):
        """测试非拥有者不能修改对象"""
        request = self.factory.patch('/')
        request.user = Mock(is_superuser=False)
        obj = Mock(user=Mock())
        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class IsModuleAdminPermissionTest(SimpleTestCase):
    """IsModuleAdmin 权限类测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsModuleAdmin()

    def test_get_request_allows_all(self):
        """测试 GET 请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_superuser_can_modify(self):
        """测试超级管理员可以修改"""
        request = self.factory.patch('/')
        request.user = Mock(is_superuser=True)
        obj = Mock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_module_admin_can_modify(self):
        """测试板块管理员可以修改"""
        request = self.factory.patch('/')
        user = Mock(is_superuser=False)
        request.user = user
        module = Mock()
        module.admin.all.return_value = [user]
        obj = Mock(module=module)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_module_admin_cannot_modify(self):
        """测试非板块管理员不能修改"""
        request = self.factory.patch('/')
        user = Mock(is_superuser=False)
        request.user = user
        module = Mock()
        module.admin.all.return_value = []
        obj = Mock(module=module)
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_object_without_module_returns_false(self):
        """测试没有 module 属性的对象返回 False"""
        request = self.factory.patch('/')
        request.user = Mock(is_superuser=False)
        obj = Mock(spec=[])  # 没有 module 属性
        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class CustomExceptionHandlerTest(SimpleTestCase):
    """自定义异常处理器测试"""

    def test_returns_none_when_no_exception(self):
        """测试没有异常时返回 None"""
        with patch('common.exception_handler.exception_handler', return_value=None):
            result = custom_exception_handler(Exception(), {})
            self.assertIsNone(result)

    def test_handles_401_unauthorized(self):
        """测试处理 401 未授权异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_401_UNAUTHORIZED
        with patch('common.exception_handler.exception_handler', return_value=mock_response):
            result = custom_exception_handler(Exception(), {'view': None})
            self.assertEqual(result.data['code'], ErrorCode.PERMISSION_DENIED)
            self.assertEqual(result.data['message'], '认证失败，请先登录')

    def test_handles_403_forbidden(self):
        """测试处理 403 禁止访问异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        with patch('common.exception_handler.exception_handler', return_value=mock_response):
            result = custom_exception_handler(Exception(), {'view': None})
            self.assertEqual(result.data['code'], ErrorCode.PERMISSION_DENIED)
            self.assertEqual(result.data['message'], '权限不足')

    def test_handles_404_not_found(self):
        """测试处理 404 未找到异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        with patch('common.exception_handler.exception_handler', return_value=mock_response):
            result = custom_exception_handler(Exception(), {'view': None})
            self.assertEqual(result.data['code'], ErrorCode.NOT_FOUND)
            self.assertEqual(result.data['message'], '资源不存在')

    def test_handles_400_bad_request(self):
        """测试处理 400 请求错误异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'detail': 'error'}
        with patch('common.exception_handler.exception_handler', return_value=mock_response):
            result = custom_exception_handler(Exception(), {'view': None})
            self.assertEqual(result.data['code'], ErrorCode.PARAM_ERROR)
            self.assertEqual(result.data['message'], '请求参数错误')

    def test_returns_original_response_for_other_status(self):
        """测试其他状态码返回原始响应"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        with patch('common.exception_handler.exception_handler', return_value=mock_response):
            result = custom_exception_handler(Exception(), {'view': None})
            self.assertEqual(result, mock_response)
