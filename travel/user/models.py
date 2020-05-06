from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    sex_options = (
        (0, '女'),
        (1, '男')
    )
    sex = models.IntegerField('性别', choices=sex_options)
    birthday = models.DateField('生日', auto_now=False, auto_now_add=False,)

    class Meta(AbstractUser.Meta):
        pass