from django.test import TestCase, SimpleTestCase, RequestFactory
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status

from message.models import Message, create_notification
from message.views import MessageList, MessageDetail, MessageReadAll, MessageUnreadCount
from common.response import ErrorCode


class CreateNotificationTest(SimpleTestCase):
    """create_notification 函数测试"""

    @patch('message.models.Message.objects.create')
    def test_create_notification_success(self, mock_create):
        """测试成功创建通知"""
        user = Mock(id=1)
        sender = Mock(id=2)
        mock_message = Mock()
        mock_create.return_value = mock_message

        result = create_notification(
            user=user,
            sender=sender,
            message_type=1,
            title='测试标题',
            content='测试内容',
            post=None,
            repost=None
        )

        mock_create.assert_called_once_with(
            user=user,
            sender=sender,
            type=1,
            title='测试标题',
            content='测试内容',
            post=None,
            repost=None
        )
        self.assertEqual(result, mock_message)

    def test_create_notification_self_returns_none(self):
        """测试给自己发送通知返回 None"""
        user = Mock(id=1)
        result = create_notification(
            user=user,
            sender=user,  # 同一用户
            message_type=1,
            title='测试标题',
            content='测试内容'
        )
        self.assertIsNone(result)

    @patch('message.models.Message.objects.create')
    def test_create_notification_with_post(self, mock_create):
        """测试创建带帖子关联的通知"""
        user = Mock(id=1)
        sender = Mock(id=2)
        post = Mock(id=100)
        mock_create.return_value = Mock()

        create_notification(
            user=user,
            sender=sender,
            message_type=2,
            title='点赞通知',
            content='有人点赞了你的帖子',
            post=post
        )

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['post'], post)


class MessageListViewTest(SimpleTestCase):
    """MessageList 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageList()

    @patch('message.views.Message.objects')
    def test_get_queryset_filters_by_user(self, mock_objects):
        """测试按用户过滤消息"""
        request = self.factory.get('/')
        request.user = Mock(id=1)
        request.query_params = {}

        self.view.request = request
        mock_queryset = Mock()
        mock_objects.filter.return_value = mock_queryset

        self.view.get_queryset()

        mock_objects.filter.assert_called_once_with(user=request.user)

    @patch('message.views.Message.objects')
    def test_get_queryset_filters_by_type(self, mock_objects):
        """测试按消息类型过滤"""
        request = self.factory.get('/', {'type': '1'})
        request.user = Mock(id=1)
        request.query_params = {'type': '1'}

        self.view.request = request
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_objects.filter.return_value = mock_queryset

        self.view.get_queryset()

        mock_queryset.filter.assert_any_call(type='1')

    @patch('message.views.Message.objects')
    def test_get_queryset_filters_by_read_status(self, mock_objects):
        """测试按已读状态过滤"""
        request = self.factory.get('/', {'read': '0'})
        request.user = Mock(id=1)
        request.query_params = {'read': '0'}

        self.view.request = request
        mock_queryset = Mock()
        mock_queryset.filter.return_value = mock_queryset
        mock_objects.filter.return_value = mock_queryset

        self.view.get_queryset()

        mock_queryset.filter.assert_any_call(read='0')


class MessageDetailViewTest(SimpleTestCase):
    """MessageDetail 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageDetail()

    @patch('message.views.Message.objects.get')
    @patch('message.views.MessageSerializer')
    def test_get_message_success(self, mock_serializer, mock_get):
        """测试成功获取消息详情"""
        request = self.factory.get('/')
        request.user = Mock(id=1)
        mock_message = Mock(read=0)
        mock_get.return_value = mock_message
        mock_serializer.return_value.data = {'id': 1, 'title': 'test'}

        response = self.view.get(request, message_id=1)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        # 验证消息被标记为已读
        self.assertEqual(mock_message.read, 1)
        mock_message.save.assert_called_once()

    @patch('message.views.Message.objects.get')
    def test_get_message_not_found(self, mock_get):
        """测试消息不存在"""
        request = self.factory.get('/')
        request.user = Mock(id=1)
        mock_get.side_effect = Message.DoesNotExist

        response = self.view.get(request, message_id=999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    @patch('message.views.Message.objects.get')
    def test_delete_message_success(self, mock_get):
        """测试成功删除消息"""
        request = self.factory.delete('/')
        request.user = Mock(id=1)
        mock_message = Mock()
        mock_get.return_value = mock_message

        response = self.view.delete(request, message_id=1)

        mock_message.delete.assert_called_once()
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)

    @patch('message.views.Message.objects.get')
    def test_delete_message_not_found(self, mock_get):
        """测试删除不存在的消息"""
        request = self.factory.delete('/')
        request.user = Mock(id=1)
        mock_get.side_effect = Message.DoesNotExist

        response = self.view.delete(request, message_id=999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)


class MessageReadAllViewTest(SimpleTestCase):
    """MessageReadAll 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageReadAll()

    @patch('message.views.Message.objects')
    def test_mark_all_as_read(self, mock_objects):
        """测试标记所有消息为已读"""
        request = self.factory.post('/')
        request.user = Mock(id=1)
        mock_queryset = Mock()
        mock_objects.filter.return_value = mock_queryset

        response = self.view.post(request)

        mock_objects.filter.assert_called_once_with(user=request.user, read=0)
        mock_queryset.update.assert_called_once_with(read=1)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)


class MessageUnreadCountViewTest(SimpleTestCase):
    """MessageUnreadCount 视图测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MessageUnreadCount()

    @patch('message.views.Message.objects')
    def test_get_unread_count(self, mock_objects):
        """测试获取未读消息数量"""
        request = self.factory.get('/')
        request.user = Mock(id=1)
        mock_queryset = Mock()
        mock_queryset.count.return_value = 5
        mock_objects.filter.return_value = mock_queryset

        response = self.view.get(request)

        mock_objects.filter.assert_called_once_with(user=request.user, read=0)
        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['unread_count'], 5)

    @patch('message.views.Message.objects')
    def test_get_unread_count_zero(self, mock_objects):
        """测试没有未读消息时返回0"""
        request = self.factory.get('/')
        request.user = Mock(id=1)
        mock_queryset = Mock()
        mock_queryset.count.return_value = 0
        mock_objects.filter.return_value = mock_queryset

        response = self.view.get(request)

        self.assertEqual(response.data['data']['unread_count'], 0)
