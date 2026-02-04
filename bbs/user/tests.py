from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status

from user.views import UserEmail, UserList, UserDetail, UserPublicProfile
from user.models import User
from common.response import ErrorCode

UserModel = get_user_model()


class UserEmailViewTestCase(TestCase):
    """测试邮箱验证码发送视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserEmail()

    def test_invalid_email_format(self):
        """测试无效邮箱格式"""
        request = self.factory.post('/', {'email': 'invalid_email'})
        request.data = {'email': 'invalid_email'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '邮箱格式不正确')

    @patch.object(UserModel.objects, 'filter')
    def test_email_already_exists(self, mock_filter):
        """测试邮箱已存在"""
        mock_filter.return_value.exists.return_value = True

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)
        self.assertEqual(response.data['message'], '该邮箱已被注册')

    @patch('user.views.get_from_redis')
    @patch.object(UserModel.objects, 'filter')
    def test_email_too_frequent(self, mock_filter, mock_get_redis):
        """测试请求过于频繁"""
        mock_filter.return_value.exists.return_value = False
        mock_get_redis.return_value = '1'  # 冷却时间内有值

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.TOO_FREQUENT)
        self.assertEqual(response.data['message'], '请求过于频繁，请稍后再试')

    @patch('user.views.set_to_redis')
    @patch('user.views.send_mail')
    @patch('user.views.get_from_redis')
    @patch.object(UserModel.objects, 'filter')
    def test_email_send_failed(self, mock_filter, mock_get_redis, mock_send_mail, mock_set_redis):
        """测试邮件发送失败"""
        mock_filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None
        mock_send_mail.side_effect = Exception('Send failed')

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_SEND_FAILED)
        self.assertEqual(response.data['message'], '邮件发送失败')

    @patch('user.views.set_to_redis')
    @patch('user.views.send_mail')
    @patch('user.views.get_from_redis')
    @patch.object(UserModel.objects, 'filter')
    def test_email_send_success(self, mock_filter, mock_get_redis, mock_send_mail, mock_set_redis):
        """测试邮件发送成功"""
        mock_filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None
        mock_send_mail.return_value = None

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['message'], '验证码发送成功')
        # 验证redis被调用了两次（存储验证码和冷却时间）
        self.assertEqual(mock_set_redis.call_count, 2)


class UserListViewTestCase(TestCase):
    """测试用户列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserList()

    def test_register_missing_params(self):
        """测试注册缺少参数"""
        request = self.factory.post('/', {'username': '', 'email': '', 'code': ''})
        request.data = {'username': '', 'email': '', 'code': ''}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '参数不完整')

    def test_register_username_too_short(self):
        """测试用户名太短"""
        request = self.factory.post('/')
        request.data = {'username': 'a', 'email': 'test@example.com', 'code': 'ABC123'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '用户名长度应在2-20个字符之间')

    def test_register_username_too_long(self):
        """测试用户名太长"""
        request = self.factory.post('/')
        request.data = {'username': 'a' * 21, 'email': 'test@example.com', 'code': 'ABC123'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '用户名长度应在2-20个字符之间')

    @patch.object(UserModel.objects, 'filter')
    def test_register_username_exists(self, mock_filter):
        """测试用户名已存在"""
        mock_filter.return_value.exists.return_value = True

        request = self.factory.post('/')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': 'ABC123'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.USERNAME_EXISTS)
        self.assertEqual(response.data['message'], '用户名已被使用')

    @patch.object(UserModel.objects, 'filter')
    def test_register_email_exists(self, mock_filter):
        """测试邮箱已存在"""
        # 第一次调用返回用户名不存在，第二次调用返回邮箱已存在
        mock_filter.return_value.exists.side_effect = [False, True]

        request = self.factory.post('/')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': 'ABC123'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)
        self.assertEqual(response.data['message'], '邮箱已被注册')

    @patch('user.views.get_from_redis')
    @patch.object(UserModel.objects, 'filter')
    def test_register_code_error(self, mock_filter, mock_get_redis):
        """测试验证码错误"""
        mock_filter.return_value.exists.return_value = False
        mock_get_redis.return_value = 'WRONG_CODE'

        request = self.factory.post('/')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': 'ABC123'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)
        self.assertEqual(response.data['message'], '验证码错误或已过期')

    @patch('user.views.get_from_redis')
    @patch.object(UserModel.objects, 'filter')
    def test_register_code_expired(self, mock_filter, mock_get_redis):
        """测试验证码过期"""
        mock_filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None

        request = self.factory.post('/')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': 'ABC123'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)
        self.assertEqual(response.data['message'], '验证码错误或已过期')


class UserDetailViewTestCase(TestCase):
    """测试用户详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserDetail()

    def test_get_object_returns_current_user(self):
        """测试get_object返回当前用户"""
        mock_user = Mock()
        request = self.factory.get('/')
        request.user = mock_user

        self.view.request = request

        result = self.view.get_object()

        self.assertEqual(result, mock_user)

    @patch.object(UserDetail, 'get_serializer')
    def test_get_returns_api_response(self, mock_get_serializer):
        """测试GET请求返回api_response"""
        mock_user = Mock()
        mock_serializer = Mock()
        mock_serializer.data = {'id': 1, 'username': 'test'}
        mock_get_serializer.return_value = mock_serializer

        request = self.factory.get('/')
        request.user = mock_user

        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], 0)
        self.assertEqual(response.data['data'], {'id': 1, 'username': 'test'})


class UserPublicProfileViewTestCase(TestCase):
    """测试用户公开信息视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserPublicProfile()

    @patch.object(UserModel.objects, 'get')
    def test_get_object_not_found(self, mock_get):
        """测试用户不存在"""
        mock_get.side_effect = UserModel.DoesNotExist

        self.view.kwargs = {'user_id': 999}

        result = self.view.get_object()

        self.assertIsNone(result)

    @patch.object(UserModel.objects, 'get')
    def test_get_object_success(self, mock_get):
        """测试成功获取用户"""
        mock_user = Mock()
        mock_get.return_value = mock_user

        self.view.kwargs = {'user_id': 1}

        result = self.view.get_object()

        self.assertEqual(result, mock_user)
        mock_get.assert_called_with(id=1)

    @patch.object(UserPublicProfile, 'get_object')
    def test_get_user_not_found(self, mock_get_object):
        """测试GET请求用户不存在"""
        mock_get_object.return_value = None

        request = self.factory.get('/')
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '用户不存在')

    @patch.object(UserPublicProfile, 'get_object')
    def test_get_user_public_profile(self, mock_get_object):
        """测试GET请求返回公开信息"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = None
        mock_user.bio = 'Test bio'
        mock_user.date_joined = '2024-01-01'
        mock_user.posts.count.return_value = 10
        mock_get_object.return_value = mock_user

        request = self.factory.get('/')
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], 0)
        self.assertEqual(response.data['data']['id'], 1)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['bio'], 'Test bio')
        self.assertEqual(response.data['data']['post_count'], 10)


class UserModelTestCase(TestCase):
    """测试用户模型"""

    def test_user_sex_options(self):
        """测试性别选项"""
        sex_options = User.sex_options
        self.assertEqual(len(sex_options), 3)
        self.assertEqual(sex_options[0], (0, '女'))
        self.assertEqual(sex_options[1], (1, '男'))
        self.assertEqual(sex_options[2], (2, '保密'))

    def test_user_meta_verbose_name(self):
        """测试用户verbose_name"""
        self.assertEqual(User._meta.verbose_name, '用户')
