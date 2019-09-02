from django.conf.urls import url
from . import views

app_name = 'users'
urlpatterns = [
    url('^login/', views.login, name='login'),
    url('^signup/', views.signup, name='signup'),
    url('^logout/', views.logout, name='logout'),
    url('^profile/(?P<pk>\d+)/', views.ProfileView.as_view(), name='profile'),
    url('^change_password/', views.change_password, name='change_password'),
    url('^subscribe/(?P<pk>\d+)/', views.SubscribeView.as_view(), name='subscribe'),
    url('^feedback/', views.FeedbackView.as_view(), name='feedback'),
    url('^(?P<pk>\d+)/collect_videos/', views.CollectListView.as_view(), name='collect_videos'),
    url('^(?P<pk>\d+)/like_videos/', views.LikeListView.as_view(), name='like_videos'),
]
