
from django.conf.urls import  *
from .api import (
    BidViewSet, AskViewSet, LaunchProjectListView
)
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()

router.register(
    r'bidding', BidViewSet, base_name='bidding'
)
router.register(
    r'asking', AskViewSet, base_name='asking'
)
router.register(
    r'launch-project-list', LaunchProjectListView, base_name='launch_project_list'
)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^mapping', mapping, name='mapping'),
]



