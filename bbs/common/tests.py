from django.test import TestCase, RequestFactory
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model

from common.response import api_response, ErrorCode, ERROR_MESSAGES
from common.permissions import IsAdmin, IsLogin, IsOwnerOrReadOnly, IsModuleAdmin
from common.exception_handler import custom_exception_handler

User = get_user_model()


class ErrorCodeTests(TestCase):
    """错误码测试"""

    def test_error_code_values(self):
        """测试错误码值是否正确定义"""
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
        self.assertEqual(ErrorCode.SELF_ACTION_NOT_ALLOWED, 4001)

    def test_error_messages_mapping(self):
        """测试错误消息映射是否完整"""
        self.assertEqual(ERROR_MESSAGES[ErrorCode.SUCCESS], '成功')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.PARAM_ERROR], '参数错误')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.NOT_FOUND], '资源不存在')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.PERMISSION_DENIED], '权限不足')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.ALREADY_LIKED], '已经点过赞了')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.NOT_LIKED], '还没有点赞')


class ApiResponseTests(TestCase):
    """api_response 函数测试"""

    def test_success_response_default(self):
        """测试默认成功响应"""
        response = api_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['message'], '成功')
        self.assertIsNone(response.data['data'])

    def test_success_response_with_data(self):
        """测试带数据的成功响应"""
        test_data = {'key': 'value', 'count': 10}
        response = api_response(data=test_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data'], test_data)

    def test_error_response_with_code(self):
        """测试错误响应"""
        response = api_response(code=ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '资源不存在')

    def test_error_response_with_custom_message(self):
        """测试自定义消息的响应"""
        custom_message = '自定义错误消息'
        response = api_response(code=ErrorCode.PARAM_ERROR, message=custom_message)
        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], custom_message)

    def test_response_with_http_status(self):
        """测试自定义 HTTP 状态码"""
        response = api_response(
            code=ErrorCode.NOT_FOUND,
            http_status=status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    def test_unknown_error_code(self):
        """测试未知错误码"""
        unknown_code = 9999
        response = api_response(code=unknown_code)
        self.assertEqual(response.data['code'], unknown_code)
        self.assertEqual(response.data['message'], '未知错误')


class IsAdminPermissionTests(TestCase):
    """IsAdmin 权限测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAdmin()

    def test_admin_user_has_permission(self):
        """测试管理员用户有权限"""
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
        request.user = Mock()
        request.user.is_authenticated = False
        request.user.is_superuser = False

        self.assertFalse(self.permission.has_permission(request, None))

    def test_none_user_no_permission(self):
        """测试空用户无权限"""
        request = self.factory.get('/')
        request.user = None

        self.assertFalse(self.permission.has_permission(request, None))


class IsLoginPermissionTests(TestCase):
    """IsLogin 权限测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsLogin()

    def test_get_request_allows_anonymous(self):
        """测试 GET 请求允许匿名访问"""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertTrue(self.permission.has_permission(request, None))

    def test_head_request_allows_anonymous(self):
        """测试 HEAD 请求允许匿名访问"""
        request = self.factory.head('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertTrue(self.permission.has_permission(request, None))

    def test_options_request_allows_anonymous(self):
        """测试 OPTIONS 请求允许匿名访问"""
        request = self.factory.options('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertTrue(self.permission.has_permission(request, None))

    def test_post_request_requires_login(self):
        """测试 POST 请求需要登录"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertFalse(self.permission.has_permission(request, None))

    def test_post_request_logged_in_user(self):
        """测试 POST 请求已登录用户有权限"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_authenticated = True

        self.assertTrue(self.permission.has_permission(request, None))

    def test_delete_request_requires_login(self):
        """测试 DELETE 请求需要登录"""
        request = self.factory.delete('/')
        request.user = Mock()
        request.user.is_authenticated = False

        self.assertFalse(self.permission.has_permission(request, None))


class IsOwnerOrReadOnlyPermissionTests(TestCase):
    """IsOwnerOrReadOnly 权限测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsOwnerOrReadOnly()

    def test_get_request_allows_all(self):
        """测试 GET 请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_head_request_allows_all(self):
        """测试 HEAD 请求允许所有人"""
        request = self.factory.head('/')
        request.user = Mock()
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_admin_can_modify_any_object(self):
        """测试管理员可以修改任何对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()
        obj.user = Mock()  # 不同的用户

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_owner_can_modify_own_object(self):
        """测试拥有者可以修改自己的对象"""
        request = self.factory.post('/')
        user = Mock()
        request.user = user
        request.user.is_superuser = False
        obj = Mock()
        obj.user = user  # 同一用户

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_owner_cannot_modify_object(self):
        """测试非拥有者不能修改对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False
        obj = Mock()
        obj.user = Mock()  # 不同的用户

        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class IsModuleAdminPermissionTests(TestCase):
    """IsModuleAdmin 权限测试"""

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

        # 创建带 module 的对象
        obj = Mock()
        obj.module = Mock()
        obj.module.admin.all.return_value = [user]  # 用户在管理员列表中

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_module_admin_cannot_modify(self):
        """测试非板块管理员不能修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock()
        obj.module = Mock()
        obj.module.admin.all.return_value = []  # 管理员列表为空

        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_object_without_module(self):
        """测试没有 module 属性的对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = False

        obj = Mock(spec=[])  # 没有 module 属性

        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class CustomExceptionHandlerTests(TestCase):
    """自定义异常处理器测试"""

    def setUp(self):
        self.context = {'view': Mock()}

    @patch('common.exception_handler.exception_handler')
    def test_401_unauthorized(self, mock_handler):
        """测试 401 未授权异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_401_UNAUTHORIZED
        mock_handler.return_value = mock_response

        exc = Exception('Unauthorized')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '认证失败，请先登录')

    @patch('common.exception_handler.exception_handler')
    def test_403_forbidden(self, mock_handler):
        """测试 403 禁止访问异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        mock_handler.return_value = mock_response

        exc = Exception('Forbidden')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(response.data['message'], '权限不足')

    @patch('common.exception_handler.exception_handler')
    def test_404_not_found(self, mock_handler):
        """测试 404 资源不存在异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_handler.return_value = mock_response

        exc = Exception('Not Found')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '资源不存在')

    @patch('common.exception_handler.exception_handler')
    def test_400_bad_request(self, mock_handler):
        """测试 400 请求参数错误异常处理"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'field': 'error message'}
        mock_handler.return_value = mock_response

        exc = Exception('Bad Request')
        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '请求参数错误')
        self.assertEqual(response.data['data'], {'field': 'error message'})

    @patch('common.exception_handler.exception_handler')
    def test_none_response_passthrough(self, mock_handler):
        """测试无法处理的异常直接返回"""
        mock_handler.return_value = None

        exc = Exception('Unknown')
        response = custom_exception_handler(exc, self.context)

        self.assertIsNone(response)

    @patch('common.exception_handler.exception_handler')
    def test_other_status_code_passthrough(self, mock_handler):
        """测试其他状态码直接返回原响应"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_handler.return_value = mock_response

        exc = Exception('Server Error')
        response = custom_exception_handler(exc, self.context)

        # 应该返回原始响应（因为没有特殊处理 500 错误）
        self.assertEqual(response, mock_response)
