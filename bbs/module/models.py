from django.db import models
from user.models import User


class Module(models.Model):
    """板块模型"""
    name = models.CharField('板块名称', max_length=32, unique=True)
    description = models.TextField('板块描述', blank=True, default='')
    icon = models.CharField('板块图标', max_length=50, blank=True, default='')
    admin = models.ManyToManyField(User, db_constraint=False, related_name='modulesadmin', blank=True)
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)

    class Meta:
        verbose_name = '板块'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', '-create_time']

    def __str__(self):
        return self.name

    @property
    def post_count(self):
        """帖子数量"""
        return self.posts.filter(status=0).count()

    @property
    def today_post_count(self):
        """今日帖子数"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.posts.filter(status=0, create_time__date=today).count()
