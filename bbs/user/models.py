from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """用户模型扩展"""
    sex_options = (
        (0, '女'),
        (1, '男'),
        (2, '保密')
    )
    sex = models.IntegerField('性别', choices=sex_options, default=2)
    birthday = models.DateField('生日', auto_now=False, auto_now_add=False, null=True, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', null=True, blank=True)
    bio = models.CharField('个人简介', max_length=200, null=True, blank=True)
    phone = models.CharField('手机号', max_length=11, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField('最后登录IP', null=True, blank=True)

    class Meta(AbstractUser.Meta):
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
