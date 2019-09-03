from django.conf.urls import url
from . import views

app_name = 'users'
urlpatterns = [
    url('^login/', views.login, name='login'),  # 登录路由
    url('^signup/', views.signup, name='signup'),  # 注册路由
    url('^logout/', views.logout, name='logout'),  # 登出路由
    url('^profile/(?P<pk>\d+)/', views.ProfileView.as_view(), name='profile'),  # 个人资料路由
    url('^change_password/', views.change_password, name='change_password'),  # 修改密码
    url('^subscribe/(?P<pk>\d+)/', views.SubscribeView.as_view(), name='subscribe'),  # 订阅功能路由
    url('^feedback/', views.FeedbackView.as_view(), name='feedback'),
    url('^(?P<pk>\d+)/collect_videos/', views.CollectListView.as_view(), name='collect_videos'),
    url('^(?P<pk>\d+)/like_videos/', views.LikeListView.as_view(), name='like_videos'),
]
