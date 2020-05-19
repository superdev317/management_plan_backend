
from django.conf.urls import  *
from . import views
# from . import abc

urlpatterns = [
    
    url(r'^read-image/$', views.read_image, name="read_image"),
    # url(r'^abc/$', abc.abc, name="abc"),
]

