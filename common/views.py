from django.shortcuts import render
from djmoney.settings import CURRENCY_CHOICES
from django.http import HttpResponse
import json

# Create your views here.

# Create your views here.
def currency_list(request):
	"""
	Endpoint to get currency list
	"""
	if request.method == 'GET':
		data = []
		for i in CURRENCY_CHOICES:
			data.append({"key": i[0],"value":i[1]})

		return HttpResponse(json.dumps(data), content_type="application/json")
