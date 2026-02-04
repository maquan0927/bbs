from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock

from message.models import Message, create_notification
from message.views import MessageList, MessageDetail, MessageReadAll, MessageUnreadCount
from common.response import ErrorCode

User = get_user_model()


class CreateNotificationTests(TestCase):
    """create_notification 函数测试"""

    def setUp(self):
        self.user = Mock()
        self.user.id = 1
        self.sender = Mock()
        self.sender.id = 2

    @patch('message.models.Message.objects.create')
    def test_create_notification_success(self, mock_create):
        """测试成功创建通知"""
        mock_message = Mock()
        mock_create.return_value = mock_message

        result = create_notification(
            user=self.user,
            sender=self.sender,
            message_type=1,
            title='测试标题',
            content='测试内容'
        )

        mock_create.assert_called_once_with(
            user=self.user,
            sender=self.sender,
            type=1,
            title='测试标题',
            content='测试内容',
            post=None,
            repost=None
        )
        self.assertEqual(result, mock_message)

    def test_create_notification_to_self_returns_none(self):
        """测试不给自己发送通知"""
        same_user = Mock()
        same_user.id = 1

        result = create_notification(
            user=same_user,
            sender=same_user,
            message_type=1,
            title='测试标题',
            content='测试内容'
        )

        self.assertIsNone(result)

    @patch('message.models.Message.objects.create')
    def test_create_notification_with_post(self, mock_create):
        """测试创建带帖子的通知"""
        mock_post = Mock()
        mock_message = Mock()
        mock_create.return_value = mock_message

        result = create_notification(
            user=self.user,
            sender=self.sender,
            message_type=2,
            title='点赞通知',
            content='有人点赞了你的帖子',
            post=mock_post
        )

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['post'], mock_post)

    @patch('message.models.Message.objects.create')
    def test_create_notification_with_repost(self, mock_create):
        """测试创建带回帖的通知"""
        mock_repost = Mock()
        mock_message = Mock()
        mock_create.return_value = mock_message

        result = create_notification(
            user=self.user,
            sender=self.sender,
            message_type=1,
            title='回复通知',
            content='有人回复了你的帖子',
            repost=mock_repost
        )

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['repost'], mock_repost)


class MessageListViewTests(TestCase):
    """MessageList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageList()

    @patch('message.views.Message.objects')
    def test_get_queryset_filter_by_user(self, mock_objects):
        """测试按用户过滤消息"""
        mock_user = Mock()
        mock_user.id = 1

        mock_queryset = MagicMock()
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.user = mock_user
        request.query_params = {}

        self.view.request = request
        result = self.view.get_queryset()

        mock_objects.filter.assert_called_once_with(user=mock_user)

    @patch('message.views.Message.objects')
    def test_get_queryset_filter_by_type(self, mock_objects):
        """测试按消息类型过滤"""
        mock_user = Mock()

        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/', {'type': '1'})
        request.user = mock_user
        request.query_params = {'type': '1'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_called()

    @patch('message.views.Message.objects')
    def test_get_queryset_filter_by_read_status(self, mock_objects):
        """测试按已读状态过滤"""
        mock_user = Mock()

        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/', {'read': '0'})
        request.user = mock_user
        request.query_params = {'read': '0'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_called()


class MessageDetailViewTests(TestCase):
    """MessageDetail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageDetail()

    @patch('message.views.MessageSerializer')
    @patch('message.views.Message.objects')
    def test_get_message_success(self, mock_objects, mock_serializer):
        """测试成功获取消息详情"""
        mock_user = Mock()
        mock_user.id = 1

        mock_message = Mock()
        mock_message.read = 0
        mock_objects.get.return_value = mock_message

        mock_serializer_instance = Mock()
        mock_serializer_instance.data = {'id': 1, 'title': 'test'}
        mock_serializer.return_value = mock_serializer_instance

        request = self.factory.get('/')
        request.user = mock_user

        response = self.view.get(request, message_id=1)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(mock_message.read, 1)
        mock_message.save.assert_called_once()

    @patch('message.views.Message.objects')
    def test_get_message_not_found(self, mock_objects):
        """测试消息不存在"""
        mock_user = Mock()
        mock_objects.get.side_effect = Message.DoesNotExist

        request = self.factory.get('/')
        request.user = mock_user

        response = self.view.get(request, message_id=999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    @patch('message.views.Message.objects')
    def test_delete_message_success(self, mock_objects):
        """测试成功删除消息"""
        mock_user = Mock()
        mock_message = Mock()
        mock_objects.get.return_value = mock_message

        request = self.factory.delete('/')
        request.user = mock_user

        response = self.view.delete(request, message_id=1)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        mock_message.delete.assert_called_once()

    @patch('message.views.Message.objects')
    def test_delete_message_not_found(self, mock_objects):
        """测试删除不存在的消息"""
        mock_user = Mock()
        mock_objects.get.side_effect = Message.DoesNotExist

        request = self.factory.delete('/')
        request.user = mock_user

        response = self.view.delete(request, message_id=999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)


class MessageReadAllViewTests(TestCase):
    """MessageReadAll 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageReadAll()

    @patch('message.views.Message.objects')
    def test_mark_all_as_read(self, mock_objects):
        """测试标记所有消息为已读"""
        mock_user = Mock()

        mock_queryset = Mock()
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.post('/')
        request.user = mock_user

        response = self.view.post(request)

        mock_objects.filter.assert_called_once_with(user=mock_user, read=0)
        mock_queryset.update.assert_called_once_with(read=1)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)


class MessageUnreadCountViewTests(TestCase):
    """MessageUnreadCount 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageUnreadCount()

    @patch('message.views.Message.objects')
    def test_get_unread_count(self, mock_objects):
        """测试获取未读消息数量"""
        mock_user = Mock()

        mock_queryset = Mock()
        mock_queryset.count.return_value = 5
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.user = mock_user

        response = self.view.get(request)

        mock_objects.filter.assert_called_once_with(user=mock_user, read=0)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['unread_count'], 5)

    @patch('message.views.Message.objects')
    def test_get_unread_count_zero(self, mock_objects):
        """测试未读消息为0"""
        mock_user = Mock()

        mock_queryset = Mock()
        mock_queryset.count.return_value = 0
        mock_objects.filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.user = mock_user

        response = self.view.get(request)

        self.assertEqual(response.data['data']['unread_count'], 0)
