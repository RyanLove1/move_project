from django.conf.urls import url
from . import views

app_name = 'myadmin'
urlpatterns = [
    url('login/', views.login, name='login'),  # 后台管理登录
    url('logout/', views.logout, name='logout'),  # 后台管理登出

    #----------------------总览---------------------------
    url(r'^$', views.IndexView.as_view(), name='index'),  # 后台首页,数据总览功能

    #----------------------视频管理------------------------
    # 视频列表
    url('^video_list/', views.VideoListView.as_view(), name='video_list'),   # 视频列表
    url('video_add/', views.AddVideoView.as_view(), name='video_add'),  # 后台添加视频
    #  前端有个回调方法done()，该方法表示上传完毕，前端可在里面做一些额外的事情
    #  上传完毕后，调用了一个接口api_chunked_upload_complete，来给后端发送一个回执：我已上传完毕
    url('chunked_upload/',  views.MyChunkedUploadView.as_view(), name='api_chunked_upload'),  # 上传视频
    url('chunked_upload_complete/', views.MyChunkedUploadCompleteView.as_view(),name='api_chunked_upload_complete'),  # 上传完毕调用的接口
    # video_publish页面，开始发布前的资料填写
    url('video_publish/(?P<pk>\d+)', views.VideoPublishView.as_view(), name='video_publish'),
    # 点击发布，django将通过UpdateView自动为你更新视频信息。
    # 并通过get_success_url跳转到成功页面myadmin:video_publish_success
    url('video_publish_success/', views.VideoPublishSuccessView.as_view(), name='video_publish_success'),
    # 实现编辑功能
    url('video_edit/(?P<pk>\d+)/', views.VideoEditView.as_view(), name='video_edit'),
    # 视频删除
    url('video_delete/', views.video_delete, name='video_delete'),

    #----------------------分类管理（增删改查）----------------------------
    url('classification_add/', views.ClassificationAddView.as_view(), name='classification_add'),  # 分类增加管理
    url('classification_list/', views.ClassificationListView.as_view(), name='classification_list'),  # 分类管理列表
    url('classification_edit/(?P<pk>\d+)/', views.ClassificationEditView.as_view(), name='classification_edit'),  # 分类管理修改
    url('classification_delete/', views.classification_delete, name='classification_delete'),  # 分类管理删除

    #----------------------评论管理----------------------------
    url('comment_list/', views.CommentListView.as_view(), name='comment_list'),  # 评论列表
    url('comment_delete/', views.comment_delete, name='comment_delete'),  # 删除评论

    #----------------------用户管理-------------------------
    url('user_add/', views.UserAddView.as_view(), name='user_add'),  # 添加用户
    url('user_list/', views.UserListView.as_view(), name='user_list'),  # 用户列表
    url('user_edit/(?P<pk>\d+)',views.UserEditView.as_view(), name='user_edit'),  # 编辑用户
    url('user_delete/', views.user_delete, name='user_delete'),  # 删除用户

    #-----------------------订阅通知-------------------------
    # 实现发邮件
    # 当我们要给用户发送邮件的时候，需要先选择要推送的视频。然后点击通知订阅用户
    # 程序最终调用的是django自带的 send_mass_mail 函数，该函数封装了发送邮件的细节
    url('subscribe/', views.SubscribeView.as_view(), name='subscribe'),

    # -----------------------用户反馈-------------------------
    url('feedback_list/', views.FeedbackListView.as_view(), name='feedback_list'),  # 反馈列表
    url('feedback_delete/', views.feedback_delete, name='feedback_delete'),  # 反馈删除
]