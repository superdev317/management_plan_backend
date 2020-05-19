from django.db import models
from accounts.models import User
from projects.models import Project, ProjectLaunchType
from djmoney.models.fields import MoneyField
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save

ORDER_TYPE = [('market','market'),
			('limit','limit')]

EXCHANGE_TYPE = [('isx','isx'),
			('lsx','lsx')]

# Create your models here.

class OrderInfo(models.Model):
	"""
	Model for Order Info
	"""
	order_time = models.DateTimeField(blank=True, null=True)
	quantity = models.IntegerField(null=True)
	# price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
	order_type = models.CharField(choices=ORDER_TYPE,default=ORDER_TYPE[0][0],max_length=10)
	limit_price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
	exchange_type = models.CharField(max_length=10, choices=EXCHANGE_TYPE, blank=True, null=True)
	is_closed = models.BooleanField(
		_('Is Closed'),
		default=False,
	)
	remain_quantity = models.IntegerField(null=True)
	lots_pending = models.IntegerField(null=True)

	class Meta:
	    abstract = True

class Bid(OrderInfo):
	"""
	Model for Bid
	"""
	bid_by = models.ForeignKey(User,related_name='bid',blank=True, null=True)
	project = models.ForeignKey(Project,related_name='bid',blank=True, null=True)
	launch_type = models.ForeignKey(ProjectLaunchType,related_name='bid',blank=True, null=True)
	lots_filled = models.IntegerField(null=True,default=0)

class Ask(OrderInfo):
	"""
	Model for Ask
	"""
	ask_by = models.ForeignKey(User,related_name='ask',blank=True, null=True)
	project = models.ForeignKey(Project,related_name='ask',blank=True, null=True)
	launch_type = models.ForeignKey(ProjectLaunchType,related_name='ask',blank=True, null=True)
	lots_sold = models.IntegerField(null=True,default=0)

class OrderBook(models.Model):
	"""
	Model for Order Book
	"""
	buyer = models.ForeignKey(User,related_name='order_book_buyer',blank=True, null=True)
	seller = models.ForeignKey(User,related_name='order_book_seller',blank=True, null=True)
	project = models.ForeignKey(Project,related_name='order_book',blank=True, null=True)
	bid_id = models.ForeignKey(Bid,related_name='order_book',blank=True, null=True)
	ask_id = models.ForeignKey(Ask,related_name='order_book',blank=True, null=True)
	shares = models.IntegerField(null=True)
	price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')

	
