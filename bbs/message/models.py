from django.db import models
from user.models import User
from post.models import Post, RePost


class Message(models.Model):
    """消息通知模型"""
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, db_constraint=False, on_delete=models.SET_NULL, related_name='sent_messages', null=True, blank=True)
    post = models.ForeignKey(Post, db_constraint=False, on_delete=models.SET_NULL, related_name='messages', null=True, blank=True)
    repost = models.ForeignKey(RePost, db_constraint=False, on_delete=models.SET_NULL, related_name='messages', null=True, blank=True)

    type_options = (
        (0, '系统通知'),
        (1, '回复通知'),
        (2, '点赞通知'),
        (3, '收藏通知'),
        (4, '@提及'),
    )
    type = models.IntegerField('消息类型', default=0, choices=type_options)

    title = models.CharField('消息标题', max_length=100, default='')
    content = models.TextField('消息内容', default='')

    read_options = (
        (0, '未读'),
        (1, '已读')
    )
    read = models.IntegerField('是否已读', default=0, choices=read_options)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '消息'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f'{self.title} - {self.user.username}'


def create_notification(user, sender, message_type, title, content, post=None, repost=None):
    """
    创建通知消息的工具函数
    :param user: 接收用户
    :param sender: 发送用户
    :param message_type: 消息类型
    :param title: 标题
    :param content: 内容
    :param post: 关联帖子
    :param repost: 关联回复
    """
    # 不给自己发送通知
    if user == sender:
        return None

    return Message.objects.create(
        user=user,
        sender=sender,
        type=message_type,
        title=title,
        content=content,
        post=post,
        repost=repost
    )
