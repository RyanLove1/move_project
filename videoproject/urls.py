"""videoproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.conf.urls import url, include
from video import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^video/',include('video.urls')),
    url(r'^myadmin/', include('myadmin.urls')),
    url(r'^users/',include('users.urls')),
    url(r'^comment/',include('comment.urls')),
    url('^$', views.IndexView.as_view(), name='home'), # 默认首页

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)