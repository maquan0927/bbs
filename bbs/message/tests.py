from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from message.models import Message, create_notification
from message.views import MessageList, MessageDetail, MessageReadAll, MessageUnreadCount

User = get_user_model()


class CreateNotificationTest(TestCase):
    """测试创建通知工具函数"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='senderpass123'
        )

    def test_create_notification_success(self):
        """测试成功创建通知"""
        message = create_notification(
            user=self.user,
            sender=self.sender,
            message_type=1,
            title='测试标题',
            content='测试内容'
        )

        self.assertIsNotNone(message)
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.type, 1)
        self.assertEqual(message.title, '测试标题')
        self.assertEqual(message.content, '测试内容')
        self.assertEqual(message.read, 0)

    def test_create_notification_self_returns_none(self):
        """测试自己给自己发通知返回None"""
        message = create_notification(
            user=self.user,
            sender=self.user,  # 同一用户
            message_type=1,
            title='测试标题',
            content='测试内容'
        )

        self.assertIsNone(message)

    def test_create_notification_with_post(self):
        """测试创建带帖子关联的通知"""
        from post.models import Post
        from module.models import Module

        module = Module.objects.create(name='测试板块')
        post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            user=self.sender,
            module=module
        )

        message = create_notification(
            user=self.user,
            sender=self.sender,
            message_type=2,
            title='点赞通知',
            content='有人给你的帖子点赞了',
            post=post
        )

        self.assertIsNotNone(message)
        self.assertEqual(message.post, post)


class MessageModelTest(TestCase):
    """测试消息模型"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_message_str_method(self):
        """测试消息的字符串表示"""
        message = Message.objects.create(
            user=self.user,
            title='测试消息',
            content='测试内容',
            type=0
        )

        self.assertEqual(str(message), f'测试消息 - {self.user.username}')

    def test_message_default_read_status(self):
        """测试消息默认未读状态"""
        message = Message.objects.create(
            user=self.user,
            title='测试消息',
            content='测试内容'
        )

        self.assertEqual(message.read, 0)

    def test_message_ordering(self):
        """测试消息按创建时间倒序排列"""
        Message.objects.create(
            user=self.user,
            title='消息1',
            content='内容1'
        )
        Message.objects.create(
            user=self.user,
            title='消息2',
            content='内容2'
        )

        messages = Message.objects.all()
        self.assertEqual(messages[0].title, '消息2')
        self.assertEqual(messages[1].title, '消息1')


class MessageListViewTest(APITestCase):
    """测试消息列表视图"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client = APIClient()

        # 创建测试消息
        self.message1 = Message.objects.create(
            user=self.user,
            title='消息1',
            content='内容1',
            type=0,
            read=0
        )
        self.message2 = Message.objects.create(
            user=self.user,
            title='消息2',
            content='内容2',
            type=1,
            read=1
        )
        # 其他用户的消息
        Message.objects.create(
            user=self.other_user,
            title='其他用户消息',
            content='内容'
        )

    def test_message_list_filter_by_type(self):
        """测试按类型筛选消息"""
        factory = RequestFactory()
        request = factory.get('/', {'type': '0'})
        request.user = self.user
        # 为 WSGIRequest 添加 query_params 属性
        request.query_params = request.GET

        view = MessageList()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().type, 0)

    def test_message_list_filter_by_read_status(self):
        """测试按已读状态筛选消息"""
        factory = RequestFactory()
        request = factory.get('/', {'read': '0'})
        request.user = self.user
        # 为 WSGIRequest 添加 query_params 属性
        request.query_params = request.GET

        view = MessageList()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().read, 0)


class MessageDetailViewTest(APITestCase):
    """测试消息详情视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.message = Message.objects.create(
            user=self.user,
            title='测试消息',
            content='测试内容',
            read=0
        )

    def test_get_message_marks_as_read(self):
        """测试获取消息详情后标记为已读"""
        request = self.factory.get(f'/api/message/{self.message.id}/')
        request.user = self.user

        view = MessageDetail()
        response = view.get(request, message_id=self.message.id)

        self.message.refresh_from_db()
        self.assertEqual(self.message.read, 1)
        self.assertEqual(response.data['code'], 0)

    def test_get_nonexistent_message(self):
        """测试获取不存在的消息"""
        request = self.factory.get('/api/message/99999/')
        request.user = self.user

        view = MessageDetail()
        response = view.get(request, message_id=99999)

        self.assertEqual(response.data['code'], 1002)  # NOT_FOUND

    def test_delete_message_success(self):
        """测试成功删除消息"""
        request = self.factory.delete(f'/api/message/{self.message.id}/')
        request.user = self.user

        view = MessageDetail()
        response = view.delete(request, message_id=self.message.id)

        self.assertEqual(response.data['code'], 0)
        self.assertFalse(Message.objects.filter(id=self.message.id).exists())

    def test_delete_nonexistent_message(self):
        """测试删除不存在的消息"""
        request = self.factory.delete('/api/message/99999/')
        request.user = self.user

        view = MessageDetail()
        response = view.delete(request, message_id=99999)

        self.assertEqual(response.data['code'], 1002)


class MessageReadAllViewTest(APITestCase):
    """测试标记所有消息已读视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # 创建多条未读消息
        for i in range(3):
            Message.objects.create(
                user=self.user,
                title=f'消息{i}',
                content=f'内容{i}',
                read=0
            )

    def test_mark_all_as_read(self):
        """测试标记所有消息为已读"""
        request = self.factory.post('/api/message/read-all/')
        request.user = self.user

        view = MessageReadAll()
        response = view.post(request)

        unread_count = Message.objects.filter(user=self.user, read=0).count()
        self.assertEqual(unread_count, 0)
        self.assertEqual(response.data['code'], 0)


class MessageUnreadCountViewTest(APITestCase):
    """测试未读消息数量视图"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # 创建2条未读和1条已读消息
        Message.objects.create(user=self.user, title='消息1', content='内容1', read=0)
        Message.objects.create(user=self.user, title='消息2', content='内容2', read=0)
        Message.objects.create(user=self.user, title='消息3', content='内容3', read=1)

    def test_get_unread_count(self):
        """测试获取未读消息数量"""
        request = self.factory.get('/api/message/unread-count/')
        request.user = self.user

        view = MessageUnreadCount()
        response = view.get(request)

        self.assertEqual(response.data['code'], 0)
        self.assertEqual(response.data['data']['unread_count'], 2)
