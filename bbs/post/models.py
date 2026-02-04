from django.db import models
from user.models import User
from module.models import Module


class Post(models.Model):
    """帖子模型"""
    title = models.CharField('标题', max_length=100)
    content = models.TextField('帖子内容')
    create_time = models.DateTimeField('发帖时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('修改时间', auto_now=True, null=True)
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.SET_NULL, related_name='posts', null=True)
    module = models.ForeignKey(Module, db_constraint=False, on_delete=models.SET_NULL, related_name='posts', null=True)
    # 新增字段
    view_count = models.PositiveIntegerField('浏览量', default=0)
    is_top = models.BooleanField('是否置顶', default=False)
    is_essence = models.BooleanField('是否精华', default=False)
    status_options = (
        (0, '正常'),
        (1, '已删除'),
        (2, '待审核')
    )
    status = models.IntegerField('状态', choices=status_options, default=0)

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = verbose_name
        ordering = ['-is_top', '-create_time']

    def __str__(self):
        return self.title

    @property
    def like_count(self):
        """点赞数"""
        return self.likes.count()

    @property
    def favorite_count(self):
        """收藏数"""
        return self.favorites.count()

    @property
    def reply_count(self):
        """回复数"""
        return self.reposts.count()


class RePost(models.Model):
    """回帖模型"""
    content = models.TextField('回帖内容')
    create_time = models.DateTimeField('回帖时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('修改时间', auto_now=True, null=True)
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.SET_NULL, related_name='reposts', null=True)
    post = models.ForeignKey(Post, db_constraint=False, on_delete=models.CASCADE, related_name='reposts', null=True)
    # 支持回复嵌套
    parent = models.ForeignKey('self', db_constraint=False, on_delete=models.CASCADE, related_name='children', null=True, blank=True)

    class Meta:
        verbose_name = '回帖'
        verbose_name_plural = verbose_name
        ordering = ['create_time']

    def __str__(self):
        return f'{self.user.username if self.user else "匿名"}的回复'


class PostLike(models.Model):
    """帖子点赞"""
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, db_constraint=False, on_delete=models.CASCADE, related_name='likes')
    create_time = models.DateTimeField('点赞时间', auto_now_add=True)

    class Meta:
        verbose_name = '帖子点赞'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'post')

    def __str__(self):
        return f'{self.user.username} 赞了 {self.post.title}'


class PostFavorite(models.Model):
    """帖子收藏"""
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.CASCADE, related_name='post_favorites')
    post = models.ForeignKey(Post, db_constraint=False, on_delete=models.CASCADE, related_name='favorites')
    create_time = models.DateTimeField('收藏时间', auto_now_add=True)

    class Meta:
        verbose_name = '帖子收藏'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'post')

    def __str__(self):
        return f'{self.user.username} 收藏了 {self.post.title}'
