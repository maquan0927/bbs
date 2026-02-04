from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from user.views import UserEmail, UserList, UserDetail, UserPublicProfile

User = get_user_model()


class UserEmailViewTest(TestCase):
    """测试邮箱验证码视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

    def test_invalid_email_format(self):
        """测试无效邮箱格式"""
        request = self.factory.post('/', {'email': 'invalid-email'})
        request.data = {'email': 'invalid-email'}

        view = UserEmail()
        response = view.post(request)

        self.assertEqual(response.data['code'], 1001)  # PARAM_ERROR

    def test_email_already_exists(self):
        """测试邮箱已被注册"""
        request = self.factory.post('/', {'email': 'existing@example.com'})
        request.data = {'email': 'existing@example.com'}

        view = UserEmail()
        response = view.post(request)

        self.assertEqual(response.data['code'], 2002)  # EMAIL_EXISTS

    @patch('user.views.get_from_redis')
    def test_too_frequent_request(self, mock_get_redis):
        """测试请求过于频繁"""
        mock_get_redis.return_value = '1'  # 模拟冷却时间内

        request = self.factory.post('/', {'email': 'new@example.com'})
        request.data = {'email': 'new@example.com'}

        view = UserEmail()
        response = view.post(request)

        self.assertEqual(response.data['code'], 2005)  # TOO_FREQUENT

    @patch('user.views.send_mail')
    @patch('user.views.set_to_redis')
    @patch('user.views.get_from_redis')
    def test_send_verification_code_success(self, mock_get_redis, mock_set_redis, mock_send_mail):
        """测试成功发送验证码"""
        mock_get_redis.return_value = None  # 无冷却
        mock_send_mail.return_value = 1

        request = self.factory.post('/', {'email': 'new@example.com'})
        request.data = {'email': 'new@example.com'}

        view = UserEmail()
        response = view.post(request)

        self.assertEqual(response.data['code'], 0)
        mock_send_mail.assert_called_once()
        self.assertEqual(mock_set_redis.call_count, 2)  # 验证码 + 冷却时间

    @patch('user.views.send_mail')
    @patch('user.views.get_from_redis')
    def test_send_mail_failure(self, mock_get_redis, mock_send_mail):
        """测试邮件发送失败"""
        mock_get_redis.return_value = None
        mock_send_mail.side_effect = Exception('SMTP Error')

        request = self.factory.post('/', {'email': 'new@example.com'})
        request.data = {'email': 'new@example.com'}

        view = UserEmail()
        response = view.post(request)

        self.assertEqual(response.data['code'], 2004)  # EMAIL_SEND_FAILED


class UserListViewTest(TestCase):
    """测试用户列表和注册视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

    def test_register_missing_params(self):
        """测试注册缺少参数"""
        request = self.factory.post('/', {'username': 'newuser'})
        request.data = {'username': 'newuser'}

        view = UserList()
        view.request = request
        response = view.post(request)

        self.assertEqual(response.data['code'], 1001)  # PARAM_ERROR

    def test_register_username_too_short(self):
        """测试用户名太短"""
        request = self.factory.post('/', {
            'username': 'a',
            'email': 'new@example.com',
            'code': 'ABC123'
        })
        request.data = {
            'username': 'a',
            'email': 'new@example.com',
            'code': 'ABC123'
        }

        view = UserList()
        view.request = request
        response = view.post(request)

        self.assertEqual(response.data['code'], 1001)  # PARAM_ERROR

    def test_register_username_too_long(self):
        """测试用户名太长"""
        request = self.factory.post('/', {
            'username': 'a' * 25,
            'email': 'new@example.com',
            'code': 'ABC123'
        })
        request.data = {
            'username': 'a' * 25,
            'email': 'new@example.com',
            'code': 'ABC123'
        }

        view = UserList()
        view.request = request
        response = view.post(request)

        self.assertEqual(response.data['code'], 1001)  # PARAM_ERROR

    def test_register_username_exists(self):
        """测试用户名已存在"""
        request = self.factory.post('/', {
            'username': 'existinguser',
            'email': 'new@example.com',
            'code': 'ABC123'
        })
        request.data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'code': 'ABC123'
        }

        view = UserList()
        view.request = request
        response = view.post(request)

        self.assertEqual(response.data['code'], 2001)  # USERNAME_EXISTS

    def test_register_email_exists(self):
        """测试邮箱已存在"""
        request = self.factory.post('/', {
            'username': 'newuser',
            'email': 'existing@example.com',
            'code': 'ABC123'
        })
        request.data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'code': 'ABC123'
        }

        view = UserList()
        view.request = request
        response = view.post(request)

        self.assertEqual(response.data['code'], 2002)  # EMAIL_EXISTS

    @patch('user.views.get_from_redis')
    def test_register_wrong_code(self, mock_get_redis):
        """测试验证码错误"""
        mock_get_redis.return_value = 'CORRECT'

        request = self.factory.post('/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'code': 'WRONG'
        })
        request.data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'code': 'WRONG'
        }

        view = UserList()
        view.request = request
        response = view.post(request)

        self.assertEqual(response.data['code'], 2003)  # CODE_ERROR

    @patch('user.views.get_from_redis')
    def test_register_expired_code(self, mock_get_redis):
        """测试验证码过期"""
        mock_get_redis.return_value = None  # 验证码已过期

        request = self.factory.post('/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'code': 'ABC123'
        })
        request.data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'code': 'ABC123'
        }

        view = UserList()
        view.request = request
        response = view.post(request)

        self.assertEqual(response.data['code'], 2003)  # CODE_ERROR


class UserDetailViewTest(TestCase):
    """测试用户详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_get_current_user(self):
        """测试获取当前用户信息"""
        request = self.factory.get('/api/user/detail/')
        request.user = self.user

        view = UserDetail()
        view.request = request
        view.format_kwarg = None

        response = view.get(request)

        self.assertEqual(response.data['code'], 0)
        self.assertEqual(response.data['data']['username'], 'testuser')

    def test_get_object_returns_current_user(self):
        """测试get_object返回当前用户"""
        request = self.factory.get('/')
        request.user = self.user

        view = UserDetail()
        view.request = request

        obj = view.get_object()
        self.assertEqual(obj, self.user)


class UserPublicProfileViewTest(TestCase):
    """测试用户公开信息视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            bio='这是我的简介'
        )

    def test_get_public_profile_success(self):
        """测试成功获取用户公开信息"""
        request = self.factory.get(f'/api/user/{self.user.id}/profile/')
        request.user = Mock()

        view = UserPublicProfile()
        view.kwargs = {'user_id': self.user.id}
        view.request = request

        response = view.get(request)

        self.assertEqual(response.data['code'], 0)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['bio'], '这是我的简介')
        # 不应该包含敏感信息
        self.assertNotIn('email', response.data['data'])

    def test_get_nonexistent_user(self):
        """测试获取不存在用户的信息"""
        request = self.factory.get('/api/user/99999/profile/')
        request.user = Mock()

        view = UserPublicProfile()
        view.kwargs = {'user_id': 99999}
        view.request = request

        response = view.get(request)

        self.assertEqual(response.data['code'], 1002)  # NOT_FOUND

    def test_get_object_returns_user(self):
        """测试get_object返回正确用户"""
        view = UserPublicProfile()
        view.kwargs = {'user_id': self.user.id}

        obj = view.get_object()
        self.assertEqual(obj, self.user)

    def test_get_object_returns_none_for_invalid_id(self):
        """测试get_object对无效ID返回None"""
        view = UserPublicProfile()
        view.kwargs = {'user_id': 99999}

        obj = view.get_object()
        self.assertIsNone(obj)


class UserModelTest(TestCase):
    """测试用户模型"""

    def test_user_str_method(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser')

    def test_user_default_sex(self):
        """测试用户默认性别为保密"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.sex, 2)  # 保密

    def test_user_optional_fields(self):
        """测试用户可选字段"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            bio='测试简介',
            phone='13800138000'
        )

        self.assertEqual(user.bio, '测试简介')
        self.assertEqual(user.phone, '13800138000')
