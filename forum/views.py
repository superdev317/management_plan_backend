from django.shortcuts import render
import re
import json
import requests
from .models import (Thread,Comment,ForumCategories,Topics,User,thread_view)
from django.http import HttpResponseRedirect,HttpResponse
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from .serializers import ThreadSerializer,ThreadCountSerializer
from google_places.models import Place
from ipware import get_client_ip
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
from core.serializers import Base64ImageField, Base64FileField 
from core.utils import convert_file_to_base64,convert_file_to_s3url

# Create your views here.
@csrf_exempt
@api_view(['GET', ])
def forum_user(request):
    """
    Endpoint to get thread based on user
    """
    if request.method=="GET":
        id    = request.GET['user_id']
        thread_obj = Thread.objects.filter(Q(owner= id) | Q(participants= id))
        serializer = ThreadSerializer(thread_obj, many=True)
        return Response(serializer.data)

       # return HttpResponse(json.dumps(serializer.data), content_type="application/json") 

def forum_user_list(request):
    """
    Endpoint to get forum user
    """
    if request.method=="GET":
        user_list = []
        user_data=[]
        owner_list = Thread.objects.all().values_list("owner", flat=True).distinct()
        participant_list = Thread.objects.all().values_list("participants", flat=True).distinct()
        user_list =list(set(list(owner_list)+list(participant_list)))
        for user in user_list:
            if user is not None:
                user_obj = User.objects.get(id=user)
                #google_address = Place.objects.get(id =user_obj.userprofile.address)
                #user_address = google_address.formatted_address
                user_address ="Sector 24, Turbhe, Navi Mumbai, Maharashtra 400703, India" 
                imageName = user_obj.userprofile.photo
                sub_data = {
                    "id":user,
                    "name":user_obj.userprofile.first_name + ' ' + user_obj.userprofile.last_name,
                    "city": user_address.split(',')[::-1][2],
                    "state":user_address.split(',')[::-1][1],
                    "country":user_address.split(',')[::-1][0],
                    "image": convert_file_to_s3url(imageName) if imageName else None
                }
                user_data.append(sub_data)
        data={
            "user":user_data
            
        }
        return HttpResponse(json.dumps(data), content_type="application/json") 

@api_view(['GET','POST', ])
def thread_viewcount(request):
    """
    Endpoint to get client ip address
    """
    if request.method=="GET":
        client_ip, is_routable = get_client_ip(request)
        if client_ip is not None:
            thread_id = request.GET['thread_id']
            data={
                "ip_address":client_ip,
                "thread":thread_id
            }
            s = ThreadCountSerializer(data=data)
            s.is_valid(raise_exception=True)     
            s.save()
            return Response(status=status.HTTP_201_CREATED)

