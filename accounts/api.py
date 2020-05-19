from datetime import datetime
import sys

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import (
    jwt_payload_handler, jwt_encode_handler
)
from rest_framework_jwt.views import (
    JSONWebTokenAPIView, ObtainJSONWebToken, jwt_response_payload_handler
)

from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework_social_oauth2.authentication import SocialAuthentication

from .models import (
    User, UserProfile, SecurityQuestion, Answer, EmployeeBasicDetails, EmployeeProfessionalDetails,
    EmployeeEmploymentDetails, EmployeeWorkDetails, EmployeeAvailability, Resume, BankAccounts, TestClass
)
from .forms import UserProfileCreationForm, UserNameCreationForm

from rest_framework.views import APIView

from django.utils.crypto import get_random_string

from rest_framework import filters 
import django_filters.rest_framework
from django.core.paginator import Paginator
from rest_framework import pagination
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.db.models import Q

from .serializers import (
    AuthLazyUserTokenSerializer,
    AuthLazyUserConvertSerializer,
    EmailPhoneJSONWebTokenSerializer,
    SocialJSONWebTokenSerializer,
    CreateUserSerializer,
    UserProfileSerializer,
    UserProfileShortDataSerializer,
    SecurityQuestionSerializer,
    SecurityAnswerSerializer,
    SocialMediaSerializer,
    EmployeeBasicDetailSerializer,
    EmployeeProfessionalDetailSerializer,
    EmployeeEmploymentDetailSerializer,
    EmployeeWorkDetailSerializer,
    EmployeeAvailabilitySerializer,
    ResumeSerializer,
    EmployeeDetailSerializer,
    BankAccountsSerializer,
    TestClassSerializer,
)

from lazysignup.models import LazyUser
from lazysignup.exceptions import NotLazyError
from rest_framework import serializers
from rest_framework import viewsets
import random
from rest_framework.decorators import list_route, detail_route
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.http import HttpResponseBadRequest
from django.http import QueryDict, HttpResponse
from django.db.models import Q

from common.models import (
    University, Campus, 
)
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import views
import mimetypes
from django.core.files.storage import default_storage
from twilio.rest import Client
from core.utils import convert_file_to_base64
from rest_framework.parsers import FormParser, MultiPartParser

class RegistrationView(generics.CreateAPIView):
    """
    Registration by email
    """

    model = get_user_model()
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]


class OtpLoginView(generics.CreateAPIView):
    """
    Login / registration by phone
    """
    model = get_user_model()
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        created = True
        try:
            user = User.objects.get(
                userprofile__phone_number=request.data.get('phone')
            )

            created = False

            if user and user.is_auth:
                qdict = QueryDict('', mutable=True)
                qdict.update(request.data)
                user_profile_form = UserProfileCreationForm
                form = user_profile_form(data=qdict)
                return HttpResponseBadRequest(content=str(form.errors.as_json()))

        except User.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            user = serializer.instance

        # FIXME: we use free version of twilio and can send sms only for verified numbers
        # The number +380937691185 is unverified. Trial accounts cannot send messages to unverified numbers; verify +380937691185 at twilio.com/user/account/phone-numbers/verified, or purchase a Twilio number to send messages to unverified numbers.
        # phone = str(
        #     UserProfile.objects.get(user=user).phone_number
        # )
        phone = '+41797752819'
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        if created:
            user.twiliosmsdevice_set.create(
                name='SMS', number=phone
            )
        
        device = user.twiliosmsdevice_set.get()
        token = device.generate_challenge()
        client.api.account.messages.create(
                to=phone,
                from_=settings.OTP_TWILIO_FROM,
                body=token)

        data = {'phone': phone}
        if settings.DEBUG or 'test' in sys.argv:
            data.update({'token': token})
        return Response(data, status=status.HTTP_201_CREATED)

class UsernameRegistrationView(generics.CreateAPIView):
    """
    Registration by Username
    """
    model = get_user_model()
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny] 

    def create(self, request, *args, **kwargs):
        created = True
        try:
            user = User.objects.get(
                user_name=request.data.get('user_name')
            )
            created = False
            qdict = QueryDict('', mutable=True)
            qdict.update(request.data)
            user_profile_form = UserNameCreationForm
            form = user_profile_form(data=qdict)
            return HttpResponseBadRequest(content=str(form.errors.as_json()))
        except User.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            user = serializer.instance
        data = {'security_question': request.data.get('security_question'),'response_text':request.data.get('answer'),'user': user}
        if created:
            SecurityAnswerSerializer.create(SecurityAnswerSerializer(), validated_data=data)
        return Response(data,status=status.HTTP_201_CREATED)


class SecurityQuestionViewSet(generics.RetrieveUpdateAPIView):
    """
        Endpoint security questions
    """

    serializer_class = SecurityQuestionSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        queryset =  SecurityQuestion.objects.values_list('id', flat=True)
        secure_random = random.SystemRandom()
        question_obj = SecurityQuestion.objects.get(id=secure_random.choice(list(queryset)))
        return question_obj


class AuthLazyUserTokenView(JSONWebTokenAPIView):

    """
    Endpoint for lazy user token
    """
    serializer_class = AuthLazyUserTokenSerializer

    def get(self, request, *args, **kwargs):

        return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs):

        # Monkey patch - application haven't settings for username field
        LazyUser.objects.username_field = 'email'
        user, username = LazyUser.objects.create_lazy_user()
        lazy_password = random.SystemRandom().randint(100000,999999)
        user.set_password(lazy_password)
        user.save(update_fields=['password'])
        UserProfile.objects.filter(user_id=user.id).update(temp_password=lazy_password)
        User.objects.filter(email=username).update(user_name=username,is_tempuser=True)
        User.objects.filter(email=username).update(email='')


        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response_data = jwt_response_payload_handler(token, user, request)
        response = Response(response_data)
        
        if api_settings.JWT_AUTH_COOKIE:
            expiration = (datetime.utcnow() +
                          api_settings.JWT_EXPIRATION_DELTA)
            response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                token, 
                                expires=expiration,
                                httponly=True)

        return response
       


class AuthLazyUserConvertView(generics.CreateAPIView):
    """
    Convert a temporary user to a real one. Reject users who don't
        appear to be temporary users (ie. they have a usable password)
    """
    serializer_class = AuthLazyUserConvertSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # If we've got an anonymous user, raise him
        if request.user.is_anonymous():
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            serializer.instance = request.user
            LazyUser.objects.convert(serializer)
        except NotLazyError:
            # If the user already has a usable password, return a Bad request
            return Response(status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class EmailPhoneObtainJSONWebToken(ObtainJSONWebToken):
    """
    ObtainJSONWebToken verify user by USERNAME_FIELD. We need add phone
    """
    serializer_class = EmailPhoneJSONWebTokenSerializer


class SocialObtainJSONWebToken(JSONWebTokenAPIView):
    """
    Login / registration by social media
    """
    serializer_class = SocialJSONWebTokenSerializer
    # permission_classes = [IsAuthenticated]
    # #TODO: move oauth classes to settings
    # authentication_classes = (
    #     OAuth2Authentication,
    #     SocialAuthentication,
    # )
    # def create(self, request, *args, **kwargs):

    #     created = True
    #     try:
    #         user = User.objects.get(email=request.data.get('email'))
    #         token, created = Token.objects.get_or_create(user=user)

    #     except User.DoesNotExist:
    #         serializer = self.get_serializer(data=request.data)
    #         serializer.is_valid(raise_exception=True)
    #         self.perform_create(serializer)
    #         headers = self.get_success_headers(serializer.data)
    #         token, created = Token.objects.get_or_create(user=serializer.instance) 
 
    #     return Response({'token': token.key}, status=status.HTTP_201_CREATED)

    def post(self, request, *args, **kwargs):
        user = ''
        if request.data.get('email'):
            user = User.objects.get(email=request.data.get('email'))

        elif request.data.get('user_name'):
            user = User.objects.get(user_name=request.data.get('user_name'))

        elif request.data.get('phone'):
            user = UserProfile.objects.get(phone_number=request.data.get('phone'))


        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response_data = jwt_response_payload_handler(token, user, request)
        response = Response(response_data)

        return response
    

class CurrentUserProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for current user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)


class CurrentUserEmployeesListView(generics.ListAPIView):
    """
    Endpoint for current user employees list
    """
    serializer_class = UserProfileShortDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(
            user__employers=self.request.user.userprofile
        )

class CurrentUserCreatorsListView(generics.ListAPIView):
    """
    Endpoint for current user creator list
    """
    serializer_class = UserProfileShortDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(
            Q(user=self.request.user) |
            Q(role="creator")
        ).distinct()

class SocialMediaUserView(generics.CreateAPIView):
    """
    Login / registration by social media
    """
    model = get_user_model()
    serializer_class = SocialMediaSerializer
    permission_classes = [AllowAny]

class EmployeeBasicDetailsView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for employee basic details
    """
    serializer_class = EmployeeBasicDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return EmployeeBasicDetails.objects.get(userprofile=self.request.user.userprofile.id)

class ResumeView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for employee resume
    """
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Resume.objects.get(userprofile=self.request.user.userprofile.id)


class EmployeeProfessionalDetailsView(viewsets.ModelViewSet):
    """
    Endpoint for employee professional details
    """
    serializer_class = EmployeeProfessionalDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmployeeProfessionalDetails.objects.filter(
            userprofile=self.request.user.userprofile.id
        )

    def perform_create(self, serializer):
        serializer.save(userprofile=self.request.user.userprofile)

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def create_university(self, university):
        try:
            university_obj = University.objects.get(title=university)
        except University.DoesNotExist:
            university_obj = University(
                title=university,
            )
            university_obj.save(force_insert=True)

        return university_obj

    def create_campus(self, campus, university):
        try:
            campus_obj = Campus.objects.get(title=campus, university__id = university.id)
        except Campus.DoesNotExist:
            campus_obj = Campus(
                title=campus,
                university=university
            )
            campus_obj.save(force_insert=True)

        return campus_obj

    def create(self, request, *args, **kwargs):
        if not dict(request.POST.lists()):
            for data in request.data:
                created = False
                try:
                    employee_professional_id = EmployeeProfessionalDetails.objects.get(
                        id=data.get('id')
                    )
                    created = True

                except EmployeeProfessionalDetails.DoesNotExist:
                    serializer = self.get_serializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    employee_professional_id = serializer.instance
                    if data.get('present'):
                        employee_professional_id.to_date = None
                        employee_professional_id.save()

                    if data.get('other_university'):
                        university = self.create_university(data.get('other_university'))
                        employee_professional_id.university = university
                        employee_professional_id.other_university = ''
                        employee_professional_id.save()

                    if data.get('other_campus'):
                        campus = self.create_campus(data.get('other_campus'), employee_professional_id.university)
                        other_campus = Campus.objects.get(title__icontains='other')
                        employee_professional_id.campus.remove(other_campus)
                        employee_professional_id.campus.add(campus)
                        employee_professional_id.other_campus = ''
                        employee_professional_id.save()

                if created:
                    if data.get('present'):
                        employee_professional_id.to_date = None
                        employee_professional_id.save()
                    
                    serializer = self.serializer_class(employee_professional_id, data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    employee_professional_id = serializer.instance

                    if data.get('other_university'):
                        university = self.create_university(data.get('other_university'))
                        employee_professional_id.university = university
                        employee_professional_id.other_university = ''
                        employee_professional_id.save()

                    if data.get('other_campus'):
                        campus = self.create_campus(data.get('other_campus'), employee_professional_id.university)
                        other_campus = Campus.objects.get(title__icontains='other')
                        employee_professional_id.campus.remove(other_campus)
                        employee_professional_id.campus.add(campus)
                        employee_professional_id.other_campus = ''
                        employee_professional_id.save()
        else:
            try:
                employee_professional_id = EmployeeProfessionalDetails.objects.get(
                    id=request.data.get('id')
                )
            except EmployeeProfessionalDetails.DoesNotExist:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                employee_professional_id = serializer.instance
                if request.data.get('other_university'):
                        university = self.create_university(request.data.get('other_university'))
                        employee_professional_id.university = university
                        employee_professional_id.other_university = ''
                        employee_professional_id.save()

                if request.data.get('other_campus'):
                        campus = self.create_campus(request.data.get('other_campus'), employee_professional_id.university)
                        other_campus = Campus.objects.get(title__icontains='other')
                        employee_professional_id.campus.remove(other_campus)
                        employee_professional_id.campus.add(campus)
                        employee_professional_id.other_campus = ''
                        employee_professional_id.save()


        return Response("created", status=status.HTTP_201_CREATED)


class EmployeeEmploymentDetailsView(viewsets.ModelViewSet):
    """
    Endpoint for employee employment details
    """
    serializer_class = EmployeeEmploymentDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmployeeEmploymentDetails.objects.filter(
            userprofile=self.request.user.userprofile.id
        )

    def perform_create(self, serializer):
        serializer.save(userprofile=self.request.user.userprofile)

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not dict(request.POST.lists()):
            for data in request.data:
                created = False
                try:
                    employee_employment_id = EmployeeEmploymentDetails.objects.get(
                        id=data.get('id')
                    )
                    created = True

                except EmployeeEmploymentDetails.DoesNotExist:
                    serializer = self.get_serializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    employee_employment_id = serializer.instance
                    if data.get('present'):
                        employee_employment_id.date_end = None
                        employee_employment_id.save()

                if created:
                    if data.get('present'):
                        employee_employment_id.date_end = None
                        employee_employment_id.save()
                        
                    serializer = self.serializer_class(employee_employment_id, data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
        else:
            try:
                employee_employment_id = EmployeeEmploymentDetails.objects.get(
                    id=request.data.get('id')
                )
            except EmployeeEmploymentDetails.DoesNotExist:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                employee_employment_id = serializer.instance

        return Response("created", status=status.HTTP_201_CREATED)


class EmployeeWorkDetailsView(viewsets.ModelViewSet):
    """
    Endpoint for employee employment details
    """
    serializer_class = EmployeeWorkDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmployeeWorkDetails.objects.filter(
            userprofile=self.request.user.userprofile.id
        )

    def perform_create(self, serializer):
        serializer.save(userprofile=self.request.user.userprofile)

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not dict(request.POST.lists()):
            for data in request.data:
                created = False
                try:
                    employee_work_id = EmployeeWorkDetails.objects.get(
                        id=data.get('id')
                    )
                    created = True

                except EmployeeWorkDetails.DoesNotExist:
                    serializer = self.get_serializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    employee_work_id = serializer.instance

                if created:
                    serializer = self.serializer_class(employee_work_id, data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
        else:
            try:
                employee_work_id = EmployeeWorkDetails.objects.get(
                    id=request.data.get('id')
                )
            except EmployeeWorkDetails.DoesNotExist:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                employee_work_id = serializer.instance

        return Response("created", status=status.HTTP_201_CREATED)

class EmployeeAvailabilityView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for employee availability
    """
    serializer_class = EmployeeAvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return EmployeeAvailability.objects.get(userprofile=self.request.user.userprofile.id)

class EmployeeProfileViewSet(viewsets.ModelViewSet):
    """
    Endpoint for current user profile
    """
    serializer_class = EmployeeDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(
            Q(user=self.request.user) |
            Q(role="employee")
        ).distinct()

class ResumeDownloadView(viewsets.ModelViewSet):
    """
    Endpoint for Resume user profile
    """
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head']

    @detail_route(url_name='download')
    def download(self, request, pk=None):
        resume_obj = Resume.objects.get(id=pk)
        if resume_obj.resume:
            srcFileName = resume_obj.resume.name

            file = default_storage.open(srcFileName, 'rb')
            f = convert_file_to_base64(file)
            file_mimetype = mimetypes.guess_type(srcFileName)
            response = HttpResponse(f, content_type=file_mimetype)
            response['content-disposition'] = 'attachment; filename=' + resume_obj.file_name
            return response
        else:
            return Response("Resume is not uploaded")

class BankAccountsViewSet(viewsets.ModelViewSet):
    """
    Endpoint for Bank Account Details
    """
    serializer_class = BankAccountsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BankAccounts.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

class TestClassViewSet(viewsets.ModelViewSet):
    """
    Endpoint for Transaction Details of Bank Accounts
    """
    serializer_class = TestClassSerializer
    permission_classes = [AllowAny]
    parser_classes = (FormParser, MultiPartParser)

    def get_queryset(self):
        return TestClass.objects.all()