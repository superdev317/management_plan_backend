
from django.conf.urls import  *
from . import views

urlpatterns = [
    url(r'^paypalcallback/$', views.paypal_callback, name="paypal_callback") 
]

