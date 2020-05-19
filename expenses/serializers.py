from rest_framework import serializers
from projects.models import Project
from .models import SalaryPayment
from projects.serializers import MoneyField


class SalaryPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Salary Payment
    """
    bonus = MoneyField(required=False, allow_null=True,)
    deductions = MoneyField(required=False, allow_null=True,)
    amount = MoneyField(required=False, allow_null=True,)
    
    class Meta:
        model = SalaryPayment

        fields = ('id','user','project','from_date','to_date','loggedin_hours','bonus','deductions','hourly_rate','amount')


class ExpensesPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Salary Payment
    """
    payment_details = serializers.SerializerMethodField()

    class Meta:
        model = Project

        fields = ('id','owner','title','payment_details')

    def get_availability_details(self, obj):
        salary_details = SalaryPayment.objects.filter(project=obj)
        registration_details = obj.project.package
        return

