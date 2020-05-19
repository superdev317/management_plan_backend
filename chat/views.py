from django.shortcuts import render
import requests
import json
from .helpers import RocketChat
from django.http import HttpResponse
from .models import UserChat, MessageType, DecisionPollVote, DirectGroup
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import http.client,urllib.request, urllib.parse, urllib.error
import urllib
from projects.models import ProjectFund
import base64
from base64 import *
from boto.s3.connection import S3Connection
from saffron_backend import settings

# Create your views here.

@csrf_exempt
def upload_file(request):
	headers = {
		"X-Auth-Token": request.META['HTTP_X_AUTH_TOKEN'],
		"X-User-Id": request.META['HTTP_X_USER_ID'],
		"Content-Type": request.META['CONTENT_TYPE']
	}

	conn = http.client.HTTPConnection("localhost:3000")
	conn.request("POST", "/api/v1/rooms.upload/"+request.META['HTTP_ROOMID'] , request.body, headers)

	rocket = RocketChat(
				headers={
					"X-Auth-Token": request.META['HTTP_X_AUTH_TOKEN'],
					"X-User-Id": request.META['HTTP_X_USER_ID'],
				}
			)
	
	res = conn.getresponse()
	response = res.read()
	r = rocket.groups_history(room_id=request.META['HTTP_ROOMID'])
	user_message_list = []
	result = r.json()
	if r.status_code == 200:
		for i in result['messages']:
			if i['u']['_id']==request.META['HTTP_X_USER_ID']:
				user_message_list.append(i['_id'])

	if user_message_list:
		MessageType.objects.create(
			group_id= request.META['HTTP_ROOMID'],
			message_id= user_message_list[0],
			message_type= request.META['HTTP_MESSAGETYPE'],
			chat_user_id=request.META['HTTP_X_USER_ID'],
		)

	return HttpResponse(response, content_type="application/json")


@csrf_exempt
def post_chat(request):

	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)

	rocket = RocketChat(
				headers=body['header']
				)	
	r = rocket.chat_post_message(text=body['text'],
								room_id=body['roomId'],
								attachments=body['attachments'],
								emoji=body['emoji'],)
	result = r.json()

	MessageType.objects.create(
			group_id= body['roomId'],
			message_id= result['message']['_id'],
			message_type= body['message_type'],
			parent_message_id= body['parent_message_id'],
			chat_user_id=body['header']['X-User-Id'],
			options=body['options']
		)
	
	result['message'].update({'message_type':body['message_type']})

	return HttpResponse(json.dumps(result), content_type="application/json")

@csrf_exempt
def group_history(request):
	final_list = []
	# if request.content_type == 'application/json':
	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)

	rocket = RocketChat(
				headers=body['header']
				)	
	r = rocket.groups_history(room_id=body['roomId'])
	result = r.json()

	if r.status_code == 200:
		for i in result['messages']:
			message_type_obj = MessageType.objects.filter(message_id=i['_id']).first()
			if message_type_obj:
				i.update({'message_type': message_type_obj.message_type})
				if message_type_obj.message_type == 'decision_poll':
					is_vote = DecisionPollVote.objects.filter(chat_user_id=body['header']['X-User-Id'], message_id=i['_id']).values_list('id')
					if is_vote.exists():
						i.update({'is_reply': True})
					i.update({'options': message_type_obj.options,'voting_result': message_type_obj.voting})
			is_apply = MessageType.objects.filter(parent_message_id=i['_id'],message_type='',chat_user_id=body['header']['X-User-Id'])
			
			if is_apply.exists():
				i.update({'is_reply': True})

			if i['u']['username'] == 'admin':
				pass
			else:
				final_list.append(i)
	data = {'messages': final_list}
	return HttpResponse(json.dumps(data), content_type="application/json")



@csrf_exempt
def direct_chat_room(request):

	# if request.content_type == 'application/json':
	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)

	# auth_token = request.META['QUERY_STRING'].split('auth_token=')[1]
	# chat_user_id = request.META['QUERY_STRING'].split('chat_user_id=')[1]
	# headers = {
	# 	"X-Auth-Token": auth_token,
	# 	"X-User-Id": chat_user_id,
	# 	"Content-Type": "application/json"
	# }
	headers = {
		"X-Auth-Token": "g_ng05UM9lETYtqS3BXVe_XsB250XXdoVz0nQCL0eQf",
		"X-User-Id": "fzw8ZKvAihqiMXdFp",
		"Content-Type": "application/json"
	}

	conn = http.client.HTTPConnection("localhost:3000")
	conn.request("POST", "/api/v1/im.create/", body , headers)

	res = conn.getresponse()
	response = res.read()

	return HttpResponse(response, content_type="application/json")

@csrf_exempt
def direct_room_list(request):
	# X-Auth-Token=_Drp_686jinjcyxx2PRH2d1y46prf7fag89sOc3-Bkz&X-User-Id=ZcjcjsA42Rc4MWFj8

	auth_token = request.META['QUERY_STRING'].split('&X-User-Id=')[0].split('X-Auth-Token=')[1]
	chat_user_id = request.META['QUERY_STRING'].split('&X-User-Id=')[1]

	headers = {
		"X-Auth-Token": auth_token,
		"X-User-Id": chat_user_id,
		"Content-Type": "application/json"
	}

	rocket = RocketChat(
				headers=headers
				)	

	r = rocket.im_list()
	result = r.json()

	if r.status_code == 200:
		for i in result['ims']:
			direct_group = DirectGroup.objects.filter(group_id=i.get("_id")).first()
			if direct_group:
				if direct_group.participant1 == chat_user_id:
					room_name = UserChat.objects.filter(chat_user_id=direct_group.participant2).values_list("username",flat=True).first()
					i.update({'room_name':room_name})
				elif direct_group.participant2 == chat_user_id:
					room_name = UserChat.objects.filter(chat_user_id=direct_group.participant1).values_list("username",flat=True).first()
					i.update({'room_name':room_name})
	return HttpResponse(json.dumps(result), content_type="application/json")

@csrf_exempt
def direct_room_history(request):

	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)

	rocket = RocketChat(
				headers=body['header']
				)	
	r = rocket.im_history(room_id=body['roomId'])
	result = r.json()
	for i in result['messages']:
		# i.get('u').get('_id')
		if i.get('u').get('_id') == body['header'].get('X-User-Id'):
			i.update({'flag':True})
		else:
			i.update({'flag':False})
	return HttpResponse(json.dumps(result), content_type="application/json")

@csrf_exempt
def post_show_interest_msg(request):

	# if request.content_type == 'application/json':
	body_unicode = request.body.decode('utf-8')
	body = json.loads(body_unicode)

	headers = body['header']

	fund_obj = ProjectFund.objects.filter(id=body["fund"]).first()
	if fund_obj:
		user = UserChat.objects.filter(user=fund_obj.owner).first()
		direct_room_body = {'username': user.username}
		conn = http.client.HTTPConnection("localhost:3000")
		conn.request("POST", "/api/v1/im.create/", json.dumps(direct_room_body) , headers)

		res = conn.getresponse()
		response = res.read()

		DirectGroup.objects.get_or_create(
                    group_id=json.loads(response.decode('utf-8'))['room']['_id'],
                    participant1=body['header'].get('X-User-Id'),
                    participant2=user.chat_user_id
                )

		room_id = json.loads(response.decode('utf-8'))['room']['_id']
		
		rocket = RocketChat(
					headers = headers
					)	
		r = rocket.chat_post_message(text= 'I am Interested in "' +fund_obj.fund.title +'" for ' + fund_obj.project.title,
									room_id=room_id)
		result = r.json()
		return HttpResponse(json.dumps(result), content_type="application/json")
	else:
		data = {"message": "data related to fund does not exists"}
		return HttpResponse(data, content_type="application/json")