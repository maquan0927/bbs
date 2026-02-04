from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, MagicMock, patch
from common.permissions import IsAdmin, IsLogin, IsOwnerOrReadOnly, IsModuleAdmin
from common.response import api_response, ErrorCode, ERROR_MESSAGES
from common.exception_handler import custom_exception_handler
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound, ValidationError

User = get_user_model()


class IsAdminPermissionTest(TestCase):
    """测试管理员权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAdmin()
        self.view = Mock()

    def test_has_permission_with_superuser(self):
        """测试超级用户有权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_superuser = True

        result = self.permission.has_permission(request, self.view)
        self.assertTrue(result)

    def test_has_permission_without_superuser(self):
        """测试非超级用户无权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.is_superuser = False

        result = self.permission.has_permission(request, self.view)
        self.assertFalse(result)

    def test_has_permission_without_auth(self):
        """测试未认证用户无权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.user.is_superuser = False

        result = self.permission.has_permission(request, self.view)
        self.assertFalse(result)

    def test_has_permission_with_none_user(self):
        """测试没有用户对象时无权限"""
        request = self.factory.get('/')
        request.user = None

        result = self.permission.has_permission(request, self.view)
        self.assertFalse(result)


class IsLoginPermissionTest(TestCase):
    """测试登录权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsLogin()
        self.view = Mock()

    def test_get_request_allows_anonymous(self):
        """测试GET请求允许匿名访问"""
        request = self.factory.get('/')
        request.user = None

        result = self.permission.has_permission(request, self.view)
        self.assertTrue(result)

    def test_head_request_allows_anonymous(self):
        """测试HEAD请求允许匿名访问"""
        request = self.factory.head('/')
        request.user = None

        result = self.permission.has_permission(request, self.view)
        self.assertTrue(result)

    def test_options_request_allows_anonymous(self):
        """测试OPTIONS请求允许匿名访问"""
        request = self.factory.options('/')
        request.user = None

        result = self.permission.has_permission(request, self.view)
        self.assertTrue(result)

    def test_post_request_requires_auth(self):
        """测试POST请求需要登录"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = True

        result = self.permission.has_permission(request, self.view)
        self.assertTrue(result)

    def test_post_request_denies_anonymous(self):
        """测试POST请求拒绝未登录用户"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = False

        result = self.permission.has_permission(request, self.view)
        self.assertFalse(result)

    def test_delete_request_requires_auth(self):
        """测试DELETE请求需要登录"""
        request = self.factory.delete('/')
        request.user = Mock()
        request.user.is_authenticated = True

        result = self.permission.has_permission(request, self.view)
        self.assertTrue(result)


class IsOwnerOrReadOnlyPermissionTest(TestCase):
    """测试拥有者或只读权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsOwnerOrReadOnly()
        self.view = Mock()

    def test_get_request_allows_all(self):
        """测试GET请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()
        obj.user = Mock()

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertTrue(result)

    def test_superuser_can_modify_any_object(self):
        """测试超级用户可以修改任何对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()
        obj.user = Mock()  # 不同用户

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertTrue(result)

    def test_owner_can_modify_own_object(self):
        """测试拥有者可以修改自己的对象"""
        request = self.factory.post('/')
        user = Mock()
        request.user = user
        request.user.is_superuser = False
        obj = Mock()
        obj.user = user  # 同一用户

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertTrue(result)

    def test_non_owner_cannot_modify_others_object(self):
        """测试非拥有者不能修改他人对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False
        obj = Mock()
        obj.user = Mock()  # 不同用户

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertFalse(result)


class IsModuleAdminPermissionTest(TestCase):
    """测试板块管理员权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsModuleAdmin()
        self.view = Mock()

    def test_get_request_allows_all(self):
        """测试GET请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertTrue(result)

    def test_superuser_can_modify_any_module(self):
        """测试超级用户可以修改任何板块"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertTrue(result)

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

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertTrue(result)

    def test_non_admin_cannot_modify(self):
        """测试非管理员不能修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock()
        obj.module = Mock()
        obj.module.admin = Mock()
        obj.module.admin.all = Mock(return_value=[])

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertFalse(result)

    def test_object_without_module_returns_false(self):
        """测试没有板块的对象返回False"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock()
        obj.module = None

        result = self.permission.has_object_permission(request, self.view, obj)
        self.assertFalse(result)


class ApiResponseTest(TestCase):
    """测试统一API响应函数"""

    def test_default_success_response(self):
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
        self.assertEqual(response.data['message'], '参数错误')

    def test_response_with_custom_http_status(self):
        """测试自定义HTTP状态码"""
        response = api_response(http_status=status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_all_error_codes_have_messages(self):
        """测试所有错误码都有对应消息"""
        error_codes = [
            ErrorCode.SUCCESS,
            ErrorCode.PARAM_ERROR,
            ErrorCode.NOT_FOUND,
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.USERNAME_EXISTS,
            ErrorCode.EMAIL_EXISTS,
            ErrorCode.CODE_ERROR,
            ErrorCode.EMAIL_SEND_FAILED,
            ErrorCode.TOO_FREQUENT,
            ErrorCode.POST_NOT_FOUND,
            ErrorCode.ALREADY_LIKED,
            ErrorCode.NOT_LIKED,
            ErrorCode.ALREADY_FAVORITED,
            ErrorCode.NOT_FAVORITED,
            ErrorCode.SELF_ACTION_NOT_ALLOWED,
        ]

        for code in error_codes:
            self.assertIn(code, ERROR_MESSAGES)


class CustomExceptionHandlerTest(TestCase):
    """测试自定义异常处理器"""

    def setUp(self):
        self.context = {'view': Mock()}

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_401_unauthorized(self, mock_logger, mock_handler):
        """测试401未授权异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_401_UNAUTHORIZED
        mock_handler.return_value = mock_response

        exc = NotAuthenticated()
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '认证失败，请先登录')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_403_forbidden(self, mock_logger, mock_handler):
        """测试403禁止访问异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        mock_handler.return_value = mock_response

        exc = PermissionDenied()
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '权限不足')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_404_not_found(self, mock_logger, mock_handler):
        """测试404资源不存在异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_handler.return_value = mock_response

        exc = NotFound()
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '资源不存在')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handle_400_bad_request(self, mock_logger, mock_handler):
        """测试400参数错误异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'field': 'error'}
        mock_handler.return_value = mock_response

        exc = ValidationError()
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '请求参数错误')

    @patch('common.exception_handler.exception_handler')
    def test_return_none_for_unhandled_exception(self, mock_handler):
        """测试未处理异常返回None"""
        mock_handler.return_value = None

        exc = Exception('test')
        response = custom_exception_handler(exc, self.context)

        self.assertIsNone(response)
