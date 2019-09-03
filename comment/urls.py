from django.conf.urls import url
from . import views

app_name = 'comment'
urlpatterns = [
    # 提交评论内容
    url('submit_comment/(?P<pk>\d+)',views.submit_comment, name='submit_comment'),
    # 获取评论内容
    url('get_comments/', views.get_comments, name='get_comments'),
]
