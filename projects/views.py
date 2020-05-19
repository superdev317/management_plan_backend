from django.shortcuts import render
from django.http import HttpResponse
import json
import requests
from django.conf import settings
from projects.models import ProductExpenses, FundInterestPay
from projects.serializers import ProductSerializer
import urllib
from urllib.request import urlopen
import base64
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from rest_framework import serializers
from django.http import HttpResponseBadRequest
from django.forms.forms import Form, ValidationError



# Create your views here.
def product_search(request):
	"""
	Endpoint to get product search data from 3rd party api
	"""
	if request.method == 'GET':
		response = []
		product    = request.GET['product']
		startparam = request.GET.get('start')
		starttext = ''
		if startparam is not None:
			starttext    = '&start=' + startparam 

		url = 'http://api.walmartlabs.com/v1/search?format=json&apiKey='+settings.PRODUCT_APIKEY+'&query='+product + starttext
		r = requests.get(url)
		product_data = r.json()
		if product_data['numItems'] > 0:
			for i in product_data['items']:
				
				sub_data={
					'product_id' : i.get('itemId'),
					'name' : i.get('name', None),
					'msrp':i.get('msrp',None),
					'price':i.get('salePrice',None),
					'categoryPath':i.get('categoryPath',None),
					'categoryNode':i.get('categoryNode',None),
					'shortDescription':i.get('shortDescription',None),
					'brandName':i.get('brandName',None),
					'thumbnailImage':i.get('thumbnailImage',None),
					'color':i.get('color',None),
					'customerRating':i.get('customerRating',None),
					'numReviews':i.get('numReviews',None),
					'bundle':i.get('bundle',None),
					'gender':i.get('gender',None),
					'age':i.get('age',None),
					'attributes':i.get('bundle',None),#features['attributes']['color']
					'largeImage':i.get('largeImage',None),
					'mediumImage':i.get('mediumImage',None)
					
				}

				response.append(sub_data)
			data={
				"totalResults":product_data['totalResults'],
				"start":product_data['start'],
				"numItems":product_data['numItems'],
				"products":response
			}
		else:
			data={}	
		return HttpResponse(json.dumps(data), content_type="application/json")


@csrf_exempt
def product_details(request):
	"""
	End point to get product details using product id 
	"""
	if request.content_type == 'application/json':
		body_unicode = request.body.decode('utf-8')
		body = json.loads(body_unicode)
		request.POST = request.POST.copy()
		request.POST['product_id'] = body['product_id']
		request.POST['project_id'] = body['project_id']
		request.POST['qty'] = body['qty']
		request.POST['url'] = body['url']

		if request.method == 'POST':
			productparam   = request.POST['product_id']
			productid = request.POST['project_id']
			qty = request.POST['qty']
			url = request.POST['url']

			productId =''
			if request.POST['url'] == True:
				producturl = request.POST['product_id']

				if "https://www.walmart.com/" in producturl:
						productId =  producturl.split('/')[::-1][0]
				else:
					return JsonResponse({"errors": [{
					        "code": 400,
					        "message": "Please provide walmart url."
					    }]})
					
			else:
				productId = str(request.POST['product_id'])

			url = 'http://api.walmartlabs.com/v1/items/'+ productId +'?format=json&apiKey='+settings.PRODUCT_APIKEY

			r = requests.get(url)

			if r.status_code == 403:
					return JsonResponse({"errors": [{
					        "code": 403,
					        "message": "Please provide walmart url."
					    }]})
		
			if r.status_code == 200:
				features = r.json()

				image = urllib.request.urlopen(features['largeImage'])
				image_64 = base64.encodestring(image.read())
				image_url = str(image_64, "utf-8").strip()

				material_data = {
					'name': features['name'],
					'price':{'amount': features['salePrice'],'currency': 'USD'},
					'project':request.POST['project_id'],
					'shortdescription':features['shortDescription'],
					'largeimage':image_url,
					'qty': request.POST['qty'],
					'product_id': productId,
				}

				s = ProductSerializer(data=material_data)
				s.is_valid(raise_exception=True)     
				s.save()
			else:
				material_data = r.json()

		return HttpResponse(json.dumps(material_data), content_type="application/json")
			

@csrf_exempt
def single_product(request):
	"""
	End point to get product details using product id 
	"""
	if request.content_type == 'application/json':
		body_unicode = request.body.decode('utf-8')
		body = json.loads(body_unicode)
		request.POST = request.POST.copy()
		request.POST['url'] = body['url']

		if request.method == 'POST':
			response = []
			attributes = ''
			for prod in body['products']:
				if request.POST['url'] == True:
					producturl = prod['product']

					if "https://www.walmart.com/" in producturl:
						productId =  producturl.split('/')[::-1][0]
					else:
						return JsonResponse({"errors": [{
						        "code": 400,
						        "message": "Please provide walmart url."
						    }]})
					
				else:
					productId = str(prod['product'])

				url = 'http://api.walmartlabs.com/v1/items/'+ productId +'?format=json&apiKey='+settings.PRODUCT_APIKEY
				r = requests.get(url)

				if r.status_code == 403:
					return JsonResponse({"errors": [{
					        "code": 403,
					        "message": "Please provide walmart url."
					    }]})

				if r.status_code == 200:
					features = r.json()
					if features.get('attributes'):
						if features.get('attributes').get('color'):
							attributes = features.get('attributes').get('color')
						else:
							attributes = None
					else:
						attributes = None
					
					sub_data={
						'itemId' : features.get('itemId',None),
						'name' : features.get('name',None),
						'msrp':features.get('msrp',None),
						'price':features.get('salePrice',None),
						'categoryPath':features.get('categoryPath',None),
						'categoryNode':features.get('categoryNode',None),
						'shortDescription':features.get('shortDescription',None),
						'brandName':features.get('brandName',None),
						'thumbnailImage':features.get('thumbnailImage',None),
						'color':features.get('color',None),
						'customerRating':features.get('customerRating',None),
						'numReviews':features.get('numReviews',None),
						'bundle':features.get('bundle',None),
						'gender':features.get('gender',None),
						'age':features.get('age',None),
						'attributes': attributes,
						'largeImage':features.get('largeImage',None),
						'mediumImage':features.get('mediumImage',None)
					
					}
					response.append(sub_data)
				data={
						"product_features":response
				}
			
			return JsonResponse(data)
			
def company_search(request):
	"""
	Endpoint to get company search data from 3rd party api
	"""
	if request.method == 'GET':
		company    = request.GET['company']
		
		
		url = 'https://api.opencorporates.com/v0.4/companies/search?q='+company+'&format=json&api_token=0xBZtsHToiTSE7MQfyxf'
		r = requests.get(url)
		company_data = r.json()

		if 'error' in company_data:
			return HttpResponse(json.dumps(company_data), content_type="application/json")
		else:
			if company_data['results'] is not None:

				if company_data['results']['companies']:
					msg=''
					status = ''
					response = []
					for i in company_data['results']['companies']:
						if i.get('company'):
							if 'us_' in i.get('company').get('jurisdiction_code'):
								msg = "This name is available in California!  We want to advise you that business names are only bound to an individual state"
								status = False
								response.append(i.get('company'))
					data={
						"company_data":response,
						"message":msg,
						"status":status
					}
					return HttpResponse(json.dumps(data), content_type="application/json")
				else:
					data={"status":True}
			else:
				data={"status":True}
		

			return HttpResponse(json.dumps(data), content_type="application/json")
							
				
