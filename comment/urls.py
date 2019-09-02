from django.conf.urls import url
from . import views

app_name = 'comment'
urlpatterns = [
    url('submit_comment/(?P<pk>\d+)',views.submit_comment, name='submit_comment'),
    url('get_comments/', views.get_comments, name='get_comments'),
]
