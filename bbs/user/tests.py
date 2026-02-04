from django.test import TestCase, SimpleTestCase, RequestFactory
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status

from user.models import User
from user.views import UserEmail, UserList, UserDetail, UserPublicProfile
from common.response import ErrorCode


class UserEmailViewTest(SimpleTestCase):
    """UserEmail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserEmail()

    @patch('user.views.User.objects')
    def test_invalid_email_format(self, mock_user_objects):
        """测试无效邮箱格式"""
        request = self.factory.post('/', data={'email': 'invalid-email'})
        request.data = {'email': 'invalid-email'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_email_already_exists(self, mock_user_objects):
        """测试邮箱已被注册"""
        mock_user_objects.filter.return_value.exists.return_value = True

        request = self.factory.post('/', data={'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)

    @patch('user.views.set_to_redis')
    @patch('user.views.get_from_redis')
    @patch('user.views.User.objects')
    def test_request_too_frequent(self, mock_user_objects, mock_get_redis, mock_set_redis):
        """测试请求过于频繁"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = '1'  # 存在冷却标记

        request = self.factory.post('/', data={'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.TOO_FREQUENT)

    @patch('user.views.set_to_redis')
    @patch('user.views.get_from_redis')
    @patch('user.views.send_mail')
    @patch('user.views.User.objects')
    def test_email_send_success(self, mock_user_objects, mock_send_mail, mock_get_redis, mock_set_redis):
        """测试成功发送验证码"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None  # 无冷却标记

        request = self.factory.post('/', data={'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        mock_send_mail.assert_called_once()

    @patch('user.views.set_to_redis')
    @patch('user.views.get_from_redis')
    @patch('user.views.send_mail')
    @patch('user.views.User.objects')
    def test_email_send_failure(self, mock_user_objects, mock_send_mail, mock_get_redis, mock_set_redis):
        """测试发送邮件失败"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None
        mock_send_mail.side_effect = Exception('SMTP error')

        request = self.factory.post('/', data={'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_SEND_FAILED)


class UserListViewTest(SimpleTestCase):
    """UserList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserList()

    @patch('user.views.User.objects')
    def test_register_missing_params(self, mock_user_objects):
        """测试注册参数不完整"""
        request = self.factory.post('/')
        request.data = {'username': 'testuser'}  # 缺少 email 和 code

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_register_username_too_short(self, mock_user_objects):
        """测试用户名过短"""
        request = self.factory.post('/')
        request.data = {
            'username': 'a',  # 小于2个字符
            'email': 'test@example.com',
            'code': 'ABC123'
        }

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_register_username_too_long(self, mock_user_objects):
        """测试用户名过长"""
        request = self.factory.post('/')
        request.data = {
            'username': 'a' * 21,  # 大于20个字符
            'email': 'test@example.com',
            'code': 'ABC123'
        }

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)

    @patch('user.views.User.objects')
    def test_register_username_exists(self, mock_user_objects):
        """测试用户名已存在"""
        mock_user_objects.filter.return_value.exists.side_effect = [True, False]

        request = self.factory.post('/')
        request.data = {
            'username': 'existinguser',
            'email': 'test@example.com',
            'code': 'ABC123'
        }

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.USERNAME_EXISTS)

    @patch('user.views.User.objects')
    def test_register_email_exists(self, mock_user_objects):
        """测试邮箱已被注册"""
        mock_user_objects.filter.return_value.exists.side_effect = [False, True]

        request = self.factory.post('/')
        request.data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'code': 'ABC123'
        }

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)

    @patch('user.views.get_from_redis')
    @patch('user.views.User.objects')
    def test_register_invalid_code(self, mock_user_objects, mock_get_redis):
        """测试验证码错误"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = 'DIFFERENT'

        request = self.factory.post('/')
        request.data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'code': 'WRONG123'
        }

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)

    @patch('user.views.get_from_redis')
    @patch('user.views.User.objects')
    def test_register_code_expired(self, mock_user_objects, mock_get_redis):
        """测试验证码已过期"""
        mock_user_objects.filter.return_value.exists.return_value = False
        mock_get_redis.return_value = None  # 验证码不存在

        request = self.factory.post('/')
        request.data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'code': 'ABC123'
        }

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)


class UserDetailViewTest(SimpleTestCase):
    """UserDetail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserDetail()

    def test_get_object_returns_request_user(self):
        """测试 get_object 返回当前用户"""
        request = self.factory.get('/')
        mock_user = Mock(id=1, username='testuser')
        request.user = mock_user

        self.view.request = request
        result = self.view.get_object()

        self.assertEqual(result, mock_user)

    @patch.object(UserDetail, 'get_serializer')
    def test_get_user_detail(self, mock_get_serializer):
        """测试获取当前用户信息"""
        request = self.factory.get('/')
        mock_user = Mock(id=1, username='testuser')
        request.user = mock_user

        mock_serializer = Mock()
        mock_serializer.data = {'id': 1, 'username': 'testuser'}
        mock_get_serializer.return_value = mock_serializer

        self.view.request = request
        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['username'], 'testuser')


class UserPublicProfileViewTest(SimpleTestCase):
    """UserPublicProfile 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserPublicProfile()

    @patch('user.views.User.objects')
    def test_get_object_success(self, mock_user_objects):
        """测试成功获取用户对象"""
        mock_user = Mock(id=1, username='testuser')
        mock_user_objects.get.return_value = mock_user

        self.view.kwargs = {'user_id': 1}
        result = self.view.get_object()

        self.assertEqual(result, mock_user)

    @patch('user.views.User.objects')
    def test_get_object_not_found(self, mock_user_objects):
        """测试用户不存在返回 None"""
        mock_user_objects.get.side_effect = User.DoesNotExist

        self.view.kwargs = {'user_id': 999}
        result = self.view.get_object()

        self.assertIsNone(result)

    @patch('user.views.User.objects')
    def test_get_user_not_found_response(self, mock_user_objects):
        """测试用户不存在时返回错误响应"""
        mock_user_objects.get.side_effect = User.DoesNotExist

        request = self.factory.get('/')
        self.view.kwargs = {'user_id': 999}
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    @patch('user.views.User.objects')
    def test_get_public_profile_success(self, mock_user_objects):
        """测试成功获取用户公开信息"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = None
        mock_user.bio = '测试简介'
        mock_user.date_joined = '2026-01-01'
        mock_user.posts.count.return_value = 10
        mock_user_objects.get.return_value = mock_user

        request = self.factory.get('/')
        self.view.kwargs = {'user_id': 1}
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['id'], 1)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['bio'], '测试简介')
        self.assertEqual(response.data['data']['post_count'], 10)

    @patch('user.views.User.objects')
    def test_get_public_profile_with_avatar(self, mock_user_objects):
        """测试获取带头像的用户公开信息"""
        mock_avatar = Mock()
        mock_avatar.url = '/media/avatars/test.jpg'

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = mock_avatar
        mock_user.bio = '测试简介'
        mock_user.date_joined = '2026-01-01'
        mock_user.posts.count.return_value = 5
        mock_user_objects.get.return_value = mock_user

        request = self.factory.get('/')
        self.view.kwargs = {'user_id': 1}
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['avatar'], '/media/avatars/test.jpg')

    @patch('user.views.User.objects')
    def test_get_public_profile_without_posts(self, mock_user_objects):
        """测试获取没有帖子属性的用户信息"""
        mock_user = Mock(spec=['id', 'username', 'avatar', 'bio', 'date_joined'])
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = None
        mock_user.bio = None
        mock_user.date_joined = '2026-01-01'
        mock_user_objects.get.return_value = mock_user

        request = self.factory.get('/')
        self.view.kwargs = {'user_id': 1}
        self.view.request = request

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['post_count'], 0)
