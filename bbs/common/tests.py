from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.response import Response
from unittest.mock import Mock, patch, MagicMock

from common.response import api_response, ErrorCode, ERROR_MESSAGES
from common.permissions import IsAdmin, IsLogin, IsOwnerOrReadOnly, IsModuleAdmin
from common.exception_handler import custom_exception_handler


class ErrorCodeTests(TestCase):
    """测试错误码定义"""

    def test_error_codes_defined(self):
        """测试所有错误码都已定义"""
        self.assertEqual(ErrorCode.SUCCESS, 0)
        self.assertEqual(ErrorCode.PARAM_ERROR, 1001)
        self.assertEqual(ErrorCode.NOT_FOUND, 1002)
        self.assertEqual(ErrorCode.PERMISSION_DENIED, 1003)
        self.assertEqual(ErrorCode.USERNAME_EXISTS, 2001)
        self.assertEqual(ErrorCode.EMAIL_EXISTS, 2002)
        self.assertEqual(ErrorCode.CODE_ERROR, 2003)
        self.assertEqual(ErrorCode.EMAIL_SEND_FAILED, 2004)
        self.assertEqual(ErrorCode.TOO_FREQUENT, 2005)
        self.assertEqual(ErrorCode.POST_NOT_FOUND, 3001)
        self.assertEqual(ErrorCode.ALREADY_LIKED, 3002)
        self.assertEqual(ErrorCode.NOT_LIKED, 3003)
        self.assertEqual(ErrorCode.ALREADY_FAVORITED, 3004)
        self.assertEqual(ErrorCode.NOT_FAVORITED, 3005)
        self.assertEqual(ErrorCode.SELF_ACTION_NOT_ALLOWED, 4001)

    def test_error_messages_defined(self):
        """测试所有错误消息都已定义"""
        self.assertIn(ErrorCode.SUCCESS, ERROR_MESSAGES)
        self.assertIn(ErrorCode.PARAM_ERROR, ERROR_MESSAGES)
        self.assertIn(ErrorCode.NOT_FOUND, ERROR_MESSAGES)
        self.assertEqual(ERROR_MESSAGES[ErrorCode.SUCCESS], '成功')


class ApiResponseTests(TestCase):
    """测试统一API响应函数"""

    def test_api_response_with_default_params(self):
        """测试默认参数"""
        response = api_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['message'], '成功')
        self.assertIsNone(response.data['data'])

    def test_api_response_with_custom_code(self):
        """测试自定义错误码"""
        response = api_response(code=ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '资源不存在')

    def test_api_response_with_custom_message(self):
        """测试自定义消息"""
        response = api_response(message='自定义消息')
        self.assertEqual(response.data['message'], '自定义消息')

    def test_api_response_with_data(self):
        """测试带数据的响应"""
        test_data = {'key': 'value', 'count': 10}
        response = api_response(data=test_data)
        self.assertEqual(response.data['data'], test_data)

    def test_api_response_with_custom_http_status(self):
        """测试自定义HTTP状态码"""
        response = api_response(http_status=status.HTTP_201_CREATED)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_response_unknown_code(self):
        """测试未知错误码使用默认消息"""
        response = api_response(code=9999)
        self.assertEqual(response.data['message'], '未知错误')


class IsAdminPermissionTests(TestCase):
    """测试管理员权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAdmin()

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

    def test_anonymous_user_no_permission(self):
        """测试匿名用户无权限"""
        request = self.factory.get('/')
        request.user = None

        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_user_no_permission(self):
        """测试未认证用户无权限"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.user.is_superuser = False

        self.assertFalse(self.permission.has_permission(request, None))


class IsLoginPermissionTests(TestCase):
    """测试登录权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsLogin()

    def test_get_request_allowed_for_anonymous(self):
        """测试GET请求允许匿名访问"""
        request = self.factory.get('/')
        request.user = None

        self.assertTrue(self.permission.has_permission(request, None))

    def test_head_request_allowed_for_anonymous(self):
        """测试HEAD请求允许匿名访问"""
        request = self.factory.head('/')
        request.user = None

        self.assertTrue(self.permission.has_permission(request, None))

    def test_options_request_allowed_for_anonymous(self):
        """测试OPTIONS请求允许匿名访问"""
        request = self.factory.options('/')
        request.user = None

        self.assertTrue(self.permission.has_permission(request, None))

    def test_post_request_requires_login(self):
        """测试POST请求需要登录"""
        request = self.factory.post('/')
        request.user = None

        self.assertFalse(self.permission.has_permission(request, None))

    def test_post_request_authenticated_user(self):
        """测试POST请求-已登录用户"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = True

        self.assertTrue(self.permission.has_permission(request, None))

    def test_delete_request_requires_login(self):
        """测试DELETE请求需要登录"""
        request = self.factory.delete('/')
        request.user = None

        self.assertFalse(self.permission.has_permission(request, None))


class IsOwnerOrReadOnlyPermissionTests(TestCase):
    """测试拥有者权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsOwnerOrReadOnly()

    def test_get_request_allowed_for_all(self):
        """测试GET请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()

        obj = Mock()
        obj.user = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_owner_can_modify(self):
        """测试拥有者可以修改"""
        request = self.factory.post('/')
        user = Mock()
        request.user = user
        request.user.is_superuser = False

        obj = Mock()
        obj.user = user

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_owner_cannot_modify(self):
        """测试非拥有者不能修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock()
        obj.user = Mock()  # 不同的用户

        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_admin_can_modify_any(self):
        """测试管理员可以修改任何对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True

        obj = Mock()
        obj.user = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))


class IsModuleAdminPermissionTests(TestCase):
    """测试板块管理员权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsModuleAdmin()

    def test_get_request_allowed_for_all(self):
        """测试GET请求允许所有人"""
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

        module = Mock()
        module.admin.all.return_value = [user]

        obj = Mock()
        obj.module = module

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_module_admin_cannot_modify(self):
        """测试非板块管理员不能修改"""
        request = self.factory.post('/')
        user = Mock()
        request.user = user
        request.user.is_superuser = False

        module = Mock()
        module.admin.all.return_value = []

        obj = Mock()
        obj.module = module

        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_obj_without_module(self):
        """测试无module属性的对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock(spec=[])  # 没有module属性

        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class CustomExceptionHandlerTests(TestCase):
    """测试自定义异常处理器"""

    @patch('common.exception_handler.exception_handler')
    def test_none_response_returns_none(self, mock_handler):
        """测试原始异常处理返回None时直接返回"""
        mock_handler.return_value = None

        result = custom_exception_handler(Exception(), {})

        self.assertIsNone(result)

    @patch('common.exception_handler.exception_handler')
    def test_401_unauthorized(self, mock_handler):
        """测试401未授权异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_401_UNAUTHORIZED
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception(), {'view': None})

        self.assertEqual(result.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(result.data['message'], '认证失败，请先登录')

    @patch('common.exception_handler.exception_handler')
    def test_403_forbidden(self, mock_handler):
        """测试403禁止访问异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception(), {'view': None})

        self.assertEqual(result.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(result.data['message'], '权限不足')

    @patch('common.exception_handler.exception_handler')
    def test_404_not_found(self, mock_handler):
        """测试404资源不存在异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception(), {'view': None})

        self.assertEqual(result.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(result.data['message'], '资源不存在')

    @patch('common.exception_handler.exception_handler')
    def test_400_bad_request(self, mock_handler):
        """测试400参数错误异常"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'field': ['error message']}
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception(), {'view': None})

        self.assertEqual(result.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(result.data['message'], '请求参数错误')
        self.assertEqual(result.data['data'], {'field': ['error message']})
