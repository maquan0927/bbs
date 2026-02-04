from django.test import TestCase, RequestFactory
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from rest_framework.response import Response

from common.permissions import IsAdmin, IsLogin, IsOwnerOrReadOnly, IsModuleAdmin
from common.response import api_response, ErrorCode, ERROR_MESSAGES
from common.exception_handler import custom_exception_handler


class IsAdminPermissionTest(TestCase):
    """IsAdmin 权限测试"""

    def setUp(self):
        self.permission = IsAdmin()
        self.factory = RequestFactory()

    def test_has_permission_with_superuser(self):
        """测试超级管理员有权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_superuser = True

        result = self.permission.has_permission(request, None)
        self.assertTrue(result)

    def test_has_permission_with_normal_user(self):
        """测试普通用户无权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_superuser = False

        result = self.permission.has_permission(request, None)
        self.assertFalse(result)

    def test_has_permission_with_unauthenticated_user(self):
        """测试未登录用户无权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.user.is_superuser = False

        result = self.permission.has_permission(request, None)
        self.assertFalse(result)

    def test_has_permission_with_none_user(self):
        """测试 user 为 None 的情况"""
        request = self.factory.get('/')
        request.user = None

        result = self.permission.has_permission(request, None)
        self.assertFalse(result)


class IsLoginPermissionTest(TestCase):
    """IsLogin 权限测试"""

    def setUp(self):
        self.permission = IsLogin()
        self.factory = RequestFactory()

    def test_get_request_allows_anonymous(self):
        """测试 GET 请求允许匿名访问"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False

        result = self.permission.has_permission(request, None)
        self.assertTrue(result)

    def test_head_request_allows_anonymous(self):
        """测试 HEAD 请求允许匿名访问"""
        request = self.factory.head('/')
        request.user = Mock()
        request.user.is_authenticated = False

        result = self.permission.has_permission(request, None)
        self.assertTrue(result)

    def test_options_request_allows_anonymous(self):
        """测试 OPTIONS 请求允许匿名访问"""
        request = self.factory.options('/')
        request.user = Mock()
        request.user.is_authenticated = False

        result = self.permission.has_permission(request, None)
        self.assertTrue(result)

    def test_post_request_requires_login(self):
        """测试 POST 请求需要登录"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = False

        result = self.permission.has_permission(request, None)
        self.assertFalse(result)

    def test_post_request_with_authenticated_user(self):
        """测试已登录用户可以 POST"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = True

        result = self.permission.has_permission(request, None)
        self.assertTrue(result)

    def test_delete_request_requires_login(self):
        """测试 DELETE 请求需要登录"""
        request = self.factory.delete('/')
        request.user = Mock()
        request.user.is_authenticated = False

        result = self.permission.has_permission(request, None)
        self.assertFalse(result)


class IsOwnerOrReadOnlyPermissionTest(TestCase):
    """IsOwnerOrReadOnly 权限测试"""

    def setUp(self):
        self.permission = IsOwnerOrReadOnly()
        self.factory = RequestFactory()

    def test_get_request_allows_all(self):
        """测试 GET 请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()

        result = self.permission.has_object_permission(request, None, obj)
        self.assertTrue(result)

    def test_superuser_can_modify_any_object(self):
        """测试超级管理员可以修改任何对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()
        obj.user = Mock()  # 不同的用户

        result = self.permission.has_object_permission(request, None, obj)
        self.assertTrue(result)

    def test_owner_can_modify_own_object(self):
        """测试拥有者可以修改自己的对象"""
        request = self.factory.post('/')
        user = Mock()
        user.is_superuser = False
        request.user = user
        obj = Mock()
        obj.user = user  # 同一个用户

        result = self.permission.has_object_permission(request, None, obj)
        self.assertTrue(result)

    def test_non_owner_cannot_modify(self):
        """测试非拥有者无法修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False
        obj = Mock()
        obj.user = Mock()  # 不同的用户

        result = self.permission.has_object_permission(request, None, obj)
        self.assertFalse(result)


class IsModuleAdminPermissionTest(TestCase):
    """IsModuleAdmin 权限测试"""

    def setUp(self):
        self.permission = IsModuleAdmin()
        self.factory = RequestFactory()

    def test_get_request_allows_all(self):
        """测试 GET 请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()

        result = self.permission.has_object_permission(request, None, obj)
        self.assertTrue(result)

    def test_superuser_can_modify(self):
        """测试超级管理员可以修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()

        result = self.permission.has_object_permission(request, None, obj)
        self.assertTrue(result)

    def test_module_admin_can_modify(self):
        """测试板块管理员可以修改"""
        request = self.factory.post('/')
        user = Mock()
        user.is_superuser = False
        request.user = user

        module = Mock()
        module.admin.all.return_value = [user]

        obj = Mock()
        obj.module = module

        result = self.permission.has_object_permission(request, None, obj)
        self.assertTrue(result)

    def test_non_admin_cannot_modify(self):
        """测试非管理员无法修改"""
        request = self.factory.post('/')
        user = Mock()
        user.is_superuser = False
        request.user = user

        module = Mock()
        module.admin.all.return_value = []  # 空管理员列表

        obj = Mock()
        obj.module = module

        result = self.permission.has_object_permission(request, None, obj)
        self.assertFalse(result)

    def test_object_without_module(self):
        """测试没有 module 属性的对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock(spec=[])  # 没有 module 属性

        result = self.permission.has_object_permission(request, None, obj)
        self.assertFalse(result)


class ApiResponseTest(TestCase):
    """api_response 函数测试"""

    def test_success_response_default(self):
        """测试默认成功响应"""
        response = api_response()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['message'], '成功')
        self.assertIsNone(response.data['data'])

    def test_response_with_data(self):
        """测试带数据的响应"""
        test_data = {'key': 'value'}
        response = api_response(data=test_data)

        self.assertEqual(response.data['data'], test_data)

    def test_response_with_custom_message(self):
        """测试自定义消息"""
        response = api_response(message='自定义消息')

        self.assertEqual(response.data['message'], '自定义消息')

    def test_response_with_error_code(self):
        """测试错误码响应"""
        response = api_response(code=ErrorCode.PARAM_ERROR)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], ERROR_MESSAGES[ErrorCode.PARAM_ERROR])

    def test_response_with_custom_http_status(self):
        """测试自定义 HTTP 状态码"""
        response = api_response(http_status=status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_response_with_all_error_codes(self):
        """测试所有预定义的错误码"""
        for code, message in ERROR_MESSAGES.items():
            response = api_response(code=code)
            self.assertEqual(response.data['code'], code)
            self.assertEqual(response.data['message'], message)


class ErrorCodeTest(TestCase):
    """ErrorCode 错误码测试"""

    def test_error_code_values(self):
        """测试错误码值"""
        self.assertEqual(ErrorCode.SUCCESS, 0)
        self.assertEqual(ErrorCode.PARAM_ERROR, 1001)
        self.assertEqual(ErrorCode.NOT_FOUND, 1002)
        self.assertEqual(ErrorCode.PERMISSION_DENIED, 1003)
        self.assertEqual(ErrorCode.POST_NOT_FOUND, 3001)
        self.assertEqual(ErrorCode.ALREADY_LIKED, 3002)

    def test_error_messages_mapping(self):
        """测试错误消息映射"""
        self.assertIn(ErrorCode.SUCCESS, ERROR_MESSAGES)
        self.assertIn(ErrorCode.PARAM_ERROR, ERROR_MESSAGES)
        self.assertIn(ErrorCode.NOT_FOUND, ERROR_MESSAGES)


class CustomExceptionHandlerTest(TestCase):
    """custom_exception_handler 异常处理测试"""

    def setUp(self):
        self.context = {'view': Mock()}

    @patch('common.exception_handler.exception_handler')
    def test_handles_401_unauthorized(self, mock_handler):
        """测试处理 401 未授权异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_401_UNAUTHORIZED
        mock_handler.return_value = mock_response

        exc = Exception('Unauthorized')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '认证失败，请先登录')

    @patch('common.exception_handler.exception_handler')
    def test_handles_403_forbidden(self, mock_handler):
        """测试处理 403 禁止访问异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        mock_handler.return_value = mock_response

        exc = Exception('Forbidden')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '权限不足')

    @patch('common.exception_handler.exception_handler')
    def test_handles_404_not_found(self, mock_handler):
        """测试处理 404 未找到异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_handler.return_value = mock_response

        exc = Exception('Not Found')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '资源不存在')

    @patch('common.exception_handler.exception_handler')
    def test_handles_400_bad_request(self, mock_handler):
        """测试处理 400 请求错误异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'field': ['error']}
        mock_handler.return_value = mock_response

        exc = Exception('Bad Request')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '请求参数错误')

    @patch('common.exception_handler.exception_handler')
    def test_handles_none_response(self, mock_handler):
        """测试处理 None 响应（非 DRF 异常）"""
        mock_handler.return_value = None

        exc = Exception('Unknown Error')
        response = custom_exception_handler(exc, self.context)

        self.assertIsNone(response)
