from django.shortcuts import render
import http.client, urllib.request, urllib.parse, urllib.error, base64
from PIL import Image
import json
import time
import requests
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import boto3
from boto.s3.connection import S3Connection
from saffron_backend import settings
import uuid
from django.http import HttpResponse

# Create your views here.
# 8b9aede7f49e42a5971d62bb92f66294
# 62adba581d794f7ab97403986d969348
@csrf_exempt
def read_image(request):
	headers = {
	# Request headers
	'ocp-apim-subscription-key': 'a38764cfa44947e6a81ae6ef9278b0c6',  #'08498d322bae44f7a8d24cb91fd1bbdf' ffd0ef2f2ecd4544824603c6ba58cf36, 3ce30ffc496849c7bc6ede056fed33ad

	'content-type': 'application/octet-stream'
	}
	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)

	header, base64_data = body['image'].split(';base64,')
	data = base64.b64decode(base64_data)
	file_name = str(uuid.uuid4())[:12]

	params = urllib.parse.urlencode({
		# Request parameters
		'handwriting' : body['handwriting']
	})

	conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	conn.request("POST", "/vision/v1.0/RecognizeText?%s" % params, data, headers)
	response = conn.getresponse()
	# a = response.read().decode('utf-8')

	file_content = ""
	if response.headers["Operation-Location"]:
		analysis = {}
		while not "recognitionResult" in analysis:
			response_final = requests.get(response.headers["Operation-Location"], headers=headers)
			analysis       = response_final.json()
			time.sleep(1)

		polygons = [(line["boundingBox"], line["text"]) for line in analysis["recognitionResult"]["lines"]]
		for polygon in polygons:
			vertices = [(polygon[0][i], polygon[0][i+1]) for i in range(0,len(polygon[0]),2)]
			text     = polygon[1]
			file_content = file_content + text + '\n'

	else:
		info = response.read()
		res = json.loads(info.decode())
		line_infos = [region["lines"] for region in res["regions"]]
		for line in line_infos:
		    for word_metadata in line:
		        for word_info in word_metadata["words"]:
		        	file_content = file_content + ' ' + word_info["text"]

		        file_content = file_content + "\n"

	a = {'content': file_content}

	if body["workarea"] == False:
		client = S3Connection(settings.AWS_ACCESS_KEY_ID,settings.AWS_SECRET_ACCESS_KEY,host=settings.AWS_HOST)
		#connecting to aws with specific endpoint reason
		bucket = client.get_bucket(settings.AWS_S3_BUCKET_NAME)
		key = bucket.new_key("projects/ocr/"+file_name+ ".txt")
		key.set_contents_from_string(file_content)
		url = key.generate_url(900)
		a = {'content': file_content,'file_name':key.name}

	conn.close()
	
	return HttpResponse(json.dumps(a), content_type="application/json")


@csrf_exempt
def read_printed_text(request):
	headers = {
	# Request headers
	'ocp-apim-subscription-key': '08498d322bae44f7a8d24cb91fd1bbdf',
	'content-type': 'application/json'
	}
	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)


	data = base64.b64decode(body['image'])
	# file_name = str(uuid.uuid4())[:12]

	params = urllib.parse.urlencode({
		'language': 'en',
    	'detectOrientation ': 'true',
	})

	conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	conn.request("POST", "/vision/v1.0/ocr?%s" % params, data, headers)
	response = conn.getresponse()
	analysis = response.read()

	# client = S3Connection(settings.AWS_ACCESS_KEY_ID,settings.AWS_SECRET_ACCESS_KEY,host=settings.AWS_HOST)
	# #connecting to aws with specific endpoint reason
	# bucket = client.get_bucket(settings.AWS_S3_BUCKET_NAME)
	# key = bucket.new_key("ocr/"+file_name+ ".txt")

	file_content = ""
	line_infos = [region["lines"] for region in analysis["regions"]]
	word_infos = []
	for line in line_infos:
	    for word_metadata in line:
	        for word_info in word_metadata["words"]:
	            word_infos.append(word_info)
	

	# file_content = file_content + text + '\n'

	# key.set_contents_from_string(file_content)
	# url = key.generate_url(900)
	conn.close()
	