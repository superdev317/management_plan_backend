
import re

from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json

from django.contrib.auth import authenticate, login, logout

import base64
import requests
from django.utils.datastructures import MultiValueDictKeyError

from paypal_users import settings


def paypal_callback(request):

    code = ''
    msg =''

    if request.method == 'GET':

        msg = 'something went wrong'

        try:
            code    = request.GET['code']

            credentials = "%s:%s" % (settings.KEY, settings.SECRET)
            encode_credential = base64.b64encode(credentials.encode('utf-8')).decode('utf-8').replace("\n", "")

            headers = {
                "Authorization": ("Basic %s" % encode_credential)
            }

            #url='https://api.sandbox.paypal.com/v1/identity/openidconnect/tokenservice?grant_type=authorization_code&code=' + code
            url='https://api.paypal.com/v1/identity/openidconnect/tokenservice?grant_type=authorization_code&code=' + code
            
            r = requests.get(url, headers=headers)

            data = r.json()
            print("ddddddddddddddddddddddd",data)

            #url2='https://api.sandbox.paypal.com/v1/oauth2/token/userinfo?schema=openid'
            url2='https://api.paypal.com/v1/oauth2/token/userinfo?schema=openid'

            headers2 = {
                "Content-Type":"application/json",
                "Authorization":("Bearer %s" % data['access_token'])
            }

            r1 = requests.get(url2, headers=headers2)
            userinfo = r1.json()
            print("uuuuuuuuuuuuuuuuuuuuuuuuuu",userinfo)

            user = authenticate(paypal_id = userinfo['user_id'],
                                username  = userinfo['name'],
                                email     = userinfo['email'],
                                )
            print("gggggggggggggggggggggggggggg",user.email)
            # Comment for birthdate error
            # birthdate = userinfo['birthdate']
            data = {'email':user.email}

            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL+'?email='+user.email+'&paypal=true')

        except MultiValueDictKeyError:
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL+'?error='+msg+'&paypal=true&is_error=true')


# def docsign_callback(request):
#     if request.method == 'GET':

#         # INTEGRATE_KEY = 'ade83a8e-99b5-404a-a845-31aff1554447'
#         # credentials = "%s:%s" % ("X-DocuSign-Authentication",{'sachin.m@intelegain.com','Docusign@2018',INTEGRATE_KEY})
#         # encode_credential = base64.b64encode(credentials.encode('utf-8')).decode('utf-8').replace("\n", "")

#         headers = {
#                 "X-DocuSign-Authentication": {"username":'sachin.m@intelegain.com',
#                                               "password":'Docusign@2018',
#                                               "IntegratorKey":'ade83a8e-99b5-404a-a845-31aff1554447'


#                 }
#         }
#         url = 'https://demo.docusign.net/restapi/v2/login_information?api_password=true'
#         r = requests.get(url, headers=headers)
#         data = r.json()
