from django.shortcuts import render
import re
import json
import requests
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth import authenticate, login, logout
from projects.models import  DocumentsToNotarisation

from projects.serializers import DocumentsToNotarisationSerializer
import boto
from boto.s3.key import Key
import mimetypes
import os
from django.core.files.storage import default_storage
from core.utils import convert_file_to_base64
from projects.models import NotarizationDetails, NotarizedDocuments, Project
from projects.serializers import NotarizationDetailsSerializer, NotarizedDocumentsSerializer, DocumentsToNotarisationSerializer
from django.conf import settings
from django.core.files import File
import json
import urllib
from urllib.request import urlopen
import codecs
import base64
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from core.serializers import Base64ImageField, Base64FileField

@csrf_exempt
def notary_transaction(request):

	url = "https://api.notarize.com/v1/transactions"
	headers = {
		'ApiKey':'bE86KimZDtrwD5rj9hq8RiMk',
		'Content-Type':'application/json'
	}

	
	if request.content_type == 'application/json':
		body_unicode = request.body.decode('utf-8')
		body = json.loads(body_unicode)
	#Post data to create notarise transaction which returns transaction id
	
	if request.method == "POST":
		notarize_id = ''
		project = Project.objects.get(id=body['project'])
		notarization_details = {'project':body['project'], 'email':body['email']}

		if body['id'] != 0 and body['is_draft'] == True:
			
			instance = NotarizationDetails.objects.get(id = body['id'])
			instance.email = body['email']
			instance.save()
			for doc in body['documents']:
				if doc['id'] == 0:
					notarization_doc = {'document':doc['document'],'document_name':doc['document_name'],'size':doc['size'],'is_draft':'True'}
					s = DocumentsToNotarisationSerializer(data=notarization_doc)
					s.is_valid(raise_exception=True)     
					s.save(notarization_details=instance)


			response = NotarizationDetailsSerializer(instance).data
			return HttpResponse(json.dumps(response), content_type="application/json")

		elif body['is_draft'] == True:
			
			s = NotarizationDetailsSerializer(data=notarization_details)
			s.is_valid(raise_exception=True)     
			instance = s.save()
			for doc in body['documents']:
				notarization_doc = {'document':doc['document'],'document_name':doc['document_name'],'size':doc['size'],'is_draft':'True'}
				s = DocumentsToNotarisationSerializer(data=notarization_doc)
				s.is_valid(raise_exception=True)     
				s.save(notarization_details=instance)

			response = NotarizationDetailsSerializer(instance).data
			return HttpResponse(json.dumps(response), content_type="application/json")

		else:
			if body['id'] == 0:

				s = NotarizationDetailsSerializer(data=notarization_details)
				s.is_valid(raise_exception=True)     
				instance = s.save()
				for doc in body['documents']:
					notarization_doc = {'document':doc['document'],'document_name':doc['document_name'],'size':doc['size']}
					s = DocumentsToNotarisationSerializer(data=notarization_doc)
					s.is_valid(raise_exception=True)     
					s.save(notarization_details=instance)
				
				documents = DocumentsToNotarisationSerializer(
					DocumentsToNotarisation.objects.filter(notarization_details=instance), many=True
				).data
				notarize_id = instance.id
				
			else:
				notarize_id = body['id']
				documents = DocumentsToNotarisationSerializer(
					DocumentsToNotarisation.objects.filter(notarization_details_id=body['id']), many=True
				).data

			data = {
				"documents":[i.get('document') for i in documents],
				"signer":{
						"email":body['email']	
				},
			}

			r = requests.post(url, headers=headers, data=json.dumps(data))
			trans = r.json()
			if r.status_code == 200:
				NotarizationDetails.objects.filter(id=notarize_id).update(transaction_id=trans['id'])
				obj = NotarizationDetails.objects.filter(id=notarize_id).first()
				response = NotarizationDetailsSerializer(obj).data
				return HttpResponse(json.dumps(response), content_type="application/json")
			else:
				return HttpResponse(json.dumps(trans), content_type="application/json")

	#delete functionality
	if request.method == "DELETE":
		id = request.META['QUERY_STRING'].split('id=')[1]
		id = id.split('/')[0]
		id = int(id)
		m = DocumentsToNotarisation(id=id)
		response = m.delete()
		return HttpResponse(json.dumps(response), content_type="application/json")
		
	#Get data against transaction id with status
	if request.method == "GET":
		transaction_id = request.META['QUERY_STRING'].split('transaction_id=')[1]
		url2 ="https://api.notarize.com/v1/transactions/" + transaction_id
		r1 = requests.get(url2, headers=headers)
		getresponse = r1.json()

		status = getresponse['status']
		
		if status == 'completed':
			notarization_record = getresponse['notarization_record']
			url3 = 'https://api.notarize.com/v1/notarization_records/' + notarization_record
			r2 = requests.get(url3, headers=headers)
			notaryrecordresponse = r2.json()

			document_url = [i.get('document_url') for i in notaryrecordresponse['notarized_documents']]

			doc_file = urllib.request.urlopen(document_url[0])
			doc_64 = base64.encodestring(doc_file.read())
			documents = str(doc_64, "utf-8").strip()

			data={
				'document':documents
			}

			notarization_details_obj = NotarizationDetails.objects.get(transaction_id=transaction_id)
			notarization_details_obj.first_name = notaryrecordresponse['signer_info']['first_name']
			notarization_details_obj.last_name = notaryrecordresponse['signer_info']['last_name']
			notarization_details_obj.address_line1 = notaryrecordresponse['signer_info']['address']['line1']
			notarization_details_obj.address_line2 = notaryrecordresponse['signer_info']['address']['line2']
			notarization_details_obj.city = notaryrecordresponse['signer_info']['address']['city']
			notarization_details_obj.state = notaryrecordresponse['signer_info']['address']['state']
			notarization_details_obj.country = notaryrecordresponse['signer_info']['address']['country']
			notarization_details_obj.pincode = notaryrecordresponse['signer_info']['address']['postal']
			notarization_details_obj.start = notaryrecordresponse['meeting_start']
			notarization_details_obj.end = notaryrecordresponse['meeting_end']
			notarization_details_obj.notary_name = notaryrecordresponse['notary_name']
			notarization_details_obj.notary_city = notaryrecordresponse['notary_county_city']
			notarization_details_obj.notary_registration = notaryrecordresponse['notary_registration']
			notarization_details_obj.save()
			notarize_document_obj = NotarizedDocuments.objects.filter(notarization_details=notarization_details_obj)

			if not notarize_document_obj.exists():
				s = NotarizedDocumentsSerializer(data=data)
				s.is_valid(raise_exception=True)     
				s.save(notarization_details=notarization_details_obj)
			response = NotarizationDetailsSerializer(notarization_details_obj).data
			response.update({'status': 'completed'})
			return HttpResponse(json.dumps(response), content_type="application/json")
		else:
			return HttpResponse(json.dumps(getresponse), content_type="application/json")
	
	





