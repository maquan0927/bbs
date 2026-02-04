from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock

from message.models import Message, create_notification
from message.views import MessageList, MessageDetail, MessageReadAll, MessageUnreadCount
from common.response import ErrorCode

User = get_user_model()


class CreateNotificationTests(TestCase):
    """测试创建通知消息的工具函数"""

    def setUp(self):
        self.user1 = Mock()
        self.user1.id = 1
        self.user2 = Mock()
        self.user2.id = 2

    def test_create_notification_returns_none_for_self(self):
        """测试不给自己发送通知"""
        result = create_notification(
            user=self.user1,
            sender=self.user1,
            message_type=0,
            title='测试标题',
            content='测试内容'
        )

        self.assertIsNone(result)

    @patch('message.models.Message.objects.create')
    def test_create_notification_success(self, mock_create):
        """测试成功创建通知"""
        mock_message = Mock()
        mock_create.return_value = mock_message

        result = create_notification(
            user=self.user1,
            sender=self.user2,
            message_type=1,
            title='新回复',
            content='有人回复了你的帖子'
        )

        mock_create.assert_called_once_with(
            user=self.user1,
            sender=self.user2,
            type=1,
            title='新回复',
            content='有人回复了你的帖子',
            post=None,
            repost=None
        )
        self.assertEqual(result, mock_message)

    @patch('message.models.Message.objects.create')
    def test_create_notification_with_post(self, mock_create):
        """测试创建带帖子关联的通知"""
        mock_post = Mock()
        mock_message = Mock()
        mock_create.return_value = mock_message

        result = create_notification(
            user=self.user1,
            sender=self.user2,
            message_type=2,
            title='点赞通知',
            content='有人赞了你的帖子',
            post=mock_post
        )

        mock_create.assert_called_once_with(
            user=self.user1,
            sender=self.user2,
            type=2,
            title='点赞通知',
            content='有人赞了你的帖子',
            post=mock_post,
            repost=None
        )


class MessageListViewTests(TestCase):
    """测试消息列表视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageList()

    @patch.object(Message.objects, 'filter')
    def test_get_queryset_returns_user_messages(self, mock_filter):
        """测试获取当前用户的消息"""
        mock_user = Mock()
        mock_queryset = Mock()
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.user = mock_user
        request.query_params = {}

        self.view.request = request
        result = self.view.get_queryset()

        mock_filter.assert_called_once_with(user=mock_user)

    @patch.object(Message.objects, 'filter')
    def test_get_queryset_filter_by_type(self, mock_filter):
        """测试按消息类型筛选"""
        mock_user = Mock()
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'type': '1'})
        request.user = mock_user
        request.query_params = {'type': '1'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(type='1')

    @patch.object(Message.objects, 'filter')
    def test_get_queryset_filter_by_read(self, mock_filter):
        """测试按已读状态筛选"""
        mock_user = Mock()
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'read': '0'})
        request.user = mock_user
        request.query_params = {'read': '0'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(read='0')


class MessageDetailViewTests(TestCase):
    """测试消息详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageDetail()

    @patch.object(Message.objects, 'get')
    def test_get_message_not_found(self, mock_get):
        """测试消息不存在"""
        mock_get.side_effect = Message.DoesNotExist()

        request = self.factory.get('/')
        request.user = Mock()

        response = self.view.get(request, message_id=999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '消息不存在')

    @patch('message.views.MessageSerializer')
    @patch.object(Message.objects, 'get')
    def test_get_message_marks_as_read(self, mock_get, mock_serializer):
        """测试获取消息后标记为已读"""
        mock_message = Mock()
        mock_message.read = 0
        mock_get.return_value = mock_message

        mock_serializer.return_value.data = {'id': 1, 'title': 'test'}

        request = self.factory.get('/')
        mock_user = Mock()
        request.user = mock_user

        response = self.view.get(request, message_id=1)

        self.assertEqual(mock_message.read, 1)
        mock_message.save.assert_called_once()

    @patch.object(Message.objects, 'get')
    def test_delete_message_not_found(self, mock_get):
        """测试删除不存在的消息"""
        mock_get.side_effect = Message.DoesNotExist()

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, message_id=999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    @patch.object(Message.objects, 'get')
    def test_delete_message_success(self, mock_get):
        """测试成功删除消息"""
        mock_message = Mock()
        mock_get.return_value = mock_message

        request = self.factory.delete('/')
        request.user = Mock()

        response = self.view.delete(request, message_id=1)

        mock_message.delete.assert_called_once()
        self.assertEqual(response.data['message'], '删除成功')


class MessageReadAllViewTests(TestCase):
    """测试标记所有消息为已读视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageReadAll()

    @patch.object(Message.objects, 'filter')
    def test_mark_all_as_read(self, mock_filter):
        """测试标记所有消息为已读"""
        mock_queryset = Mock()
        mock_filter.return_value = mock_queryset

        request = self.factory.post('/')
        mock_user = Mock()
        request.user = mock_user

        response = self.view.post(request)

        mock_filter.assert_called_once_with(user=mock_user, read=0)
        mock_queryset.update.assert_called_once_with(read=1)
        self.assertEqual(response.data['message'], '全部标记为已读')


class MessageUnreadCountViewTests(TestCase):
    """测试获取未读消息数量视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageUnreadCount()

    @patch.object(Message.objects, 'filter')
    def test_get_unread_count(self, mock_filter):
        """测试获取未读消息数量"""
        mock_queryset = Mock()
        mock_queryset.count.return_value = 5
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        mock_user = Mock()
        request.user = mock_user

        response = self.view.get(request)

        mock_filter.assert_called_once_with(user=mock_user, read=0)
        self.assertEqual(response.data['data']['unread_count'], 5)


class MessageModelTests(TestCase):
    """测试消息模型"""

    def test_message_type_options(self):
        """测试消息类型选项"""
        type_options = dict(Message.type_options)
        self.assertEqual(type_options[0], '系统通知')
        self.assertEqual(type_options[1], '回复通知')
        self.assertEqual(type_options[2], '点赞通知')
        self.assertEqual(type_options[3], '收藏通知')
        self.assertEqual(type_options[4], '@提及')

    def test_read_options(self):
        """测试已读状态选项"""
        read_options = dict(Message.read_options)
        self.assertEqual(read_options[0], '未读')
        self.assertEqual(read_options[1], '已读')
