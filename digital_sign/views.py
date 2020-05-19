
import re

from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json

from django.contrib.auth import authenticate, login, logout

import base64
import requests
from django.utils.datastructures import MultiValueDictKeyError

from digital_sign import settings
from django.views.generic import FormView, TemplateView, RedirectView
from django.template.response import TemplateResponse



from accounts.models import (User,UserProfile)
from django.core.files.storage import default_storage
import os
from django.conf import settings as new_settings
import urllib
from urllib.request import urlopen

def create_signature(request):
    urls = []
    msg = 'something went wrong'
    credentials = { "Username": settings.USERNAME,"Password": settings.PASSWORD,"IntegratorKey": settings.INTEGRATOR_KEY }
    credentials = json.dumps(credentials)
    headers={
        "content-type": "application/json",
        "x-docusign-authentication": credentials
    }
    url= settings.URL + '/login_information'
    account = requests.get(url, headers=headers)
    account_data = account.json()
    if account.status_code == 200:
        signers = []
        creator_email = request['creator_email']
        creator = User.objects.get(email=creator_email)
        user_ids = [request['emp_id'],creator.id] if request['emp_id'] else [creator.id]
        for i, user in enumerate(user_ids,start=1):
            user_obj = User.objects.get(id=user)
            userrole = UserProfile.objects.get(user_id=user)

            if userrole.role=='employee':
                xPosition = request['employeeXposition']
                yPosition = request['employeeYposition']
            
            else:
                xPosition = request['creatorXposition']
                yPosition = request['creatorYposition']

            signer = {
            "email":user_obj.email if user_obj.email else creator_email,
            "name": (user_obj.userprofile.first_name + user_obj.userprofile.last_name) if user_obj.userprofile.first_name or user_obj.userprofile.last_name else "{{}}",
            "recipientId": user_obj.id,
            "tabs": {
                "signHereTabs": [
                    {
                        "xPosition": xPosition,
                        "yPosition": yPosition,
                        "documentId": "1",
                        "pageNumber": "1"
                    }
                ]
            }
            }

            signers.append(signer)

        if request['nda']== True:
            signer1 = {
            #"email":"sashaseifollahi@gmail.com",
            "email":"pandeynidhi28@gmail.com",
            "name":"sashaseifollahi",
            "recipientId": "1",
            "tabs": {
                "signHereTabs": [
                    {
                        "xPosition":"50",
                        "yPosition": "75",
                        "documentId": "1",
                        "pageNumber": "2"
                    }
                ]
            }
            }

            signers.append(signer1)

        body = {
        "recipients": {
        "signers": signers
        },
        "emailSubject": "DocuSign API - Signature Request on Document Call",
        "documents": [
        {
            "documentId": "1",
            "name":request['document_name'],
            "documentBase64":request['document']   
        },
        ],
        "status": "sent"     
        }
        
        body = json.dumps(body)
        url2= settings.URL + '/accounts/' + account_data.get('loginAccounts')[0].get('accountId') + '/envelopes'
        r = requests.post(url2, headers=headers, data=body)
        data = r.json()
        #print("dddddddddddddddddddddddddddddddd",data)

        return data    
    else:
        return HttpResponse(msg)


def signature_status(request):
    msg = 'something went wrong'
    credentials = { "Username": settings.USERNAME,"Password": settings.PASSWORD,"IntegratorKey": settings.INTEGRATOR_KEY }
    credentials = json.dumps(credentials)
    headers={
        "content-type": "application/json",
        "x-docusign-authentication": credentials
        
    }
    url= settings.URL + '/login_information'
    account = requests.get(url, headers=headers)
    account_data = account.json()
    if account.status_code == 200:
        envelopeId = request['envelop_id']
        url= settings.URL + '/accounts/' + account_data.get('loginAccounts')[0].get('accountId') + '/envelopes/' + envelopeId
        docusign_status = requests.get(url, headers=headers)
        data = docusign_status.json()
        status = data['status']

        if status == 'completed':
            creator_email = request['creator_email']
            creator = User.objects.get(email=creator_email)
            user_ids = [request['emp_id'],creator.id] if request['emp_id'] else [creator.id]
            for user in user_ids:
                user_obj = User.objects.get(id=user)
                final_body = {
                    "returnUrl": "http://localhost/returnUrl",
                    "authenticationMethod": "None",
                    "email": user_obj.email if user_obj.email else creator_email,
                    "userName": (user_obj.userprofile.first_name + user_obj.userprofile.last_name) if user_obj.userprofile.first_name or user_obj.userprofile.last_name else "{{}}"
                
                }
                final_body = json.dumps(final_body)
                url3= settings.URL + '/accounts/' + account_data.get('loginAccounts')[0].get('accountId') + '/envelopes/' + envelopeId + '/views/recipient'
                docusign = requests.post(url3, headers=headers, data=final_body)
                url_data = docusign.json()
                
            return url_data
        else:
            data={
                "status":status
            }
            return data





    