"""bbs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url

from user import views as user_views
from module import views as module_views
from post import views as post_views
from message import views as message_views

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # 用户相关
    url('^api/user/$', user_views.UserList.as_view()),
    url('^api/user/detail/$', user_views.UserDetail.as_view()),
    url('^api/user/email/$', user_views.UserEmail.as_view()),
    url('^api/user/(?P<user_id>\d+)/profile/$', user_views.UserPublicProfile.as_view()),

    # 模块/板块
    url('^api/module/$', module_views.ModuleList.as_view()),
    url('^api/module/(?P<id>\d+)/$', module_views.ModuleDetail.as_view()),

    # 帖子
    url('^api/post/$', post_views.PostList.as_view()),
    url('^api/post/(?P<id>\d+)/$', post_views.PostDetail.as_view()),
    url('^api/repost/$', post_views.RepostList.as_view()),

    # 点赞和收藏
    url('^api/post/(?P<post_id>\d+)/like/$', post_views.PostLikeView.as_view()),
    url('^api/post/(?P<post_id>\d+)/favorite/$', post_views.PostFavoriteView.as_view()),
    url('^api/user/favorites/$', post_views.UserFavoriteList.as_view()),

    # 搜索和热门
    url('^api/post/search/$', post_views.PostSearchView.as_view()),
    url('^api/post/hot/$', post_views.HotPostList.as_view()),

    # 消息通知
    url('^api/message/$', message_views.MessageList.as_view()),
    url('^api/message/(?P<message_id>\d+)/$', message_views.MessageDetail.as_view()),
    url('^api/message/read-all/$', message_views.MessageReadAll.as_view()),
    url('^api/message/unread-count/$', message_views.MessageUnreadCount.as_view()),
]
