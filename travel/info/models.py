from django.db import models
from django.contrib.auth.models import User

class IndexImg(models.Model):
    img = models.CharField('轮播图', max_length=100)

    def __str__(self):
        return self.img

    class Meta:
        verbose_name = "轮播图"
        verbose_name_plural = verbose_name

class Recommend(models.Model):
    title = models.CharField('标题', max_length=100)
    img = models.CharField('图', max_length=100)
    content = models.TextField('内容')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "热门推荐"
        verbose_name_plural = verbose_name

class Tourguide(models.Model):
    title = models.CharField('标题', max_length=100)
    img = models.CharField('图', max_length=100)
    content = models.TextField('内容')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "导游风采"
        verbose_name_plural = verbose_name

class Message(models.Model):
    title = models.CharField('标题', max_length=100)
    content = models.TextField('内容')
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.SET_NULL, related_name='message', null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "留言"
        verbose_name_plural = verbose_name
