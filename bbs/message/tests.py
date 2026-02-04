from django.test import TestCase
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from rest_framework.test import force_authenticate
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model

from message.models import Message, create_notification
from message.views import MessageList, MessageDetail, MessageReadAll, MessageUnreadCount
from common.response import ErrorCode

User = get_user_model()


class CreateNotificationTests(TestCase):
    """create_notification 函数测试"""

    def setUp(self):
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

    def tearDown(self):
        Message.objects.all().delete()
        User.objects.all().delete()

    def test_create_notification_success(self):
        """测试成功创建通知"""
        message = create_notification(
            user=self.user1,
            sender=self.user2,
            message_type=1,  # 回复通知
            title='新的回复',
            content='有人回复了你的帖子'
        )

        self.assertIsNotNone(message)
        self.assertEqual(message.user, self.user1)
        self.assertEqual(message.sender, self.user2)
        self.assertEqual(message.type, 1)
        self.assertEqual(message.title, '新的回复')
        self.assertEqual(message.content, '有人回复了你的帖子')
        self.assertEqual(message.read, 0)  # 默认未读

    def test_create_notification_to_self_returns_none(self):
        """测试不给自己发送通知"""
        message = create_notification(
            user=self.user1,
            sender=self.user1,  # 同一用户
            message_type=2,
            title='点赞通知',
            content='测试内容'
        )

        self.assertIsNone(message)

    def test_create_notification_different_types(self):
        """测试不同类型的通知"""
        # 系统通知
        msg_system = create_notification(
            user=self.user1,
            sender=self.user2,
            message_type=0,
            title='系统通知',
            content='系统消息'
        )
        self.assertEqual(msg_system.type, 0)

        # 点赞通知
        msg_like = create_notification(
            user=self.user1,
            sender=self.user2,
            message_type=2,
            title='点赞通知',
            content='有人点赞了你的帖子'
        )
        self.assertEqual(msg_like.type, 2)

        # 收藏通知
        msg_fav = create_notification(
            user=self.user1,
            sender=self.user2,
            message_type=3,
            title='收藏通知',
            content='有人收藏了你的帖子'
        )
        self.assertEqual(msg_fav.type, 3)


class MessageModelTests(TestCase):
    """Message 模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        Message.objects.all().delete()
        User.objects.all().delete()

    def test_message_str_representation(self):
        """测试消息字符串表示"""
        message = Message.objects.create(
            user=self.user,
            title='测试消息',
            content='消息内容',
            type=0
        )
        expected_str = f'测试消息 - {self.user.username}'
        self.assertEqual(str(message), expected_str)

    def test_message_default_read_status(self):
        """测试消息默认未读状态"""
        message = Message.objects.create(
            user=self.user,
            title='测试消息',
            content='消息内容'
        )
        self.assertEqual(message.read, 0)

    def test_message_default_type(self):
        """测试消息默认类型为系统通知"""
        message = Message.objects.create(
            user=self.user,
            title='测试消息',
            content='消息内容'
        )
        self.assertEqual(message.type, 0)

    def test_message_ordering(self):
        """测试消息按创建时间倒序排列"""
        msg1 = Message.objects.create(
            user=self.user,
            title='消息1',
            content='内容1'
        )
        msg2 = Message.objects.create(
            user=self.user,
            title='消息2',
            content='内容2'
        )

        messages = list(Message.objects.all())
        # 最新的消息应该在前面
        self.assertEqual(messages[0], msg2)
        self.assertEqual(messages[1], msg1)


class MessageListViewTests(TestCase):
    """MessageList 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        # 创建测试消息
        self.msg1 = Message.objects.create(
            user=self.user,
            title='消息1',
            content='内容1',
            type=0,
            read=0
        )
        self.msg2 = Message.objects.create(
            user=self.user,
            title='消息2',
            content='内容2',
            type=1,
            read=1
        )
        self.msg3 = Message.objects.create(
            user=self.other_user,
            title='其他用户的消息',
            content='其他内容',
            type=0
        )

    def tearDown(self):
        Message.objects.all().delete()
        User.objects.all().delete()

    def test_user_has_correct_messages(self):
        """测试用户消息数量正确"""
        user_messages = Message.objects.filter(user=self.user)
        self.assertEqual(user_messages.count(), 2)
        for msg in user_messages:
            self.assertEqual(msg.user, self.user)

    def test_filter_by_message_type_data(self):
        """测试按消息类型筛选数据"""
        messages = Message.objects.filter(user=self.user, type=0)
        self.assertEqual(messages.count(), 1)
        self.assertEqual(messages.first().type, 0)

    def test_filter_by_read_status_data(self):
        """测试按已读状态筛选数据"""
        messages = Message.objects.filter(user=self.user, read=0)
        self.assertEqual(messages.count(), 1)
        self.assertEqual(messages.first().read, 0)


class MessageDetailViewTests(TestCase):
    """MessageDetail 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.message = Message.objects.create(
            user=self.user,
            title='测试消息',
            content='消息内容',
            type=0,
            read=0
        )

    def tearDown(self):
        Message.objects.all().delete()
        User.objects.all().delete()

    def test_get_message_and_mark_as_read(self):
        """测试获取消息详情并标记为已读"""
        view = MessageDetail.as_view()
        request = self.factory.get(f'/api/message/{self.message.id}/')
        force_authenticate(request, user=self.user)

        response = view(request, message_id=self.message.id)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        # 刷新数据库中的消息
        self.message.refresh_from_db()
        self.assertEqual(self.message.read, 1)

    def test_get_nonexistent_message(self):
        """测试获取不存在的消息"""
        view = MessageDetail.as_view()
        request = self.factory.get('/api/message/9999/')
        force_authenticate(request, user=self.user)

        response = view(request, message_id=9999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    def test_get_other_user_message_fails(self):
        """测试获取其他用户的消息失败"""
        view = MessageDetail.as_view()
        request = self.factory.get(f'/api/message/{self.message.id}/')
        force_authenticate(request, user=self.other_user)

        response = view(request, message_id=self.message.id)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)

    def test_delete_message_success(self):
        """测试成功删除消息"""
        view = MessageDetail.as_view()
        request = self.factory.delete(f'/api/message/{self.message.id}/')
        force_authenticate(request, user=self.user)

        response = view(request, message_id=self.message.id)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertFalse(Message.objects.filter(id=self.message.id).exists())

    def test_delete_nonexistent_message(self):
        """测试删除不存在的消息"""
        view = MessageDetail.as_view()
        request = self.factory.delete('/api/message/9999/')
        force_authenticate(request, user=self.user)

        response = view(request, message_id=9999)

        self.assertEqual(response.data['code'], ErrorCode.NOT_FOUND)


class MessageReadAllViewTests(TestCase):
    """MessageReadAll 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # 创建多条未读消息
        for i in range(5):
            Message.objects.create(
                user=self.user,
                title=f'消息{i}',
                content=f'内容{i}',
                read=0
            )

    def tearDown(self):
        Message.objects.all().delete()
        User.objects.all().delete()

    def test_mark_all_as_read(self):
        """测试标记所有消息为已读"""
        view = MessageReadAll.as_view()
        request = self.factory.post('/api/message/read-all/')
        force_authenticate(request, user=self.user)

        # 验证初始状态
        unread_count = Message.objects.filter(user=self.user, read=0).count()
        self.assertEqual(unread_count, 5)

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        # 验证所有消息都已读
        unread_count = Message.objects.filter(user=self.user, read=0).count()
        self.assertEqual(unread_count, 0)


class MessageUnreadCountViewTests(TestCase):
    """MessageUnreadCount 视图测试"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # 创建3条未读消息和2条已读消息
        for i in range(3):
            Message.objects.create(
                user=self.user,
                title=f'未读消息{i}',
                content=f'内容{i}',
                read=0
            )
        for i in range(2):
            Message.objects.create(
                user=self.user,
                title=f'已读消息{i}',
                content=f'内容{i}',
                read=1
            )

    def tearDown(self):
        Message.objects.all().delete()
        User.objects.all().delete()

    def test_get_unread_count(self):
        """测试获取未读消息数量"""
        view = MessageUnreadCount.as_view()
        request = self.factory.get('/api/message/unread-count/')
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.data['code'], ErrorCode.SUCCESS)
        self.assertEqual(response.data['data']['unread_count'], 3)
