from django.db import models
from user.models import User
from module.models import Module

class Post(models.Model):
    title = models.CharField('标题', max_length=100)
    content = models.TextField('帖子内容')
    create_time = models.DateTimeField('发帖时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('修改时间', auto_now=True, null=True)
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.SET_NULL, related_name='posts', null=True)
    module = models.ForeignKey(Module, db_constraint=False, on_delete=models.SET_NULL, related_name='posts', null=True)

class RePost(models.Model):
    content = models.TextField('回帖内容')
    create_time = models.DateTimeField('回帖时间', auto_now_add=True, null=True)
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.SET_NULL, related_name='reposts', null=True)
    post = models.ForeignKey(Post, db_constraint=False, on_delete=models.CASCADE, related_name='reposts', null=True)
