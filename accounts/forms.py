from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm

from .models import User, SecurityQuestion, KeyVal, Answer, UserProfile
from phonenumber_field.formfields import PhoneNumberField
from django.utils.translation import ugettext, ugettext_lazy as _

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status, generics
from django.core.validators import MinLengthValidator
from django.utils.encoding import force_text, force_bytes
from django.utils.http import is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode

UserModel = get_user_model()

class UserProfileCreationForm(forms.Form):
    phone = PhoneNumberField()
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            try:
                User.objects.get(userprofile__phone_number=phone)
                raise forms.ValidationError(
                    'This phone has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return phone

class UserNameCreationForm(forms.Form):
    user_name = forms.CharField(label=_("Username"), widget=forms.TextInput(attrs={'autofocus': True}), max_length=500,validators=[MinLengthValidator(5)])
    
    def clean_user_name(self):
        user_name = self.cleaned_data.get('user_name')
        if user_name:
            try:
                User.objects.get(user_name=user_name)
                raise forms.ValidationError(
                    'This username has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return user_name

class CustomUserCreationForm(UserCreationForm):
    """
    Form for user creation from admin panel
    """
    class Meta:
        model = User
        fields = ('email',)
        field_classes = {'email': forms.EmailField}

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            try:
                User.objects.get(email=email.lower())
                raise forms.ValidationError(
                    'This email has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return email


def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            try:
                User.objects.get(email=email.lower())
                pass
            except User.DoesNotExist:
                raise forms.ValidationError(
                    'This email has not been registered.'
                )
        return email

PasswordResetForm.clean_email = clean_email

# Phone Password Reset Form
class PhonePasswordResetForm(forms.Form):
    phone = PhoneNumberField()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            try:
                User.objects.get(userprofile__phone_number=phone)
                pass
            except User.DoesNotExist:
                raise forms.ValidationError(
                    'This phone has not been registered.'
                )
        return phone

    def save(self,use_https=False, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        phone = self.cleaned_data["phone"]
        try:
            user = User.objects.get(userprofile__phone_number=phone, is_active=True)
            # phone = str(
            #     UserProfile.objects.get(user=user).phone_number
            # )
            phone = '+41797752819'
            device = user.twiliosmsdevice_set.get()
            token = device.generate_challenge()

            data = {'phone': phone}
            if settings.DEBUG or 'test' in sys.argv:
                data.update({'token': token})
            return Response(data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            raise forms.ValidationError(
                'This phone number has not been registered.'
            )

# OTP Validation Form
class OtpValidationForm(forms.Form):
    phone = PhoneNumberField()
    otp = forms.IntegerField(label=_("OTP"))

    error_messages = {
        'otp': _("Invalid OTP."),
    }

    def clean(self):
        cleaned_data = self.cleaned_data
        phone = self.cleaned_data["phone"]
        otp = self.cleaned_data["otp"]
        user = User.objects.get(userprofile__phone_number=phone)
        device = user.twiliosmsdevice_set.get()
        if device:
            status = device.verify_token(otp)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            if status:
                data = {
                    'uidb64': uidb64.decode('utf-8'),
                    'token': default_token_generator.make_token(user),
                }
                return Response(data)
            else:
                self._errors["otp"] = self.error_class([self.error_messages['otp']])
                del cleaned_data["otp"]
        return cleaned_data

    def save(self,use_https=False, request=None):
        user = User.objects.get(userprofile__phone_number=request.POST['phone'])
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        data = {
            'uidb64': uidb64.decode('utf-8'),
            'token': default_token_generator.make_token(user),
        }
        return Response(data)

# Username Reset Form
class UsernamePasswordResetForm(forms.Form):
    user_name = forms.CharField(label=_("Username"), widget=forms.TextInput(attrs={'autofocus': True}), max_length=500,validators=[MinLengthValidator(5)])

    def clean_user_name(self):
        user_name = self.cleaned_data.get('user_name')
        if user_name:
            try:
                User.objects.get(user_name=user_name)
                pass
            except User.DoesNotExist:
                raise forms.ValidationError(
                    'This username has not been registered.'
                )
        return user_name

    def save(self,use_https=False, request=None):
        user_name = self.cleaned_data["user_name"]
        try:
            users = User.objects.get(user_name=user_name)
            security_question = SecurityQuestion.objects.filter(id=users.security_question.pk).values_list('pk','title','question_type').first()
            if users.security_question.question_type != 'text':
                vals_ids = SecurityQuestion.objects.filter(id=users.security_question.pk).values_list('vals', flat=True)
                vals = [KeyVal.objects.filter(id=v).values_list('key','value').first() for v in vals_ids]
                values = [{'key':v[0], 'value':v[1]} for v in vals]
                data = {
                    'security_question': security_question,
                    'vals': values,
                }
            else:
                data = {
                    'security_question': security_question
                }
            return Response(data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            raise forms.ValidationError(
                'This username has not been registered.'
            )

# Security Question and Answer Validation Form
class SecurityQuestionForm(forms.Form):
    user_name = forms.CharField(label=_("Username"), widget=forms.TextInput(attrs={'autofocus': True}), max_length=500,validators=[MinLengthValidator(5)])
    security_question = forms.ModelChoiceField(queryset=SecurityQuestion.objects.all(),label=_('Security Question:'))
    answer = forms.CharField(label=_("Answer"),max_length=500)

    error_messages = {
        'answer': _("Answer is wrong."),
    }

    def str_to_list(self,answer):
        list1 = []
        l1 = answer.strip("[]").split(", ")
        list1 = [i.strip("''")for i in l1]
        return list1

    
    def clean(self):
        cleaned_data = self.cleaned_data
        user_name = self.cleaned_data["user_name"]
        security_question = self.cleaned_data["security_question"]
        answer = self.cleaned_data["answer"]       
        user = User.objects.get(user_name=user_name)
        
        if user:
            answer_obj = Answer.objects.get(user=user.id)
            if user.security_question.question_type == 'text':
                if answer_obj.response_text == answer:
                    pass
                else:
                    self._errors["answer"] = self.error_class([self.error_messages['answer']])
                    del cleaned_data["answer"]
            else:
                original_answer = self.str_to_list(answer_obj.response_text)
                new_answer = self.str_to_list(answer)
                if set(original_answer) == set(new_answer):
                    pass
                else:
                    self._errors["answer"] = self.error_class([self.error_messages['answer']])
                    del cleaned_data["answer"]
        return cleaned_data

    def save(self,use_https=False, request=None):
        user = User.objects.get(user_name=request.POST['user_name'])
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        data = {
            'uidb64': uidb64.decode('utf-8'),
            'token': default_token_generator.make_token(user),
        }
        return Response(data)
