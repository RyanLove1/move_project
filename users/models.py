from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# 用户信息表
class User(AbstractUser):
    # gender是性别字段,其中用到了choices=GENDER_CHOICES.这种方式常常用在下拉框或单多选框，例如 M对应男 F对应女。
    GENDER_CHOICES = (('M','男'),
                      ('F','女'))
    nickname = models.CharField(blank=True,null=True,max_length=20)  # 昵称
    avatar = models.FileField(upload_to='avatar/')  # 头像
    mobile = models.CharField(blank=True,null=True,max_length=13)  # 手机号
    gender = models.CharField(max_length=1,choices=GENDER_CHOICES,blank=True)
    subscribe = models.BooleanField(default=False)  # 是否订阅

    class Meta:
        db_table = 'v_user'

# 反馈的意见表
class Feedback(models.Model):
    contact = models.CharField(blank=True, null=True, max_length=20)  # 联系方式
    content = models.CharField(blank=True, null=True, max_length=200)  # 内容
    timestamp = models.DateTimeField(auto_now_add=True, null=True)  # 时间

    class Meta:
        db_table = "v_feedback"