from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock

from user.views import UserEmail, UserList, UserDetail, UserPublicProfile
from user.serializers import UserSerializer
from common.response import ErrorCode

User = get_user_model()


class UserEmailViewTests(TestCase):
    """测试邮箱验证码发送视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserEmail()

    def test_invalid_email_format(self):
        """测试无效邮箱格式"""
        request = self.factory.post('/', {'email': 'invalid-email'})
        request.data = {'email': 'invalid-email'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '邮箱格式不正确')

    @patch.object(User.objects, 'filter')
    def test_email_already_registered(self, mock_filter):
        """测试邮箱已被注册"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_EXISTS)

    @patch('user.views.get_from_redis')
    @patch.object(User.objects, 'filter')
    def test_request_too_frequent(self, mock_filter, mock_redis):
        """测试请求过于频繁"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        mock_redis.return_value = '1'  # 存在冷却标记

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.TOO_FREQUENT)

    @patch('user.views.set_to_redis')
    @patch('user.views.send_mail')
    @patch('user.views.get_from_redis')
    @patch.object(User.objects, 'filter')
    def test_send_email_success(self, mock_filter, mock_get_redis, mock_send_mail, mock_set_redis):
        """测试发送邮件成功"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        mock_get_redis.return_value = None  # 无冷却标记

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        mock_send_mail.assert_called_once()
        self.assertEqual(response.data['message'], '验证码发送成功')

    @patch('user.views.send_mail')
    @patch('user.views.get_from_redis')
    @patch.object(User.objects, 'filter')
    def test_send_email_failed(self, mock_filter, mock_get_redis, mock_send_mail):
        """测试发送邮件失败"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        mock_get_redis.return_value = None
        mock_send_mail.side_effect = Exception('SMTP error')

        request = self.factory.post('/', {'email': 'test@example.com'})
        request.data = {'email': 'test@example.com'}

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.EMAIL_SEND_FAILED)


class UserListViewTests(TestCase):
    """测试用户列表和注册视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserList()

    def test_register_missing_params(self):
        """测试注册缺少参数"""
        request = self.factory.post('/', {'username': 'test'})
        request.data = {'username': 'test'}
        request.user = Mock()

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertEqual(response.data['message'], '参数不完整')

    def test_register_username_too_short(self):
        """测试用户名太短"""
        request = self.factory.post('/')
        request.data = {
            'username': 'a',
            'email': 'test@example.com',
            'code': '123456'
        }
        request.user = Mock()

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.PARAM_ERROR)
        self.assertIn('用户名长度', response.data['message'])

    @patch.object(User.objects, 'filter')
    def test_register_username_exists(self, mock_filter):
        """测试用户名已存在"""
        mock_queryset = Mock()
        mock_queryset.exists.side_effect = [True, False]  # username exists
        mock_filter.return_value = mock_queryset

        request = self.factory.post('/')
        request.data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'code': '123456'
        }
        request.user = Mock()

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.USERNAME_EXISTS)

    @patch('user.views.get_from_redis')
    @patch.object(User.objects, 'filter')
    def test_register_wrong_code(self, mock_filter, mock_redis):
        """测试验证码错误"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        mock_redis.return_value = 'ABCDEF'  # 不同的验证码

        request = self.factory.post('/')
        request.data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'code': '123456'
        }
        request.user = Mock()

        response = self.view.post(request)

        self.assertEqual(response.data['code'], ErrorCode.CODE_ERROR)


class UserDetailViewTests(TestCase):
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

    @patch('user.views.UserSerializer')
    def test_get_returns_user_info(self, mock_serializer):
        """测试获取用户信息"""
        mock_user = Mock()
        mock_serializer.return_value.data = {'id': 1, 'username': 'test'}

        request = self.factory.get('/')
        request.user = mock_user

        self.view.request = request
        self.view.format_kwarg = None

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertIsNotNone(response.data['data'])


class UserPublicProfileViewTests(TestCase):
    """测试用户公开信息视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserPublicProfile()

    @patch.object(User.objects, 'get')
    def test_get_object_success(self, mock_get):
        """测试成功获取用户"""
        mock_user = Mock()
        mock_get.return_value = mock_user

        self.view.kwargs = {'user_id': 1}
        result = self.view.get_object()

        mock_get.assert_called_once_with(id=1)
        self.assertEqual(result, mock_user)

    @patch.object(User.objects, 'get')
    def test_get_object_not_found(self, mock_get):
        """测试用户不存在"""
        mock_get.side_effect = User.DoesNotExist()

        self.view.kwargs = {'user_id': 999}
        result = self.view.get_object()

        self.assertIsNone(result)

    @patch.object(UserPublicProfile, 'get_object')
    def test_get_user_not_found(self, mock_get_object):
        """测试获取不存在的用户"""
        mock_get_object.return_value = None

        request = self.factory.get('/')
        self.view.kwargs = {'user_id': 999}

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '用户不存在')

    @patch.object(UserPublicProfile, 'get_object')
    def test_get_returns_public_info(self, mock_get_object):
        """测试返回公开信息"""
        from datetime import datetime
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = None
        mock_user.bio = 'Hello world'
        mock_user.date_joined = datetime.now()
        mock_posts = Mock()
        mock_posts.count.return_value = 10
        mock_user.posts = mock_posts
        mock_get_object.return_value = mock_user

        request = self.factory.get('/')
        self.view.kwargs = {'user_id': 1}

        response = self.view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['id'], 1)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['post_count'], 10)


class UserSerializerTests(TestCase):
    """测试用户序列化器"""

    def test_get_post_count_with_posts(self):
        """测试获取用户发帖数-有帖子"""
        serializer = UserSerializer()

        mock_user = Mock()
        mock_posts = Mock()
        mock_posts.count.return_value = 5
        mock_user.posts = mock_posts

        result = serializer.get_post_count(mock_user)

        self.assertEqual(result, 5)

    def test_get_post_count_without_posts(self):
        """测试获取用户发帖数-无posts属性"""
        serializer = UserSerializer()

        mock_user = Mock(spec=[])  # 没有posts属性

        result = serializer.get_post_count(mock_user)

        self.assertEqual(result, 0)
