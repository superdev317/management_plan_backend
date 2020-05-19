from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import SalaryPayment
from .serializers import SalaryPaymentSerializer
from django.db.models import Q


class SalaryPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = SalaryPaymentSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        return SalaryPayment.objects.filter(
            Q(project__owner=self.request.user) |
            Q(user=self.request.user)
        ).order_by('-id').distinct()
