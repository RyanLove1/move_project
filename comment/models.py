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
        return self.exclude(timestamp__lt=datetime.date.today()).count()

class Comment(models.Model):
    list_display = ("content","timestamp",)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # user用户
    nickname = models.CharField(max_length=30,blank=True, null=True)
    avatar = models.CharField(max_length=100,blank=True, null=True)  # 头像
    video = models.ForeignKey(Video, on_delete=models.CASCADE)  # 对应的视频
    content = models.CharField(max_length=100)  # 评论内容
    timestamp = models.DateTimeField(auto_now_add=True)  # 评论时间
    objects = CommentQuerySet.as_manager()

    class Meta:
        db_table = "v_comment"
