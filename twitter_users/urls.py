
from django.conf.urls import  *
from . import views

urlpatterns = [
    
    url(r'^login/$', views.twitter_login, name="twitter_login"),
    url(r'^twittercallback/$', views.twitter_callbackrequest, name="twitter_callbackrequest"),
    url(r'^login/callback/$', views.twitter_callback, name="twitter_callback"),
    url(r'^logout/$', views.twitter_logout, name="twitter_logout"),
]

