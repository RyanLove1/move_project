import os
from django.conf import settings
from django.db import models
from django.dispatch import receiver


# Create your models here.

#  分类表(classification)和视频表(video)。他们是多对一的关系

class VideoQuerySet(models.query.QuerySet):
    # 视频总数
    def get_count(self):
        return self.count()

    #　发布数
    def get_published_count(self):
        return self.filter(status=0).count()

    #  未发布数
    def get_not_published_count(self):
        return self.filter(status=1).count()

    def get_published_list(self):
        return self.filter(status=0).order_by('-create_time')

    def get_search_list(self, q):
        if q:
            return self.filter(title__contains=q).order_by('-create_time')
        else:
            return self.order_by('-create_time')

    def get_recommend_list(self):
        #  通过order_by把view_count降序排序，并选取前4条数据
        return self.filter(status=0).order_by('-view_count')[:4]


class Classification(models.Model):
    list_display = ("title",)
    title = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "v_classification"


class Video(models.Model):
    STATUS_CHOICES = (
        ('0', '发布中'),
        ('1', '未发布'),
    )
    title = models.CharField(max_length=100, blank=True, null=True)  # 视频标题
    desc = models.CharField(max_length=255, blank=True, null=True)  # 视频描述
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, null=True)
    file = models.FileField(max_length=255)  # 视频文件地址
    cover = models.ImageField(upload_to='cover/', blank=True, null=True)  # 视频封面
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, blank=True, null=True)  # 视频状态
    view_count = models.IntegerField(default=0, blank=True)  # 观看次数
    liked = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   blank=True, related_name="liked_videos")  # 喜欢的用户
    collected = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                       blank=True, related_name="collected_videos")  # 收藏的用户
    create_time = models.DateTimeField(auto_now_add=True, blank=True, max_length=20)  # 创建时间

    #  用了VideoQuerySet查询器，需要我们在Video下面添加一行依赖。
    #  表示用VideoQuerySet作为Video的查询管理器
    objects = VideoQuerySet.as_manager()

    class Meta:
        db_table = "v_video"

    def increase_view_count(self):
        # 观看一次增加一次记录
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def switch_like(self, user):
        #  判断用户是否登录，如果登录了则调用switch_like(user)来实现喜欢或不喜欢功能
        if user in self.liked.all():
            self.liked.remove(user)
        else:
            self.liked.add(user)

    def count_likers(self):
        return self.liked.count()

    def user_liked(self, user):
        if user in self.liked.all():
            return 0
        else:
            return 1

    def switch_collect(self, user):
        if user in self.collected.all():
            self.collected.remove(user)

        else:
            self.collected.add(user)

    def count_collecters(self):
        return self.collected.count()

    def user_collected(self, user):
        if user in self.collected.all():
            return 0
        else:
            return 1


@receiver(models.signals.post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    删除FileField文件
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
