
from django.conf.urls import  *
from . import views

urlpatterns = [
    url(r'^notary-transaction', views.notary_transaction, name='notary_transaction'),
]

