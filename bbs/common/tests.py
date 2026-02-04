from django.test import TestCase, RequestFactory
from unittest.mock import Mock, MagicMock, patch
from rest_framework import status
from rest_framework.response import Response

from common.response import api_response, ErrorCode, ERROR_MESSAGES
from common.permissions import IsAdmin, IsLogin, IsOwnerOrReadOnly, IsModuleAdmin
from common.exception_handler import custom_exception_handler


class ErrorCodeTestCase(TestCase):
    """测试错误码定义"""

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

    def test_error_messages_mapping(self):
        """测试错误信息映射"""
        self.assertEqual(ERROR_MESSAGES[ErrorCode.SUCCESS], '成功')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.PARAM_ERROR], '参数错误')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.NOT_FOUND], '资源不存在')
        self.assertEqual(ERROR_MESSAGES[ErrorCode.PERMISSION_DENIED], '权限不足')


class ApiResponseTestCase(TestCase):
    """测试统一响应格式函数"""

    def test_api_response_success_default(self):
        """测试默认成功响应"""
        response = api_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['message'], '成功')
        self.assertIsNone(response.data['data'])

    def test_api_response_with_data(self):
        """测试带数据的响应"""
        test_data = {'key': 'value', 'count': 10}
        response = api_response(data=test_data)
        self.assertEqual(response.data['data'], test_data)

    def test_api_response_with_custom_message(self):
        """测试自定义消息"""
        custom_message = '操作成功完成'
        response = api_response(message=custom_message)
        self.assertEqual(response.data['message'], custom_message)

    def test_api_response_with_error_code(self):
        """测试错误码响应"""
        response = api_response(code=ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '资源不存在')

    def test_api_response_with_custom_http_status(self):
        """测试自定义HTTP状态码"""
        response = api_response(
            code=ErrorCode.NOT_FOUND,
            http_status=status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_response_unknown_error_code(self):
        """测试未知错误码"""
        response = api_response(code=9999)
        self.assertEqual(response.data['message'], '未知错误')


class IsAdminPermissionTestCase(TestCase):
    """测试管理员权限类"""

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

    def test_non_admin_user_no_permission(self):
        """测试非管理员用户无权限"""
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
        request.user.is_superuser = True

        self.assertFalse(self.permission.has_permission(request, None))


class IsLoginPermissionTestCase(TestCase):
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

    def test_post_request_allowed_for_authenticated_user(self):
        """测试已登录用户可以POST"""
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


class IsOwnerOrReadOnlyPermissionTestCase(TestCase):
    """测试拥有者权限类"""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsOwnerOrReadOnly()

    def test_get_request_allowed_for_all(self):
        """测试GET请求允许所有人"""
        request = self.factory.get('/')
        request.user = Mock()
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_head_request_allowed_for_all(self):
        """测试HEAD请求允许所有人"""
        request = self.factory.head('/')
        request.user = Mock()
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_superuser_can_modify_any_object(self):
        """测试管理员可以修改任何对象"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()
        obj.user = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_owner_can_modify_own_object(self):
        """测试拥有者可以修改自己的对象"""
        request = self.factory.post('/')
        user = Mock()
        user.is_superuser = False
        request.user = user
        obj = Mock()
        obj.user = user

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_owner_cannot_modify_object(self):
        """测试非拥有者不能修改对象"""
        request = self.factory.post('/')
        user1 = Mock()
        user1.is_superuser = False
        user2 = Mock()
        request.user = user1
        obj = Mock()
        obj.user = user2

        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class IsModuleAdminPermissionTestCase(TestCase):
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
        """测试管理员可以修改"""
        request = self.factory.post('/')
        request.user = Mock()
        request.user.is_superuser = True
        obj = Mock()

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_module_admin_can_modify(self):
        """测试板块管理员可以修改"""
        request = self.factory.post('/')
        user = Mock()
        user.is_superuser = False
        request.user = user

        obj = Mock()
        obj.module = Mock()
        obj.module.admin = Mock()
        obj.module.admin.all = Mock(return_value=[user])

        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_module_admin_cannot_modify(self):
        """测试非板块管理员不能修改"""
        request = self.factory.post('/')
        user = Mock()
        user.is_superuser = False
        request.user = user

        obj = Mock()
        obj.module = Mock()
        obj.module.admin = Mock()
        obj.module.admin.all = Mock(return_value=[])

        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_object_without_module_returns_false(self):
        """测试没有module属性的对象返回False"""
        request = self.factory.post('/')
        user = Mock()
        user.is_superuser = False
        request.user = user

        obj = Mock(spec=[])  # 没有module属性

        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class CustomExceptionHandlerTestCase(TestCase):
    """测试自定义异常处理器"""

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handler_returns_none_when_no_response(self, mock_logger, mock_handler):
        """测试无响应时返回None"""
        mock_handler.return_value = None

        result = custom_exception_handler(Exception('test'), {})

        self.assertIsNone(result)

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handler_401_unauthorized(self, mock_logger, mock_handler):
        """测试401未授权响应"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_401_UNAUTHORIZED
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception('test'), {'view': 'TestView'})

        self.assertEqual(result.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(result.data['message'], '认证失败，请先登录')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handler_403_forbidden(self, mock_logger, mock_handler):
        """测试403禁止响应"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception('test'), {'view': 'TestView'})

        self.assertEqual(result.data['code'], ErrorCode.PERMISSION_DENIED)
        self.assertEqual(result.data['message'], '权限不足')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handler_404_not_found(self, mock_logger, mock_handler):
        """测试404未找到响应"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_404_NOT_FOUND
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception('test'), {'view': 'TestView'})

        self.assertEqual(result.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(result.data['message'], '资源不存在')

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handler_400_bad_request(self, mock_logger, mock_handler):
        """测试400错误请求响应"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'field': 'error message'}
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception('test'), {'view': 'TestView'})

        self.assertEqual(result.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(result.data['message'], '请求参数错误')
        self.assertEqual(result.data['data'], {'field': 'error message'})

    @patch('common.exception_handler.exception_handler')
    @patch('common.exception_handler.logger')
    def test_handler_other_status_returns_original(self, mock_logger, mock_handler):
        """测试其他状态码返回原响应"""
        mock_response = Mock()
        mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_handler.return_value = mock_response

        result = custom_exception_handler(Exception('test'), {'view': 'TestView'})

        self.assertEqual(result, mock_response)
