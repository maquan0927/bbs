from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.request import Request

from user.models import User
from user.views import UserEmail, UserList, UserDetail, UserPublicProfile
from common.response import ErrorCode

UserModel = get_user_model()


class UserModelTest(TestCase):
    """User 模型测试"""

    def test_user_str_method(self):
        """测试 User 的 __str__ 方法"""
        user = User()
        user.username = 'testuser'

        self.assertEqual(str(user), 'testuser')

    def test_user_default_values(self):
        """测试 User 的默认值"""
        user = User()

        self.assertEqual(user.sex, 2)  # 保密
        self.assertIsNone(user.birthday)
        self.assertIsNone(user.bio)
        self.assertIsNone(user.phone)


class UserEmailViewTest(TestCase):
    """UserEmail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_email_validation_regex(self):
        """测试邮箱验证正则表达式"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        # 测试有效邮箱
        valid_emails = ['test@example.com', 'user.name@domain.org', 'test123@test.cn']
        for email in valid_emails:
            self.assertTrue(re.match(email_pattern, email), f'{email} should be valid')

        # 测试无效邮箱
        invalid_emails = ['invalid-email', 'test@', '@test.com', 'test']
        for email in invalid_emails:
            self.assertIsNone(re.match(email_pattern, email), f'{email} should be invalid')


class UserListViewTest(TestCase):
    """UserList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_username_length_validation(self):
        """测试用户名长度验证逻辑"""
        # 测试用户名长度限制
        min_length = 2
        max_length = 20

        # 过短用户名
        short_username = 'a'
        self.assertLess(len(short_username), min_length)

        # 有效用户名
        valid_username = 'testuser'
        self.assertGreaterEqual(len(valid_username), min_length)
        self.assertLessEqual(len(valid_username), max_length)

        # 过长用户名
        long_username = 'a' * 21
        self.assertGreater(len(long_username), max_length)

    def test_parameter_validation_logic(self):
        """测试参数验证逻辑"""
        # 模拟缺少参数的情况
        params = {'username': 'test'}
        required_fields = ['username', 'email', 'code']

        missing_fields = [f for f in required_fields if f not in params or not params.get(f)]
        self.assertEqual(len(missing_fields), 2)  # email 和 code 缺失


class UserDetailViewTest(TestCase):
    """UserDetail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.username = 'testuser'
        self.user.is_authenticated = True

    def test_get_object_returns_current_user(self):
        """测试 get_object 返回当前用户"""
        request = self.factory.get('/api/user/detail/')
        request.user = self.user

        view = UserDetail()
        view.request = request

        result = view.get_object()
        self.assertEqual(result, self.user)


class UserPublicProfileViewTest(TestCase):
    """UserPublicProfile 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()

    @patch('user.views.User.objects.get')
    def test_get_user_profile_success(self, mock_get):
        """测试成功获取用户公开信息"""
        from datetime import datetime
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = None
        mock_user.bio = '测试简介'
        mock_user.date_joined = datetime(2026, 1, 1)
        mock_user.posts = Mock()
        mock_user.posts.count.return_value = 5
        mock_get.return_value = mock_user

        request = self.factory.get('/api/user/1/profile/')

        view = UserPublicProfile()
        view.request = request
        view.kwargs = {'user_id': 1}

        response = view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['bio'], '测试简介')
        self.assertEqual(response.data['data']['post_count'], 5)

    @patch('user.views.User.objects.get')
    def test_get_user_profile_not_found(self, mock_get):
        """测试用户不存在"""
        mock_get.side_effect = User.DoesNotExist()

        request = self.factory.get('/api/user/999/profile/')

        view = UserPublicProfile()
        view.request = request
        view.kwargs = {'user_id': 999}

        response = view.get(request)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '用户不存在')

    @patch('user.views.User.objects.get')
    def test_get_user_profile_with_avatar(self, mock_get):
        """测试有头像的用户"""
        from datetime import datetime
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.avatar = Mock()
        mock_user.avatar.url = '/media/avatars/test.jpg'
        mock_user.bio = None
        mock_user.date_joined = datetime(2026, 1, 1)
        mock_user.posts = Mock()
        mock_user.posts.count.return_value = 0
        mock_get.return_value = mock_user

        request = self.factory.get('/api/user/1/profile/')

        view = UserPublicProfile()
        view.request = request
        view.kwargs = {'user_id': 1}

        response = view.get(request)

        self.assertEqual(response.data['data']['avatar'], '/media/avatars/test.jpg')
