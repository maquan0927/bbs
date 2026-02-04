from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status

from message.models import Message, create_notification
from message.views import MessageList, MessageDetail, MessageReadAll, MessageUnreadCount
from common.response import ErrorCode

User = get_user_model()


class CreateNotificationTestCase(TestCase):
    """测试创建通知函数"""

    def setUp(self):
        self.user1 = Mock()
        self.user1.id = 1
        self.user2 = Mock()
        self.user2.id = 2

    def test_create_notification_self_returns_none(self):
        """测试给自己发通知返回None"""
        result = create_notification(
            user=self.user1,
            sender=self.user1,
            message_type=0,
            title='Test',
            content='Test content'
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
            title='Test Title',
            content='Test Content',
            post=None,
            repost=None
        )

        mock_create.assert_called_once_with(
            user=self.user1,
            sender=self.user2,
            type=1,
            title='Test Title',
            content='Test Content',
            post=None,
            repost=None
        )
        self.assertEqual(result, mock_message)

    @patch('message.models.Message.objects.create')
    def test_create_notification_with_post(self, mock_create):
        """测试创建带帖子的通知"""
        mock_message = Mock()
        mock_create.return_value = mock_message
        mock_post = Mock()

        result = create_notification(
            user=self.user1,
            sender=self.user2,
            message_type=2,
            title='点赞通知',
            content='有人赞了你的帖子',
            post=mock_post
        )

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['post'], mock_post)
        self.assertEqual(call_kwargs['type'], 2)


class MessageListViewTestCase(TestCase):
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

        mock_filter.assert_called_with(user=mock_user)

    @patch.object(Message.objects, 'filter')
    def test_get_queryset_filter_by_type(self, mock_filter):
        """测试按类型筛选消息"""
        mock_user = Mock()
        mock_queryset = Mock()
        mock_queryset.filter = Mock(return_value=mock_queryset)
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'type': '1'})
        request.user = mock_user
        request.query_params = {'type': '1'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(type='1')

    @patch.object(Message.objects, 'filter')
    def test_get_queryset_filter_by_read_status(self, mock_filter):
        """测试按已读状态筛选消息"""
        mock_user = Mock()
        mock_queryset = Mock()
        mock_queryset.filter = Mock(return_value=mock_queryset)
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/', {'read': '0'})
        request.user = mock_user
        request.query_params = {'read': '0'}

        self.view.request = request
        result = self.view.get_queryset()

        mock_queryset.filter.assert_any_call(read='0')


class MessageDetailViewTestCase(TestCase):
    """测试消息详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageDetail()

    @patch.object(Message.objects, 'get')
    def test_get_message_not_found(self, mock_get):
        """测试消息不存在"""
        mock_get.side_effect = Message.DoesNotExist

        request = self.factory.get('/')
        request.user = Mock()

        response = self.view.get(request, message_id=999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)
        self.assertEqual(response.data['message'], '消息不存在')

    @patch('message.views.MessageSerializer')
    @patch.object(Message.objects, 'get')
    def test_get_message_marks_as_read(self, mock_get, mock_serializer):
        """测试获取消息时标记为已读"""
        mock_message = Mock()
        mock_message.read = 0
        mock_get.return_value = mock_message
        mock_serializer.return_value.data = {'id': 1}

        request = self.factory.get('/')
        request.user = Mock()

        response = self.view.get(request, message_id=1)

        self.assertEqual(mock_message.read, 1)
        mock_message.save.assert_called_once()

    @patch('message.views.MessageSerializer')
    @patch.object(Message.objects, 'get')
    def test_get_message_already_read(self, mock_get, mock_serializer):
        """测试已读消息不会再次保存"""
        mock_message = Mock()
        mock_message.read = 1
        mock_get.return_value = mock_message
        mock_serializer.return_value.data = {'id': 1}

        request = self.factory.get('/')
        request.user = Mock()

        response = self.view.get(request, message_id=1)

        mock_message.save.assert_not_called()

    @patch.object(Message.objects, 'get')
    def test_delete_message_not_found(self, mock_get):
        """测试删除不存在的消息"""
        mock_get.side_effect = Message.DoesNotExist

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


class MessageReadAllViewTestCase(TestCase):
    """测试标记全部已读视图"""

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

        mock_filter.assert_called_with(user=mock_user, read=0)
        mock_queryset.update.assert_called_with(read=1)
        self.assertEqual(response.data['message'], '全部标记为已读')


class MessageUnreadCountViewTestCase(TestCase):
    """测试未读数量视图"""

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

        mock_filter.assert_called_with(user=mock_user, read=0)
        self.assertEqual(response.data['data']['unread_count'], 5)

    @patch.object(Message.objects, 'filter')
    def test_get_unread_count_zero(self, mock_filter):
        """测试未读消息数量为0"""
        mock_queryset = Mock()
        mock_queryset.count.return_value = 0
        mock_filter.return_value = mock_queryset

        request = self.factory.get('/')
        request.user = Mock()

        response = self.view.get(request)

        self.assertEqual(response.data['data']['unread_count'], 0)


class MessageModelTestCase(TestCase):
    """测试消息模型"""

    def test_message_type_options(self):
        """测试消息类型选项"""
        type_options = Message.type_options
        self.assertEqual(len(type_options), 5)
        self.assertEqual(type_options[0], (0, '系统通知'))
        self.assertEqual(type_options[1], (1, '回复通知'))
        self.assertEqual(type_options[2], (2, '点赞通知'))
        self.assertEqual(type_options[3], (3, '收藏通知'))
        self.assertEqual(type_options[4], (4, '@提及'))

    def test_message_read_options(self):
        """测试消息已读选项"""
        read_options = Message.read_options
        self.assertEqual(len(read_options), 2)
        self.assertEqual(read_options[0], (0, '未读'))
        self.assertEqual(read_options[1], (1, '已读'))

    def test_message_meta_ordering(self):
        """测试消息排序"""
        self.assertEqual(Message._meta.ordering, ['-create_time'])

    def test_message_meta_verbose_name(self):
        """测试消息verbose_name"""
        self.assertEqual(Message._meta.verbose_name, '消息')
