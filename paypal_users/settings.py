
from django.conf import settings

# Required
KEY                  = settings.PAYPAL_KEY
SECRET               = settings.PAYPAL_SECRET

# Optional
LOGIN_REDIRECT_VIEW  = getattr(settings, 'LOGIN_REDIRECT_VIEW', 'http://10.0.2.51:4200/paypalcallback')
LOGIN_REDIRECT_URL   = settings.LOGIN_REDIRECT_URL # Django supplies a default value

LOGOUT_REDIRECT_VIEW = getattr(settings, 'LOGOUT_REDIRECT_VIEW', None)
LOGOUT_REDIRECT_URL  = getattr(settings, 'LOGOUT_REDIRECT_URL',  '/')

PROFILE_MODULE       = settings.AUTH_PROFILE_MODULE
USERS_FORMAT         = getattr(settings, 'PAYPAL_USERS_FORMAT', '%s')

