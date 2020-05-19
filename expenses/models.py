from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from accounts.models import User
from projects.models import Project
from django.dispatch import receiver
from django.db.models.signals import post_save

# Create your models here.

class SalaryPayment(models.Model):
    """
    Model for Direct Group data
    """
    user = models.ForeignKey(User, related_name='salary_payment',blank=True, null=True)
    project = models.ForeignKey(Project, related_name='salary_payment',blank=True, null=True)
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    loggedin_hours = models.CharField(blank=True, null=True, max_length=50)
    bonus = MoneyField(max_digits=10, decimal_places=2, default_currency='USD',blank=True, null=True)
    deductions = MoneyField(max_digits=10, decimal_places=2, default_currency='USD',blank=True, null=True)
    hourly_rate = models.IntegerField(blank=True, null=True)
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD',blank=True, null=True)

# @receiver(post_save, sender=SalaryPayment)
# def auto_calculate_amount(sender, instance, created, **kwargs):
#     if created:
#         instance.amount = instance.loggedin_hours * instance.hourly_rate
#         instance.save()
