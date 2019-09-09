import datetime
from django.conf import settings
from django.db import models
from video.models import Video


class CommentQuerySet(models.query.QuerySet):
    # 评论总数
    def get_count(self):
        return self.count()
    # 今日新增
    def get_today_count(self):
        # 通过exclude来过滤时间，使用了 lt 标签来过滤
        return self.exclude(timestamp__lt=datetime.date.today()).count()

class Comment(models.Model):
    '''
    用户评论表
    '''
    list_display = ("content","timestamp",)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 评论用户,一对多,一个用户可以被多个用户评论
    nickname = models.CharField(max_length=30,blank=True, null=True)  # 昵称
    avatar = models.CharField(max_length=100,blank=True, null=True)  # 头像
    video = models.ForeignKey(Video, on_delete=models.CASCADE)  # 对应的视频,一对多,一个视频可以被多个用户评论
    content = models.CharField(max_length=100)  # 评论内容
    timestamp = models.DateTimeField(auto_now_add=True)  # 评论时间

    # 用了CommentQuerySet查询器，需要我们在Comment下面添加一行依赖。
    # 表示用CommentQuerySet作为Comment的查询管理器
    objects = CommentQuerySet.as_manager()

    class Meta:
        db_table = "v_comment"
