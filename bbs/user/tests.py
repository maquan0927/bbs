from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock

from user.views import UserEmail, UserList, UserDetail, UserPublicProfile
from common.response import ErrorCode

User = get_user_model()


class UserEmailViewTests(TestCase):
    """UserEmail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserEmail()

    @patch('user.views.set_to_redis')
    @patch('user.views.get_from_redis')
    @patch('user.views.send_mail')
    @patch('user.views.User.objects')
    def test_send_email_success(self, mock_user_objects, mock_send_mail, mock_get_redis, mock_set_redis):
        """测试成功发送验证码"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None
        mock_send_mail.return_value = 1

        request = self.factory.post('/', data={'email': 'test@example.com'}, content_type='application/json')
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)

    @patch('user.views.User.objects')
    def test_send_email_invalid_format(self, mock_user_objects):
        """测试无效邮箱格式"""
        request = self.factory.post('/', data={'email': 'invalid-email'}, content_type='application/json')
        request.data = {'email': 'invalid-email'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_send_email_already_exists(self, mock_user_objects):
        """测试邮箱已存在"""
        mock_user_objects.filter.return_value.exists.return_value = True

        request = self.factory.post('/', data={'email': 'test@example.com'}, content_type='application/json')
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)

    @patch('user.views.get_from_redis')
    @patch('user.views.User.objects')
    def test_send_email_too_frequent(self, mock_user_objects, mock_get_redis):
        """测试请求过于频繁"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = '1'  # Cooldown exists

        request = self.factory.post('/', data={'email': 'test@example.com'}, content_type='application/json')
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.TOO_FREQUENT)


class UserListViewTests(TestCase):
    """UserList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserList()

    @patch('user.views.delete_to_redis')
    @patch('user.views.get_from_redis')
    @patch('user.views.User.objects')
    def test_register_missing_params(self, mock_user_objects, mock_get_redis, mock_delete_redis):
        """测试注册参数不完整"""
        request = self.factory.post('/', data={'username': 'test'}, content_type='application/json')
        request.data = {'username': 'test'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_register_username_too_short(self, mock_user_objects):
        """测试用户名太短"""
        request = self.factory.post('/', content_type='application/json')
        request.data = {'username': 'a', 'email': 'test@example.com', 'code': '123456'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_register_username_too_long(self, mock_user_objects):
        """测试用户名太长"""
        request = self.factory.post('/', content_type='application/json')
        request.data = {'username': 'a' * 25, 'email': 'test@example.com', 'code': '123456'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_register_username_exists(self, mock_user_objects):
        """测试用户名已存在"""
        mock_user_objects.filter.return_value.exists.side_effect = [True, False]

        request = self.factory.post('/', content_type='application/json')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': '123456'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.USERNAME_EXISTS)

    @patch('user.views.User.objects')
    def test_register_email_exists(self, mock_user_objects):
        """测试邮箱已存在"""
        mock_user_objects.filter.return_value.exists.side_effect = [False, True]

        request = self.factory.post('/', content_type='application/json')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': '123456'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)

    @patch('user.views.get_from_redis')
    @patch('user.views.User.objects')
    def test_register_wrong_code(self, mock_user_objects, mock_get_redis):
        """测试验证码错误"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = 'ABCDEF'

        request = self.factory.post('/', content_type='application/json')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': 'WRONG'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)

    @patch('user.views.get_from_redis')
    @patch('user.views.User.objects')
    def test_register_expired_code(self, mock_user_objects, mock_get_redis):
        """测试验证码过期"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None  # No code stored

        request = self.factory.post('/', content_type='application/json')
        request.data = {'username': 'testuser', 'email': 'test@example.com', 'code': '123456'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)


class UserDetailViewTests(TestCase):
    """UserDetail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserDetail()

    def test_get_object_returns_current_user(self):
        """测试返回当前用户"""
        mock_user = Mock()
        mock_user.id = 1

        request = self.factory.get('/')
        request.user = mock_user

        self.view.request = request
        result = self.view.get_object()

        self.assertEqual(result, mock_user)

    @patch.object(UserDetail, 'get_serializer')
    @patch.object(UserDetail, 'get_object')
    def test_get_user_detail(self, mock_get_object, mock_get_serializer):
        """测试获取用户详情"""
        mock_user = Mock()
        mock_get_object.return_value = mock_user

        mock_serializer = Mock()
        mock_serializer.data = {'id': 1, 'username': 'testuser'}
        mock_get_serializer.return_value = mock_serializer

        request = self.factory.get('/')
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)


class UserPublicProfileViewTests(TestCase):
    """UserPublicProfile 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserPublicProfile()

    @patch('user.views.User.objects')
    def test_get_public_profile_success(self, mock_user_objects):
        """测试获取用户公开信息成功"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = None
        mock_user.bio = 'Test bio'
        mock_user.date_joined = '2024-01-01'
        mock_user.posts = Mock()
        mock_user.posts.count.return_value = 5
        mock_user_objects.get.return_value = mock_user

        request = self.factory.get('/')
        self.view.request = request
        self.view.kwargs = {'user_id': 1}

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['post_count'], 5)

    @patch('user.views.User.objects')
    def test_get_public_profile_not_found(self, mock_user_objects):
        """测试获取不存在的用户"""
        mock_user_objects.get.side_effect = User.DoesNotExist

        request = self.factory.get('/')
        self.view.request = request
        self.view.kwargs = {'user_id': 999}

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    @patch('user.views.User.objects')
    def test_get_public_profile_with_avatar(self, mock_user_objects):
        """测试获取带头像的用户公开信息"""
        mock_avatar = Mock()
        mock_avatar.url = '/media/avatar.jpg'

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = mock_avatar
        mock_user.bio = 'Test bio'
        mock_user.date_joined = '2024-01-01'
        mock_user.posts = Mock()
        mock_user.posts.count.return_value = 0
        mock_user_objects.get.return_value = mock_user

        request = self.factory.get('/')
        self.view.request = request
        self.view.kwargs = {'user_id': 1}

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['avatar'], '/media/avatar.jpg')
