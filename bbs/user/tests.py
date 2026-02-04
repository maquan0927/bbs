from django.test import TestCase
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model

from user.views import UserEmail, UserList, UserDetail, UserPublicProfile
from common.response import ErrorCode

User = get_user_model()


class UserModelTests(TestCase):
    """User 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_user_str_representation(self):
        """测试用户字符串表示"""
        self.assertEqual(str(self.user), 'testuser')

    def test_user_default_sex(self):
        """测试用户默认性别为保密"""
        self.assertEqual(self.user.sex, 2)

    def test_user_optional_fields(self):
        """测试用户可选字段"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            bio='这是个人简介',
            phone='13800138000'
        )
        self.assertEqual(user.bio, '这是个人简介')
        self.assertEqual(user.phone, '13800138000')


class UserEmailViewTests(TestCase):
    """UserEmail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_invalid_email_format(self):
        """测试无效邮箱格式"""
        view = UserEmail.as_view()
        request = self.factory.post('/api/user/email/', {'email': 'invalid-email'})

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertIn('邮箱格式', response.data['message'])

    def test_email_already_registered(self):
        """测试邮箱已被注册"""
        view = UserEmail.as_view()
        request = self.factory.post('/api/user/email/', {'email': 'existing@example.com'})

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)

    @patch('user.views.get_from_redis')
    def test_email_cooldown(self, mock_get_redis):
        """测试邮件发送冷却时间"""
        mock_get_redis.return_value = '1'  # 模拟冷却中

        view = UserEmail.as_view()
        request = self.factory.post('/api/user/email/', {'email': 'new@example.com'})

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.TOO_FREQUENT)

    @patch('user.views.get_from_redis')
    @patch('user.views.set_to_redis')
    @patch('user.views.send_mail')
    def test_send_email_success(self, mock_send_mail, mock_set_redis, mock_get_redis):
        """测试成功发送验证码"""
        mock_get_redis.return_value = None  # 没有冷却
        mock_send_mail.return_value = 1  # 发送成功

        view = UserEmail.as_view()
        request = self.factory.post('/api/user/email/', {'email': 'new@example.com'})

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertTrue(mock_send_mail.called)
        self.assertTrue(mock_set_redis.called)

    @patch('user.views.get_from_redis')
    @patch('user.views.send_mail')
    def test_send_email_failed(self, mock_send_mail, mock_get_redis):
        """测试邮件发送失败"""
        mock_get_redis.return_value = None
        mock_send_mail.side_effect = Exception('SMTP Error')

        view = UserEmail.as_view()
        request = self.factory.post('/api/user/email/', {'email': 'new@example.com'})

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_SEND_FAILED)


class UserListViewTests(TestCase):
    """UserList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.normal_user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='normalpass123'
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_register_missing_params(self):
        """测试注册参数不完整"""
        view = UserList.as_view()
        request = self.factory.post('/api/user/', {
            'username': 'newuser',
            'email': 'new@example.com'
            # 缺少 code
        })

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertIn('参数不完整', response.data['message'])

    def test_register_username_too_short(self):
        """测试用户名太短"""
        view = UserList.as_view()
        request = self.factory.post('/api/user/', {
            'username': 'a',  # 只有1个字符
            'email': 'new@example.com',
            'code': 'ABC123'
        })

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertIn('用户名长度', response.data['message'])

    def test_register_username_too_long(self):
        """测试用户名太长"""
        view = UserList.as_view()
        request = self.factory.post('/api/user/', {
            'username': 'a' * 21,  # 21个字符
            'email': 'new@example.com',
            'code': 'ABC123'
        })

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertIn('用户名长度', response.data['message'])

    def test_register_username_exists(self):
        """测试用户名已存在"""
        view = UserList.as_view()
        request = self.factory.post('/api/user/', {
            'username': 'normaluser',  # 已存在
            'email': 'new@example.com',
            'code': 'ABC123'
        })

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.USERNAME_EXISTS)

    def test_register_email_exists(self):
        """测试邮箱已存在"""
        view = UserList.as_view()
        request = self.factory.post('/api/user/', {
            'username': 'newuser',
            'email': 'normal@example.com',  # 已存在
            'code': 'ABC123'
        })

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)

    @patch('user.views.get_from_redis')
    def test_register_wrong_code(self, mock_get_redis):
        """测试验证码错误"""
        mock_get_redis.return_value = 'CORRECT'

        view = UserList.as_view()
        request = self.factory.post('/api/user/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'code': 'WRONG'  # 错误的验证码
        })

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)

    @patch('user.views.get_from_redis')
    def test_register_expired_code(self, mock_get_redis):
        """测试验证码过期"""
        mock_get_redis.return_value = None  # 验证码不存在（已过期）

        view = UserList.as_view()
        request = self.factory.post('/api/user/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'code': 'ABC123'
        })

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)


class UserDetailViewTests(TestCase):
    """UserDetail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_get_current_user_info(self):
        """测试获取当前用户信息"""
        view = UserDetail.as_view()
        request = self.factory.get('/api/user/detail/')
        request.user = self.user

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['username'], 'testuser')

    def test_get_object_returns_request_user(self):
        """测试 get_object 返回当前请求用户"""
        view = UserDetail()
        request = self.factory.get('/api/user/detail/')
        request.user = self.user
        view.request = request

        obj = view.get_object()
        self.assertEqual(obj, self.user)


class UserPublicProfileViewTests(TestCase):
    """UserPublicProfile 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            bio='这是个人简介'
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_get_public_profile_success(self):
        """测试成功获取用户公开信息"""
        view = UserPublicProfile.as_view()
        request = self.factory.get(f'/api/user/{self.user.id}/profile/')

        response = view(request, user_id=self.user.id)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        data = response.data['data']
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['bio'], '这是个人简介')

    def test_get_public_profile_user_not_found(self):
        """测试获取不存在用户的公开信息"""
        view = UserPublicProfile.as_view()
        request = self.factory.get('/api/user/9999/profile/')

        response = view(request, user_id=9999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    def test_public_profile_contains_only_public_fields(self):
        """测试公开信息只包含公开字段"""
        view = UserPublicProfile.as_view()
        request = self.factory.get(f'/api/user/{self.user.id}/profile/')

        response = view(request, user_id=self.user.id)

        data = response.data['data']
        # 确保包含公开字段
        self.assertIn('id', data)
        self.assertIn('username', data)
        self.assertIn('bio', data)
        # 确保不包含敏感字段
        self.assertNotIn('email', data)
        self.assertNotIn('password', data)

    def test_get_object_returns_none_for_nonexistent(self):
        """测试 get_object 对不存在的用户返回 None"""
        view = UserPublicProfile()
        view.kwargs = {'user_id': 9999}

        obj = view.get_object()
        self.assertIsNone(obj)

    def test_get_object_returns_user(self):
        """测试 get_object 返回正确的用户"""
        view = UserPublicProfile()
        view.kwargs = {'user_id': self.user.id}

        obj = view.get_object()
        self.assertEqual(obj, self.user)
