from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, NotFound, ValidationError
from unittest.mock import Mock, MagicMock, patch

from common.response import api_response, ErrorCode, ERROR_MESSAGES
from common.permissions import IsAdmin, IsLogin, IsOwnerOrReadOnly, IsModuleAdmin
from common.exception_handler import custom_exception_handler


class ApiResponseTests(TestCase):
    """api_response 函数测试"""

    def test_api_response_success_default(self):
        """测试默认成功响应"""
        response = api_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['message'], ERROR_MESSAGES[ErrorCode.SUCCESS])
        self.assertIsNone(response.data['data'])

    def test_api_response_with_data(self):
        """测试带数据的响应"""
        test_data = {'key': 'value', 'count': 10}
        response = api_response(data=test_data)
        self.assertEqual(response.data['data'], test_data)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)

    def test_api_response_with_error_code(self):
        """测试错误码响应"""
        response = api_response(code=ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], ERROR_MESSAGES[ErrorCode.PARAM_ERROR])

    def test_api_response_with_custom_message(self):
        """测试自定义消息"""
        custom_msg = '自定义错误消息'
        response = api_response(code=ErrorCode.NOT_FOUND, message=custom_msg)
        self.assertEqual(response.data['message'], custom_msg)

    def test_api_response_with_http_status(self):
        """测试自定义HTTP状态码"""
        response = api_response(http_status=status.HTTP_201_CREATED)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_response_unknown_error_code(self):
        """测试未知错误码返回未知错误"""
        response = api_response(code=99999)
        self.assertEqual(response.data['message'], '未知错误')


class ErrorCodeTests(TestCase):
    """ErrorCode 常量测试"""

    def test_error_codes_defined(self):
        """测试错误码定义"""
        self.assertEqual(ErrorCode.SUCCESS, 0)
        self.assertEqual(ErrorCode.PARAM_ERROR, 1001)
        self.assertEqual(ErrorCode.NOT_FOUND, 1002)
        self.assertEqual(ErrorCode.PERMISSION_DENIED, 1003)
        self.assertEqual(ErrorCode.ALREADY_LIKED, 3002)
        self.assertEqual(ErrorCode.NOT_LIKED, 3003)

    def test_error_messages_mapping(self):
        """测试错误消息映射"""
        self.assertIn(ErrorCode.SUCCESS, ERROR_MESSAGES)
        self.assertIn(ErrorCode.PARAM_ERROR, ERROR_MESSAGES)
        self.assertIn(ErrorCode.NOT_FOUND, ERROR_MESSAGES)


class IsAdminTests(TestCase):
    """IsAdmin 权限测试"""

    def setUp(self):
        self.permission = IsAdmin()
        self.factory = RequestFactory()

    def test_admin_user_has_permission(self):
        """测试管理员有权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_superuser = True

        self.assertTrue(self.permission.has_permission(request, None))

    def test_normal_user_no_permission(self):
        """测试普通用户无权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_superuser = False

        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_user_no_permission(self):
        """测试未认证用户无权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.user.is_superuser = False

        self.assertFalse(self.permission.has_permission(request, None))

    def test_no_user_no_permission(self):
        """测试无用户对象无权限"""
        request = self.factory.get('/')
        request.user = None

        self.assertFalse(self.permission.has_permission(request, None))


class IsLoginTests(TestCase):
    """IsLogin 权限测试"""

    def setUp(self):
        self.permission = IsLogin()
        self.factory = RequestFactory()

    def test_get_request_allowed_for_anonymous(self):
        """测试GET请求允许匿名访问"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertTrue(self.permission.has_permission(request, None))

    def test_head_request_allowed_for_anonymous(self):
        """测试HEAD请求允许匿名访问"""
        request = self.factory.head('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertTrue(self.permission.has_permission(request, None))

    def test_options_request_allowed_for_anonymous(self):
        """测试OPTIONS请求允许匿名访问"""
        request = self.factory.options('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertTrue(self.permission.has_permission(request, None))

    def test_post_request_requires_login(self):
        """测试POST请求需要登录"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertFalse(self.permission.has_permission(request, None))

    def test_post_request_allowed_for_authenticated(self):
        """测试已登录用户POST请求允许"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = True

        self.assertTrue(self.permission.has_permission(request, None))

    def test_delete_request_requires_login(self):
        """测试DELETE请求需要登录"""
        request = self.factory.delete('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertFalse(self.permission.has_permission(request, None))


class IsOwnerOrReadOnlyTests(TestCase):
    """IsOwnerOrReadOnly 权限测试"""

    def setUp(self):
        self.permission = IsOwnerOrReadOnly()
        self.factory = RequestFactory()

    def test_get_request_allowed_for_all(self):
        """测试GET请求所有人可访问"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_admin_can_modify_any_object(self):
        """测试管理员可以修改任何对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()
        obj.user = Mock()  # Different user

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_owner_can_modify(self):
        """测试拥有者可以修改"""
        request = self.factory.post('/')
        user = Mock()
        request.user = user
        request.user.is_superuser = False
        obj = Mock()
        obj.user = user  # Same user

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_owner_cannot_modify(self):
        """测试非拥有者不能修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False
        obj = Mock()
        obj.user = Mock()  # Different user

        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class IsModuleAdminTests(TestCase):
    """IsModuleAdmin 权限测试"""

    def setUp(self):
        self.permission = IsModuleAdmin()
        self.factory = RequestFactory()

    def test_get_request_allowed_for_all(self):
        """测试GET请求所有人可访问"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_superuser_can_modify(self):
        """测试超级管理员可以修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_module_admin_can_modify(self):
        """测试板块管理员可以修改"""
        request = self.factory.post('/')
        user = Mock()
        request.user = user
        request.user.is_superuser = False

        obj = Mock()
        obj.module = Mock()
        obj.module.admin = Mock()
        obj.module.admin.all = Mock(return_value=[user])

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_module_admin_cannot_modify(self):
        """测试非板块管理员不能修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock()
        obj.module = Mock()
        obj.module.admin = Mock()
        obj.module.admin.all = Mock(return_value=[])

        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_object_without_module_no_permission(self):
        """测试无板块对象无权限"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock(spec=[])  # Object without module attribute

        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class CustomExceptionHandlerTests(TestCase):
    """custom_exception_handler 测试"""

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_401_unauthorized(self, mock_logger, mock_exception_handler):
        """测试401未授权异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_401_UNAUTHORIZED
        mock_exception_handler.return_value = mock_response

        exc = AuthenticationFailed()
        context = {'view': 'TestView'}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '认证失败，请先登录')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_403_forbidden(self, mock_logger, mock_exception_handler):
        """测试403权限不足异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        mock_exception_handler.return_value = mock_response

        exc = PermissionDenied()
        context = {'view': 'TestView'}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '权限不足')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_404_not_found(self, mock_logger, mock_exception_handler):
        """测试404不存在异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_exception_handler.return_value = mock_response

        exc = NotFound()
        context = {'view': 'TestView'}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '资源不存在')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_400_bad_request(self, mock_logger, mock_exception_handler):
        """测试400参数错误异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'field': ['error message']}
        mock_exception_handler.return_value = mock_response

        exc = ValidationError({'field': ['error message']})
        context = {'view': 'TestView'}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '请求参数错误')

    @patch('common.exception_handler.exception_handler')
    def test_no_response_returns_none(self, mock_exception_handler):
        """测试无响应时返回None"""
        mock_exception_handler.return_value = None

        exc = Exception('test')
        context = {'view': 'TestView'}

        response = custom_exception_handler(exc, context)

        self.assertIsNone(response)
