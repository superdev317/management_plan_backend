
from django.conf.urls import  *
from .api import (
    SalaryPaymentViewSet
)
from rest_framework import routers

router = routers.DefaultRouter()

router.register(
    r'salary-payments', SalaryPaymentViewSet, base_name='salary-payments'
)

urlpatterns = [
    url(r'^', include(router.urls)),
]

