from django.conf.urls import url
from . import views


app_name = 'video'
urlpatterns = [
    url('index', views.IndexView.as_view(), name='index'),
    # 搜索页面
    url('search/', views.SearchListView.as_view(), name='search'),
    # 表示详情信息，注意每条视频都是有自己的主键的，所以设置路径匹配为detail/(?P<pk>\d+)/,其中(?P<pk>\d+)表示主键
    url('detail/(?P<pk>\d+)/', views.VideoDetailView.as_view(), name='detail'),
    url('like/', views.like, name='like'),  # 喜欢功能路由
    url('collect/', views.collect, name='collect'),  # 收藏功能路由
]
