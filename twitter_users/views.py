
import re

from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json

from django.contrib.auth import authenticate, login, logout

from twitter_users import oauth
from twitter_users import settings
import requests

def is_safe_redirect(redirect_to):
    if ' ' in redirect_to:
        return False
    # exclude http://foo.com URLs, but not paths with GET parameters that
    # have URLs in them (/?foo=http://foo.com)
    elif '//' in redirect_to and re.match(r'[^\?]*//', redirect_to):
        return False
    return True

def twitter_login(request, redirect_field_name='next'):
    # construct the callback URL
    try:
        protocol      = 'https' if request.is_secure() else 'http'
        host          = request.get_host()
        path          = reverse('twitter_callbackrequest')
        callback_url  = protocol + '://' + host + path
        
    except NoReverseMatch:
        callback_url = settings.CALLBACK_URL+'/api/v1/twitter/twittercallback/'
        # callback_url = None
    # get a request token from Twitter
    consumer      = oauth.Consumer(settings.KEY, settings.SECRET)
    request_token = oauth.RequestToken(consumer, callback_url=callback_url)

    # save the redirect destination
    request.session['redirect_to'] = request.POST.get(redirect_field_name, None)

    # redirect to Twitter for authorization
    return HttpResponseRedirect(request_token.authorization_url)
    
def twitter_callbackrequest(request):
    oauth_token = ''
    oauth_verifier = ''
    if request.method == 'GET':
        oauth_token    = request.GET['oauth_token']
        oauth_verifier = request.GET['oauth_verifier']

    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL+'?oauth_token='+oauth_token+'&oauth_verifier='+oauth_verifier)    

@csrf_exempt
def twitter_callback(request):
    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        request.POST = request.POST.copy()
        request.POST['oauth_token'] = body['oauth_token']
        request.POST['oauth_verifier'] = body['oauth_verifier']
        
        if request.method == 'POST':
            oauth_token    = request.POST['oauth_token']
            oauth_verifier = request.POST['oauth_verifier']
            consumer           = oauth.Consumer(settings.KEY, settings.SECRET)
            access_token       = oauth.AccessToken(consumer, oauth_token, oauth_verifier)

            user = authenticate(twitter_id  = access_token.user_id,
                        username    = access_token.username,
                        token       = access_token.token,
                        secret      = access_token.secret)

            data = {'user_name':user.user_name}
            return HttpResponse(json.dumps(data), content_type="application/json")


def twitter_logout(request, redirect_field_name='next'):
    if request.user.is_authenticated():
        # get the redirect destination
        redirect_to = request.REQUEST.get(redirect_field_name, None)
        if not redirect_to or not is_safe_redirect(redirect_to):
            try:
                redirect_to = reverse(settings.LOGOUT_REDIRECT_VIEW, args=[request.user.id])
            except NoReverseMatch:
                redirect_to = settings.LOGOUT_REDIRECT_URL
        
        logout(request)
    else:
        redirect_to = '/'
    
    return HttpResponseRedirect(redirect_to)

