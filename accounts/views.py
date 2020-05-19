from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.template.response import TemplateResponse
from accounts.forms import (
    PhonePasswordResetForm, UsernamePasswordResetForm, SecurityQuestionForm, OtpValidationForm
)
from django.views.generic.edit import FormView
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth import views
import json
import functools
import warnings
from django.utils.deprecation import (
    RemovedInDjango20Warning, RemovedInDjango21Warning,
)
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)
from django.utils.encoding import force_text, force_bytes
from django.utils.http import is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode
from django.shortcuts import redirect
from .models import User, UserProfile
from django.http import HttpResponseBadRequest
from django.core import serializers
from django.contrib.auth.decorators import login_required

from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.auth import login, authenticate

import re
import requests
from .constants import (
    BANK_ACCOUNT_TYPE
)

UserModel = get_user_model()

def deprecate_current_app(func):
    """
    Handle deprecation of the current_app parameter of the views.
    """
    @functools.wraps(func)
    def inner(*args, **kwargs):
        if 'current_app' in kwargs:
            warnings.warn(
                "Passing `current_app` as a keyword argument is deprecated. "
                "Instead the caller of `{0}` should set "
                "`request.current_app`.".format(func.__name__),
                RemovedInDjango20Warning
            )
            current_app = kwargs.pop('current_app')
            request = kwargs.get('request', None)
            if request and current_app is not None:
                request.current_app = current_app
        return func(*args, **kwargs)
    return inner


@deprecate_current_app
@csrf_exempt
def password_reset(request,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=views.PasswordResetForm,
                   token_generator=views.default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   extra_context=None,
                   html_email_template_name=None,
                   extra_email_context=None):
    warnings.warn("The password_reset() view is superseded by the "
                  "class-based PasswordResetView().",
                  RemovedInDjango21Warning, stacklevel=2)

    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        content = body['email'].lower()
        request.POST = request.POST.copy()
        request.POST['email'] = content
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
                'html_email_template_name': html_email_template_name,
                'extra_email_context': extra_email_context,
            }
            form.save(**opts)
            data = 'Reset'
            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            return HttpResponseBadRequest(content=str(form.errors.as_json()))
    else:
        form = password_reset_form()
    context = {
        'form': form,
        'title': _('Password reset'),
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context)

# Doesn't need csrf_protect since no-one can guess the URL
@sensitive_post_parameters()
@never_cache
@deprecate_current_app
@csrf_exempt
def password_reset_confirm(request, uidb64=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=views.default_token_generator,
                           set_password_form=views.SetPasswordForm,
                           post_reset_redirect=None,
                           extra_context=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    warnings.warn("The password_reset_confirm() view is superseded by the "
                  "class-based PasswordResetConfirmView().",
                  RemovedInDjango21Warning, stacklevel=2)
    assert uidb64 is not None and token is not None  # checked by URLconf
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_complete')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    try:
        # urlsafe_base64_decode() decodes to bytestring on Python 3
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None
    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        request.POST = request.POST.copy()
        request.POST['new_password1'] = body['new_password']
        request.POST['new_password2'] = body['confirm_password']
    if user is not None and token_generator.check_token(user, token):
        validlink = True
        title = _('Enter new password')
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                data = 'Reset'
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                return HttpResponseBadRequest(content=str(form.errors.as_json()))
        else:
            form = set_password_form(user)
    else:
        validlink = False
        form = None
        title = _('Password reset unsuccessful')
    context = {
        'form': form,
        'title': title,
        'validlink': validlink,
    }
    if extra_context is not None:
        context.update(extra_context)

    url = settings.PASSWORD_RESET_URL+ uidb64 + '/'+ token + '/'
    # url = 'http://10.0.2.12:3000/#/resetpassword/'+ uidb64 + '/'+ token + '/'
    return redirect(url)

# 4 views for phone password reset:
# - password_reset sends the OTP
# - password_reset_done shows a success message for the above
# - password_reset_confirm checks the link the user clicked and
#   prompts for a new password
# - password_reset_complete shows a success message for the above
@csrf_exempt
def phone_password_reset(request,
                        template_name='forgot_password/phone_password_reset_form.html',
                        phone_password_reset_form=PhonePasswordResetForm,
                        token_generator=views.default_token_generator,
                        post_reset_redirect=None,
                        extra_context=None,
                        ):
    warnings.warn("The phone_password_reset() view is superseded by the "
                  "class-based PhonePasswordResetView().",
                  RemovedInDjango21Warning, stacklevel=2)

    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        content = body['phone']
        request.POST = request.POST.copy()
        request.POST['phone'] = content

    if post_reset_redirect is None:
        post_reset_redirect = reverse('otp_validation')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)

    if request.method == "POST":
        form = phone_password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'request': request,
            }
            form_data = form.save(**opts)
            return HttpResponse(json.dumps(form_data.data), content_type="application/json")
        else:
            return HttpResponseBadRequest(content=str(form.errors.as_json()))
    else:
        form = phone_password_reset_form()
    context = {
        'form': form,
        'title': _('Password reset'),
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context)

@csrf_exempt
def otp_validation(request,
                template_name='forgot_password/otp_validation_form.html',
                otp_validation_form=OtpValidationForm,
                token_generator=views.default_token_generator,
                post_reset_redirect=None,
                extra_context=None,):
    warnings.warn("The otp_validation() view is superseded by the "
                  "class-based PhonePasswordResetView().",
                  RemovedInDjango21Warning, stacklevel=2)
    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        content = body['phone']
        request.POST = request.POST.copy()
        request.POST['phone'] = content
        request.POST['otp'] = body['otp']

    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.method == "POST":
        form = otp_validation_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'request': request,
            }
            form_data = form.save(**opts)
            return HttpResponse(json.dumps(form_data.data), content_type="application/json")
        else:
            return HttpResponseBadRequest(content=str(form.errors.as_json()))

    else:
        form = otp_validation_form()
    context = {
        'form': form,
        'title': _('Password reset'),
    }
    return TemplateResponse(request, template_name, context)

class PasswordContextMixin(object):
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super(PasswordContextMixin, self).get_context_data(**kwargs)
        context['title'] = self.title
        if self.extra_context is not None:
            context.update(self.extra_context)
        return context

class PhonePasswordResetView(PasswordContextMixin, FormView):
    form_class = PhonePasswordResetForm
    title = _('Password reset')
    token_generator = views.default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(PhonePasswordResetView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super(PhonePasswordResetView, self).form_valid(form)

class OtpValidationView(PasswordContextMixin, FormView):
    form_class = OtpValidationForm
    title = _('Password reset')
    token_generator = views.default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(OtpValidationView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super(OtpValidationView, self).form_valid(form)


@csrf_exempt
def username_password_reset(request,
                        template_name='forgot_password/username_password_reset_form.html',
                        username_password_reset_form=UsernamePasswordResetForm,
                        post_reset_redirect=None,
                        extra_context=None,
                        ):
    warnings.warn("The username_password_reset() view is superseded by the "
                  "class-based PhonePasswordResetView().",
                  RemovedInDjango21Warning, stacklevel=2)
    if post_reset_redirect is None:
        post_reset_redirect = reverse('security_question_answer')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        request.POST = request.POST.copy()
        request.POST['user_name'] = body['user_name']
    if request.method == "POST":
        form = username_password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'request': request,
            }
            form_data = form.save(**opts)

            if form_data.data['security_question'][2] != 'text':
                data = {
                    'security_question': form_data.data['security_question'],
                    'vals': form_data.data['vals']
                }
            else:
                data = {
                    'security_question': form_data.data['security_question'],
                }
            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            return HttpResponseBadRequest(content=str(form.errors.as_json()))
    else:
        form = username_password_reset_form()
    context = {
        'form': form,
        'title': _('Password reset'),
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context)

@csrf_exempt
def security_question_answer(request,
                        template_name='forgot_password/security_question.html',
                        security_question_form=SecurityQuestionForm,
                        post_reset_redirect=None,
                        extra_context=None,
                        ):
    warnings.warn("The security_question_answer() view is superseded by the "
                  "class-based PhonePasswordResetView().",
                  RemovedInDjango21Warning, stacklevel=2)
    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        request.POST = request.POST.copy()
        request.POST['user_name'] = body['user_name']
        request.POST['security_question'] = body['security_question']
        request.POST['answer'] = body['answer']

    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.method == "POST":
        form = security_question_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'request': request,
            }
            form_data = form.save(**opts)
            return HttpResponse(json.dumps(form_data.data), content_type="application/json")
        else:
            return HttpResponseBadRequest(content=str(form.errors.as_json()))
    else:
        form = security_question_form()
    context = {
        'form': form,
        'title': _('Password reset'),
    }
    return TemplateResponse(request, template_name, context)

class UsernamePasswordResetView(PasswordContextMixin, FormView):
    form_class = UsernamePasswordResetForm
    title = _('Password reset')
    token_generator = views.default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(UsernamePasswordResetView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super(UsernamePasswordResetView, self).form_valid(form)

class SecurityQuestionView(PasswordContextMixin, FormView):
    form_class = SecurityQuestionForm
    title = _('Security Question')
    token_generator = views.default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(SecurityQuestionForm, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super(SecurityQuestionForm, self).form_valid(form)

@sensitive_post_parameters()
@csrf_exempt
# @login_required
@deprecate_current_app
def password_change(request,
                    template_name='registration/password_change_form.html',
                    post_change_redirect=None,
                    password_change_form=views.PasswordChangeForm,
                    extra_context=None):
    warnings.warn("The password_change() view is superseded by the "
                  "class-based PasswordChangeView().",
                  RemovedInDjango21Warning, stacklevel=2)
    if post_change_redirect is None:
        post_change_redirect = reverse('password_change_done')
    else:
        post_change_redirect = resolve_url(post_change_redirect)

    if request.content_type == 'application/json':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        request.POST = request.POST.copy()

        if  body['old_password'] and body['new_password1'] and body['new_password2']:
            request.POST['old_password'] = body['old_password']
            request.POST['new_password1'] = body['new_password1']
            request.POST['new_password2'] = body['new_password2']
        userprofile = UserProfile.objects.get(id=body['id'])
        user = User.objects.get(id=userprofile.user_id)
        request.user = user

    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Updating the password logs out all other sessions for the user
            # except the current one.
            update_session_auth_hash(request, form.user)
            # return HttpResponseRedirect(post_change_redirect)
            data = 'Reset'
            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            if  body['old_password'] and not body['new_password1'] and not body['new_password2']:
                form.errors.pop('old_password')
                return HttpResponseBadRequest(content=json.dumps(form.errors))
            elif  body['old_password'] and body['new_password1'] and not body['new_password2']:
                form.errors.pop('new_password1')
                form.errors.pop('old_password')
                return HttpResponseBadRequest(content=json.dumps(form.errors))
            elif  body['old_password'] and not body['new_password1'] and body['new_password2']:
                form.errors.pop('new_password2')
                form.errors.pop('old_password')
                return HttpResponseBadRequest(content=json.dumps(form.errors))
            elif  body['new_password1'] and not body['old_password'] and not body['new_password2']:
                form.errors.pop('new_password1')
                return HttpResponseBadRequest(content=json.dumps(form.errors))
            elif  body['new_password1'] and not body['old_password'] and body['new_password2']:
                form.errors.pop('new_password1')
                form.errors.pop('new_password2')
                return HttpResponseBadRequest(content=json.dumps(form.errors))
            elif  body['new_password2'] and not body['old_password'] and not body['new_password1']:
                form.errors.pop('new_password2')
                return HttpResponseBadRequest(content=json.dumps(form.errors))
            elif  body['new_password2'] and not body['old_password'] and body['new_password1']:
                form.errors.pop('new_password1')
                form.errors.pop('new_password2')
                return HttpResponseBadRequest(content=json.dumps(form.errors))
            else:
                return HttpResponseBadRequest(content=json.dumps(form.errors))



    else:
        form = password_change_form(user=request.user)
    context = {
        'form': form,
        'title': _('Password change'),
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)

def phone_verify(request):

    if request.method == 'GET':
        msg = ''
        phone    = request.GET['phone_number']
        KEY = '85ad58273d4d7b90bf20a931a434171d'
        url = 'http://apilayer.net/api/validate?access_key='+KEY+'&number=+'+phone+'&country_code=&format=1'
        r = requests.get(url)
        data = r.json()
        return HttpResponse(json.dumps(data), content_type="application/json")

def account_type_list(request):
    """
    Endpoint to get account types
    """
    if request.method == 'GET':
        data = []
        for i in BANK_ACCOUNT_TYPE:
            data.append({"key": i[0],"value":i[1]})

        return HttpResponse(json.dumps(data), content_type="application/json")

