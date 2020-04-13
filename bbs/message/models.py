from django.db import models
from user.models import User
from post.models import Post

class Message(models.Model):
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.SET_NULL, related_name='message', null=True)
    post = models.ForeignKey(Post, db_constraint=False, on_delete=models.SET_NULL, related_name='message', null=True)
    type_options = (
        (0, '系统通知'),
        (1, '个人消息')
    )
    type = models.IntegerField('消息类型', default=0, choices=type_options)
    read_options = (
        (0, '未读'),
        (1, '已读')
    )
    read = models.IntegerField('是否已读', default=0, choices=read_options)