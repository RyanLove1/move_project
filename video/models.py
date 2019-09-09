import os
from django.conf import settings
from django.db import models
from django.dispatch import receiver


# Create your models here.

#  分类表(classification)和视频表(video).他们是多对一的关系
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

    # 发邮件页面,获取视频对象信息列表
    def get_published_list(self):
        return self.filter(status=0).order_by('-create_time')

    def get_search_list(self, q):
        '''
        处理搜索功能
        :param q:
        :return:
        '''
        if q:
            return self.filter(title__contains=q).order_by('-create_time')
        else:
            return self.order_by('-create_time')

    def get_recommend_list(self):
        '''
        用户视频推荐
        :return:
        '''
        #  通过order_by把view_count降序排序，并选取前4条数据
        return self.filter(status=0).order_by('-view_count')[:4]

# 视频分类表
class Classification(models.Model):
    list_display = ("title",)
    title = models.CharField(max_length=100, blank=True, null=True)  # 分类名称
    status = models.BooleanField(default=True)  # 是否启用

    def __str__(self):
        return self.title

    class Meta:
        db_table = "v_classification"

#  视频表
class Video(models.Model):
    STATUS_CHOICES = (
        ('0', '发布中'),
        ('1', '未发布'),
    )
    title = models.CharField(max_length=100, blank=True, null=True)  # 视频标题　blank=True是允许字段为空
    desc = models.CharField(max_length=255, blank=True, null=True)  # 视频描述
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, null=True)  # 分类,多对一,on_delete=models.CASCADE级联删除
    file = models.FileField(max_length=255)  # 视频文件地址
    cover = models.ImageField(upload_to='cover/', blank=True, null=True)  # 视频封面
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, blank=True, null=True)  # 视频状态
    view_count = models.IntegerField(default=0, blank=True)  # 观看次数
    liked = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   blank=True, related_name="liked_videos")  # 喜欢的用户,settings.AUTH_USER_MODEL设置用户表,喜欢和用户多对多关系
    collected = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                       blank=True, related_name="collected_videos")  # 收藏的用户,收藏和用户多对多关系,设置别名，通过别名也可以访问数据
    create_time = models.DateTimeField(auto_now_add=True, blank=True, max_length=20)  # 创建时间

    #  用了VideoQuerySet查询器，需要我们在Video下面添加一行依赖。
    #  表示用VideoQuerySet作为Video的查询管理器
    objects = VideoQuerySet.as_manager()

    class Meta:
        db_table = "v_video"

    def increase_view_count(self):
        '''
        处理视频观看次数
        :return:
        '''
        # 观看一次增加一次记录
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def switch_like(self, user):
        '''
        实现用户喜欢不喜欢功能
        :param user:　登录的用户
        :return:
        '''
        #  判断用户是否登录，如果登录了则调用switch_like(user)来实现喜欢或不喜欢功能
        if user in self.liked.all():  # 如果用户已经在喜欢列表里,则将他移除
            self.liked.remove(user)
        else:
            self.liked.add(user)  # 如果不在喜欢列表里,将他添加到喜欢列表

    def count_likers(self):
        '''
        统计喜欢人数
        :return:
        '''
        return self.liked.count()

    def user_liked(self, user):
        if user in self.liked.all():  # 如果用户在喜欢列表里,给前端返回0,不在返回１
            return 0
        else:
            return 1

    def switch_collect(self, user):
        '''
        实现用户收藏功能,和喜欢不喜欢功能类似
        :param user:
        :return:
        '''
        if user in self.collected.all():
            self.collected.remove(user)

        else:
            self.collected.add(user)

    def count_collecters(self):
        '''
        统计收藏人数
        :return:
        '''
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
