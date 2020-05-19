from .models import (
    User, UserProfile,
    Education,
    WorkExperience,
    Specialization,
    SecurityQuestion,
    Answer,
    KeyVal,
    EmployeeBasicDetails,
    EmployeeProfessionalDetails,
    EmployeeEmploymentDetails,
    EmployeeWorkDetails,
    EmployeeAvailability,
    Resume,
    BankAccounts,
    TestClass
)
from .mixins import UserCheckEmailPhoneApiMixin , UserCheckIdproofApiMixin , UserCheckProviderSocialMediaApiMixin
from .constants import ROLES
from core.serializers import Base64ImageField, Base64FileField
from google_places.models import google_places, Place

from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.compat import get_username_field, Serializer

from phonenumber_field.serializerfields import PhoneNumberField
from fcm_django.models import FCMDevice
from rest_framework.validators import UniqueValidator
from django.core.validators import MinLengthValidator

from common.models import (
    Expertise, Experience, HourlyBudget, HighestQualification, Role, Bank
)
from common.serializers import HighestQualificationSerializer,ProgramsSerializer, RoleSerializer, BankSerializer

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
from datetime import datetime, date
from django.core.validators import RegexValidator
from django.db.models import Q
import json
from djmoney.money import Money
from rest_framework.reverse import reverse
from boto.s3.connection import S3Connection
from saffron_backend.settings import *
from django.core.files.storage import default_storage
import urllib
from rest_framework.response import Response
#Temporary Comment changes related to Dowlla Payment
from projects.task import create_customer

alphaSpaces = RegexValidator(r"^[a-zA-Z0-9.,']+$", 'Only alphanumerics are allowed.')

class MoneyField(serializers.Field):
    default_error_messages = {
        'positive_only': 'The amount must be positive.',
        'not_a_number': 'The amount must be a number.'
    }

    def __init__(self, *args, **kwargs):
        super(MoneyField, self).__init__(*args, **kwargs)
        self.positive_only = kwargs.get('positive_only', True)

    def to_representation(self, obj):
        data = {'amount': float(obj.amount),
            'currency': str(obj.currency),}
        return data

    def to_internal_value(self, data):
        data = json.loads(data)

        amount = data.get('amount')
        currency = data.get('currency')

        try:
            obj = Money(amount, currency)
        except decimal.InvalidOperation:
            self.fail('not_a_number')

        if obj < Money('0', currency) and self.positive_only:
            self.fail('positive_only')
        return obj

class EmailPhoneJSONWebTokenSerializer(JSONWebTokenSerializer):
    """
    Auth field for login can be email or phone or username.
    We need check which field in data and use it
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'email' in self.initial_data:
            self.initial_data['email'] = self.initial_data['email'].lower()
        elif 'phone' in self.initial_data:
            del self.fields[self.username_field]
            self.fields['phone'] = serializers.CharField()
        elif 'user_name' in self.initial_data:
            del self.fields[self.username_field]
            self.fields['user_name'] = serializers.CharField()

    @property
    def username_field(self):
        """
        Username field can be email or phone or username
        """

        if 'phone' in self.initial_data:
            return 'phone'
        if 'user_name' in self.initial_data:
            return 'user_name'
        return get_username_field()


class SocialJSONWebTokenSerializer(serializers.Serializer):
    pass

    # def validate(self, attrs):
    #     request = self.context['request']
    #     #print("aaaaaaaaaaaaaa",request.user)

    #     if request.user:
    #         if not request.user.is_active:
    #             msg = 'User account is disabled.'
    #             raise serializers.ValidationError(msg)

    #         payload = jwt_payload_handler(request.user)

    #         return {
    #             'token': jwt_encode_handler(payload),
    #             'user': request.user
    #         }
    #     else:
    #         msg = 'Unable to log in with provided credentials.'
    #         raise serializers.ValidationError(msg)




class EducationSerializer(serializers.ModelSerializer):
    """
    Serializer for employee educations
    """
    class Meta:
        model = Education
        fields = ('date_start', 'date_end', 'degree', 'school')


class WorkExperienceSerializer(serializers.ModelSerializer):
    """
    Serializer for employee work experience
    """
    class Meta:
        model = WorkExperience
        fields = ('date_start', 'date_end', 'company', 'position',
                  'description')

class EmployeeEmploymentDetailSerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField()
    functional_areas_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    departments_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeEmploymentDetails
        fields = ('id', 'present', 'current_employer', 'date_start', 'date_end','duration','current_designation', 'functional_areas','functional_areas_name','role','role_name', 'departments','departments_name','job_role','userprofile_id','is_completed')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('current_employer'):
            raise serializers.ValidationError('Please set employer')
        if not attrs.get('date_start'):
            raise serializers.ValidationError('Please set start date')
        if not attrs.get('date_end') and attrs.get('present') == False:
            raise serializers.ValidationError('Please set end date')
        if attrs.get('date_start') and attrs.get('date_end'):
            if attrs.get('date_start') >= attrs.get('date_end'):
                raise serializers.ValidationError('Please select start date less than end date')
        return attrs

    def get_functional_areas_name(self, obj):
        if obj.functional_areas:
            functional_areas = [i.title for i in obj.functional_areas.all()]
            return functional_areas

    def get_role_name(self, obj):
        if obj.role:
            role = [i.title for i in obj.role.all()]
            return role

    def get_departments_name(self, obj):
        if obj.departments:
            departments = [i.title for i in obj.departments.all()]
            return departments

    def get_duration(self, obj):
        if obj.date_start and obj.date_end:
            return str(obj.date_start.year) + '-' + str(obj.date_end.year)
        elif obj.date_start and obj.present:
            return str(obj.date_start.year) + '-' + 'Present'


class EmployeeWorkDetailSerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField(allow_null=True,)
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), required=False, many=True
    )

    class Meta:
        model = EmployeeWorkDetails
        fields = ('id', 'client', 'project_title', 'from_date', 'to_date', 'project_location', 'role','employment_type','project_details', 'role_description', 'team_size', 'skill_used', 'userprofile_id','is_completed')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('client'):
            raise serializers.ValidationError('Please set client')
        if not attrs.get('project_title'):
            raise serializers.ValidationError('Please set project title')
        if not attrs.get('from_date'):
            raise serializers.ValidationError('Please set from date')
        if not attrs.get('to_date'):
            raise serializers.ValidationError('Please set to date')
        if not attrs.get('project_details'):
            raise serializers.ValidationError('Please set project details')
        if not attrs.get('role'):
            raise serializers.ValidationError('Please set role')
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()

    """
    Email and phone are not required.
    We need check if they are are unique
    """
    email = serializers.EmailField(source='user.email', required=False, allow_null=True, allow_blank=True) #validators=[UniqueValidator(queryset=User.objects.all())]
    phone_number = PhoneNumberField(required=False, allow_null=True, allow_blank=True,validators=[UniqueValidator(queryset=UserProfile.objects.all())])
    user_name = serializers.CharField(source='user.user_name', required=False, allow_null=True, allow_blank=True,)#validators=[UniqueValidator(queryset=User.objects.all())]


    specializations = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.all(), required=False, many=True
    )
    skills = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.all(), required=False, many=True
    )
    educations = EducationSerializer(required=False, many=True)
    works = WorkExperienceSerializer(required=False, many=True)
    address = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    photo = Base64ImageField(required=False, allow_null=True)
    photo_crop = serializers.CharField(source='get_photo_crop', read_only=True)
    photo_bounds = serializers.JSONField(required=False, allow_null=True)
    passport_photo = Base64ImageField(required=False, allow_null=True)
    driver_license_photo = Base64ImageField(required=False, allow_null=True)
    role = serializers.ChoiceField(choices=ROLES, required=False)
    employees = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, many=True
    )

    class Meta:
        model = UserProfile
        fields = ('id', 'first_name', 'last_name', 'phone_number', 'user_name', 'address',
                  'photo', 'photo_crop', 'photo_bounds', 'passport_photo',
                  'driver_license_photo', 'role', 'user_id', 'phone_number',
                  'email', 'title', 'summary', 'specializations', 'skills',
                  'educations', 'works', 'employees','user_name','temp_password','zip','ssn')
        depth = 1

    def get_user_id(self, obj):
        return obj.user.pk

    def validate_address(self, value):
        """
        Try validate address using google places API and save object
        """
        # It seems we want delete address
        if not value:
            return None


        results = google_places.text_search(query=value)

        # We use google places autocomplite but we need recheck data
        # (we do not believe the data from frontend) and get first result
        if len(results.places) > 0:
            p = results.places[0]
            try:
                place = Place.objects.get(api_id=p.id)
            except Place.DoesNotExist:
                place = Place()
                place.populate_from_api(p)
            return place
        raise serializers.ValidationError('Please enter correct address')

    def update(self, instance, validated_data):
        educations_data = validated_data.pop('educations', None)
        works_data = validated_data.pop('works', None)

        email_data = None
        username_data = None
        is_tempuser = None

        if 'user' in validated_data:
            user = validated_data.pop('user')
            username_data = user.pop('user_name', None)
            email_data = user.pop('email', None)
            is_tempuser = user.pop('is_tempuser', False)

        instance = super().update(instance, validated_data)
        if educations_data is not None:
            s = EducationSerializer(data=educations_data, many=True)
            s.is_valid(raise_exception=True)
            s.save(userprofile=instance)

        if works_data is not None:
            s = WorkExperienceSerializer(data=works_data, many=True)
            s.is_valid(raise_exception=True)
            s.save(userprofile=instance)

        if email_data is not None:
            email_obj =User.objects.filter(~Q(email=''),~Q(id=instance.user.id),email = email_data).values_list('id', flat=True)
            if email_obj.exists():
                raise serializers.ValidationError({"email": "This email is already existing."})
            else:
                instance.user.email = email_data.lower()
                instance.user.save()


        if username_data is not None:
            user_id =User.objects.filter(~Q(user_name=''),~Q(id=instance.user.id),user_name = username_data).values_list('id', flat=True)
            if user_id.exists():
                raise serializers.ValidationError({"user_name": "This username is already existing."})
            else:
                instance.user.user_name = username_data
                instance.user.save()

        if is_tempuser is not None:
            instance.user.is_tempuser = False
            instance.temp_password = None
            instance.save()
            instance.user.save()

        if validated_data.get('role')=='employee':
            EmployeeBasicDetails.objects.get_or_create(userprofile=instance)
            EmployeeAvailability.objects.get_or_create(userprofile=instance)
            Resume.objects.get_or_create(userprofile=instance)

        # send push notification
        devices = FCMDevice.objects.filter(
            user=instance.user, active=True
        )
        devices.send_message(
            title='Profile', body='You successfully updated your profile'
        )

        return instance

class SecurityAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for Security Quetions answers
    """
    user = serializers.ReadOnlyField(source='user_id')
    keyval = KeyVal()

    class Meta:
        model = Answer
        fields = ('security_question', 'user', 'response_text', 'vals')

    def create(self, validated_data):
        question_obj = SecurityQuestion.objects.get(id=validated_data.pop('security_question'))
        answer, created = Answer.objects.update_or_create(
            security_question=question_obj,
            response_text=validated_data.pop('response_text'),
            user=validated_data.pop('user')
        )

        return answer

class CreateUserSerializer(
    UserCheckEmailPhoneApiMixin,
    serializers.ModelSerializer
):

    """
    Email and phone are not required.
    We need check if they are set and they are unique
    """
    phone = PhoneNumberField(required=False)
    user_name = serializers.CharField(required=False, max_length=20, allow_null=True, allow_blank=True, validators=[MinLengthValidator(5)])


    class Meta:
        model = User
        fields = ('email', 'phone','user_name', 'security_question', 'password')
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('password'):
            raise serializers.ValidationError('Please set password')
        if attrs.get('user_name') and not attrs.get('security_question'):
            raise serializers.ValidationError('Please select security question')
        return attrs

    def create(self, validated_data):
        if validated_data.get('is_superuser') is True:
            return User.objects.create_superuser(**validated_data)
        if validated_data.get('email'):
            validated_data['email']=validated_data['email'].lower()
        return User.objects.create_user(**validated_data)


class AuthLazyUserConvertSerializer(serializers.ModelSerializer):
    """
    Serializer for lazy users convert
    """
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ('email', 'password')


class AuthLazyUserTokenSerializer(serializers.Serializer):
    """
    Empty serializer for AuthLazyUserTokenViewSet. We don't need send any data
    """
    pass


class CurrentUserRolesSerializer(serializers.Serializer):
    """
    Serializer for current user roles
    """
    name = serializers.CharField()
    key = serializers.CharField()
    is_primary = serializers.BooleanField()

class UserProfileShortDataSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile published information
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    # photo_crop = serializers.CharField(source='get_photo_crop', read_only=True)
    photo_crop = serializers.SerializerMethodField()
    address = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    user_id = serializers.IntegerField(source='user.pk', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number',
                  'photo_crop', 'user_id','address')
        depth = 1

    def get_photo_crop(self, instance):
        url = ""
        if instance.photo.name:
            conn = S3Connection(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,host=AWS_HOST)
            #connecting to aws with specific endpoint reason
            bucket = conn.get_bucket(AWS_S3_BUCKET_NAME)
            #getting bucket from AWS
            key = bucket.get_key(instance.photo.name, validate=True)
            if key:
                url = key.generate_url(900)
        return "{}".format(url)

    # def get_address(self, instance):
    #     print("aaaaaaaaaaaaaaaaaa",instance)
    #     #google_address = Place.objects.get(id =user_obj.userprofile.address)
    #     #user_address = google_address.formatted_address

class KeyValSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyVal
        fields = ('key', 'value')

class SocialMediaSerializer(serializers.ModelSerializer):
    provider = serializers.CharField(required=False)
    id = serializers.CharField(required=True, allow_null=True)
    email = serializers.EmailField(required=False)
    phone = PhoneNumberField(required=False)
    name = serializers.CharField(required=False)
    #photoUrl = serializers.CharField(required=False, allow_null=False)

    class Meta:
        model = User
        fields = ('email','phone','provider','id','name')

    def validate(self, attrs):
        if not attrs.get('name'):
            raise serializers.ValidationError('Please set name')
        if not attrs.get('provider'):
            raise serializers.ValidationError('Please set provider')
        if not attrs.get('id'):
            raise serializers.ValidationError('Please set provider Id')
        if not attrs.get('email') or attrs.get('phone'):
            raise serializers.ValidationError('Please set either email or phone')
        return attrs

    def create(self,validated_data):
        return User.objects.create_user(**validated_data)

class SecurityQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Security Quetions information
    """
    vals = KeyValSerializer(required=False, many=True)

    class Meta:
        model = SecurityQuestion
        fields = ('id', 'order', 'title', 'question_type','vals', 'is_active')

class EmployeeBasicDetailSerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField()

    first_name = serializers.CharField(source='userprofile.first_name', required=False, allow_null=True, allow_blank=True, validators=[alphaSpaces])
    last_name = serializers.CharField(source='userprofile.last_name', required=False, allow_null=True, allow_blank=True, validators=[alphaSpaces])
    photo = Base64ImageField(source='userprofile.photo', required=False, allow_null=True)
    photo_crop = serializers.CharField(source='userprofile.get_photo_crop', read_only=True)
    photo_bounds = serializers.JSONField(source='userprofile.photo_bounds', required=False, allow_null=True)
    email = serializers.EmailField(source='userprofile.user.email', required=False, allow_null=True, allow_blank=True)


    class Meta:
        model = EmployeeBasicDetails
        fields = ('id', 'first_name', 'last_name','photo', 'photo_crop', 'photo_bounds',
                'date_of_birth', 'gender','marital_status','employee_status','hobbies', 'address_line1',
                'address_line2', 'city', 'state', 'country', 'pin_code', 'contact_details', 'alternate_contact_details',
                'userprofile_id', 'is_completed','total_experience','email')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk


    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('userprofile'):
            userprofile = attrs.get('userprofile')
            if not userprofile.get('first_name'):
                raise serializers.ValidationError('Please set first name')
            if not userprofile.get('last_name'):
                raise serializers.ValidationError('Please set last name')
            if not userprofile.get('user').get('email'):
                raise serializers.ValidationError('Please set email')

        if not attrs.get('date_of_birth'):
            raise serializers.ValidationError('Please set date of birth')
        if not attrs.get('gender'):
            raise serializers.ValidationError('Please set gender')
        if not attrs.get('marital_status'):
            raise serializers.ValidationError('Please set marital status')
        if not attrs.get('total_experience'):
            raise serializers.ValidationError('Please select total experience')
        if not attrs.get('total_experience'):
            raise serializers.ValidationError('Please select total experience')
        return attrs

    def update(self, instance, validated_data):

        if 'userprofile' in validated_data:
            userprofile = validated_data.pop('userprofile')
            user = userprofile.pop('user', None)
            email = user.pop('email')
            first_name = userprofile.pop('first_name', None)
            last_name = userprofile.pop('last_name', None)
            photo = userprofile.pop('photo', None)
            photo_crop = userprofile.pop('photo_crop', None)
            photo_bounds = userprofile.pop('photo_bounds', None)

        instance = super().update(instance, validated_data)

        if first_name is not None:
            instance.userprofile.first_name = first_name
            instance.userprofile.save()
        if last_name is not None:
            instance.userprofile.last_name = last_name
            instance.userprofile.save()
        if photo is not None:
            instance.userprofile.photo = photo
            instance.userprofile.save()
        if photo_crop is not None:
            instance.userprofile.photo_crop = photo_crop
            instance.userprofile.save()
        if photo_bounds is not None:
            instance.userprofile.photo_bounds = photo_bounds
            instance.userprofile.save()

        if email is not None:
            instance.userprofile.user.email = email
            instance.userprofile.user.save()

        return instance

class EmployeeProfessionalDetailSerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField()
    highest_qualification_name = serializers.SerializerMethodField()
    programs_name = serializers.SerializerMethodField()
    university_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfessionalDetails
        fields = ('id', 'highest_qualification','highest_qualification_name', 'programs','programs_name', 'university', 'university_name', 'other_university', 'campus', 'other_campus', 'from_date', 'to_date', 'duration', 'present', 'userprofile_id','is_completed')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk



    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('highest_qualification'):
            raise serializers.ValidationError('Please set highest qualification')
        if not attrs.get('from_date'):
            raise serializers.ValidationError('Please set from date')
        if not attrs.get('to_date') and attrs.get('present') == False:
            raise serializers.ValidationError('Please set end date')
        if attrs.get('from_date') and attrs.get('to_date'):
            if attrs.get('from_date') > attrs.get('to_date'):
                raise serializers.ValidationError('Please select start date less than end date')
        return attrs


    def get_highest_qualification_name(self, obj):
        if obj.highest_qualification:
            return obj.highest_qualification.title

    def get_programs_name(self, obj):
        if obj.programs:
            return obj.programs.title

    def get_university_name(self, obj):
        if obj.university:
            return obj.university.title

    def get_duration(self, obj):
        if obj.from_date and obj.to_date:
            return str(obj.from_date.year) + '-' + str(obj.to_date.year)
        elif obj.from_date and obj.present:
            return str(obj.from_date.year) + '-' + 'Present'

class ResumeSerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField()
    resume = Base64FileField(
        required=False, allow_null=True
    )
    # resume = serializers.FileField()

    class Meta:
        model = Resume
        fields = ('id','resume','file_name','userprofile_id',)

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('file_name'):
            file_extension = attrs.get('file_name').split('.')[1]
            if file_extension not in ['doc','docx','pdf','rtf','png','jpg','jpeg','txt']:
                raise serializers.ValidationError('This type of file is not valid.')
        return attrs

class EmployeeAvailabilitySerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeAvailability
        fields = ('id', 'days_per_year', 'hours_per_day', 'hourly_charges', 'userprofile_id','is_completed')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk


class EmployeeProfessionalShortDataSerializer(serializers.ModelSerializer):
    """
    Serializer for Employee Short Professional details
    """
    userprofile_id = serializers.SerializerMethodField()
    highest_qualification = serializers.SerializerMethodField()
    programs = serializers.SerializerMethodField()
    university = serializers.SerializerMethodField()
    # campus = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfessionalDetails
        fields = ('id', 'highest_qualification', 'programs', 'university', 'other_university', 'campus', 'other_campus', 'from_date', 'to_date', 'present', 'userprofile_id')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def get_highest_qualification(self, obj):
        data = {}
        if obj.highest_qualification:
            data={'id': obj.highest_qualification.id, 'title': obj.highest_qualification.title}
        return data

    def get_programs(self, obj):
        data = {}
        if obj.programs:
            data={'id': obj.programs.id, 'title': obj.programs.title}
        return data

    def get_university(self, obj):
        data = {}
        if obj.university:
            data={'id': obj.university.id, 'title': obj.university.title}
        return data


class EmployeeWorkShortDataSerializer(serializers.ModelSerializer):
    """
    Serializer for Employee Short Work details
    """
    userprofile_id = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    team_size = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeWorkDetails
        fields = ('id', 'client', 'project_title', 'from_date', 'to_date', 'project_location', 'role','employment_type','project_details', 'role_description', 'team_size', 'skill_used', 'userprofile_id')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def get_role(self, obj):
        data = {}
        return RoleSerializer(obj.role, many=True).data

    def get_team_size(self, obj):
        data = {}
        if obj.team_size:
            data={'id': obj.team_size.id, 'title': obj.team_size.title}
        return data

class EmployeeEmploymentShortDataSerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField()
    functional_areas = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    departments = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeEmploymentDetails
        fields = ('id', 'present', 'current_employer', 'date_start', 'date_end', 'current_designation', 'functional_areas', 'role', 'departments', 'job_role','userprofile_id','is_completed')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def get_functional_areas(self, obj):
        if obj.functional_areas:
            functional_areas = [{'id':i.id,'title':i.title} for i in obj.functional_areas.all()]
            return functional_areas

    def get_role(self, obj):
        if obj.role:
            role = [{'id':i.id,'title':i.title} for i in obj.role.all()]
            return role

    def get_departments(self, obj):
        if obj.departments:
            departments = [{'id':i.id,'title':i.title} for i in obj.departments.all()]
            return departments

class EmployeeAvailabilityShortDataSerializer(serializers.ModelSerializer):
    userprofile_id = serializers.SerializerMethodField()
    days_per_year = serializers.SerializerMethodField()
    hours_per_day = serializers.SerializerMethodField()
    hourly_charges = serializers.SerializerMethodField()


    class Meta:
        model = EmployeeAvailability
        fields = ('id', 'days_per_year', 'hours_per_day', 'hourly_charges', 'userprofile_id')

    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def get_days_per_year(self, obj):
        data = {}
        if obj.days_per_year:
            data={'id': obj.days_per_year.id, 'title': obj.days_per_year.title}
        return data

    def get_hours_per_day(self, obj):
        data = {}
        if obj.hours_per_day:
            data={'id': obj.hours_per_day.id, 'title': obj.hours_per_day.title}
        return data

    def get_hourly_charges(self, obj):
        data = {}
        if obj.hourly_charges:
            data={'id': obj.hourly_charges.id, 'title': obj.hourly_charges.title}
        return data

class EmployeeDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for employee detail viewset
    """
    basic_details = serializers.SerializerMethodField()
    professional_details = serializers.SerializerMethodField()
    employment_details = serializers.SerializerMethodField()
    work_details = serializers.SerializerMethodField()
    availability_details = serializers.SerializerMethodField()
    resume = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('id','basic_details','resume','professional_details','employment_details','work_details', 'availability_details')

    def get_basic_details(self, obj):
        basic_details = EmployeeBasicDetails.objects.filter(userprofile=obj)
        return EmployeeBasicDetailSerializer(basic_details, many=True).data

    def get_professional_details(self, obj):
        professional_details = EmployeeProfessionalDetails.objects.filter(userprofile=obj)
        return EmployeeProfessionalShortDataSerializer(professional_details, many=True).data

    def get_employment_details(self, obj):
        employment_details = EmployeeEmploymentDetails.objects.filter(userprofile=obj)
        return EmployeeEmploymentShortDataSerializer(employment_details, many=True).data

    def get_work_details(self, obj):
        work_details = EmployeeWorkDetails.objects.filter(userprofile=obj)
        return EmployeeWorkShortDataSerializer(work_details, many=True).data

    def get_availability_details(self, obj):
        availability_details = EmployeeAvailability.objects.filter(userprofile=obj)
        return EmployeeAvailabilityShortDataSerializer(availability_details, many=True).data

    def get_resume(self, obj):
        data = {}
        resume = Resume.objects.filter(userprofile=obj).values_list('id', 'file_name').first()
        if resume:
            data={'id': resume[0], 'file_name': resume[1]}
        return data

class BankAccountsSerializer(serializers.ModelSerializer):
    """
    Serializer for Bank Accounts
    """
    bank_name = serializers.SerializerMethodField()

    class Meta:
        model = BankAccounts
        fields = ('id', 'user', 'bank', 'bank_name', 'account_type', 'iban', 'account_holder', 'branch_identifier','branch_address','currency', 'bank_code','routing_number', 'customer_url','is_default','bank_account_no')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('bank'):
            raise serializers.ValidationError('Please select Bank')
        if not attrs.get('account_type'):
            raise serializers.ValidationError('Please set Account Type')
        if not attrs.get('iban'):
            raise serializers.ValidationError('Please set IBAN')
        if not attrs.get('account_holder'):
            raise serializers.ValidationError('Please set Account Holder Name')
        if not attrs.get('branch_identifier'):
            raise serializers.ValidationError('Please set Branch Identifier')
        if not attrs.get('branch_address'):
            raise serializers.ValidationError('Please set Branch Address')
        if not attrs.get('currency'):
            raise serializers.ValidationError('Please set Currency')
        if not attrs.get('routing_number'):
            raise serializers.ValidationError({"routing_number": "Please set routing number"})
        if not attrs.get('bank_account_no'):
            raise serializers.ValidationError({"bank_account_no": "Please set Bank Account Number"})
        return attrs

    def get_bank_name(self, obj):
        if obj.bank:
            return obj.bank.title

    ###############################Temporary Comment changes related to Dowlla Payment##############################
    def create(self, validated_data):
 
        bank = validated_data.get('bank', None)
        iban = validated_data.get('iban', None)
        account_holder = validated_data.get('account_holder', None)
        branch_identifier = validated_data.get('branch_identifier', None)
        branch_address = validated_data.get('branch_address', None)
        account_type = validated_data.get('account_type', None)
        bank_account_no = validated_data.get('bank_account_no', None)
        currency = validated_data.get('currency', None)
        account_holder = validated_data.get('account_holder', None)
        routing_number = validated_data.get('routing_number', None)
        bank_name = bank.title
        user  = self.context['request'].user
        user_profile = UserProfile.objects.get(user=user)
        FirstName = user_profile.first_name
        LastName = user_profile.last_name
        email = user.email
        businessName =  user_profile.title
        address1 = user_profile.address.name if user_profile.address else None

        if bank_account_no is not None:
            bank_obj = BankAccounts.objects.filter(bank_account_no = bank_account_no).values_list('bank_account_no', flat=True)
            if bank_obj.exists():
                raise serializers.ValidationError({"bank_account_no": "This account number is already existing."})

            else:
    
                data = {'FirstName':FirstName,'LastName':LastName,'businessName':businessName,'address1':address1,
                'email':email,'bank_name':bank_name,'iban':iban,'account_holder':account_holder,'branch_identifier':branch_identifier,
                'branch_address':branch_address,'account_type':account_type,'currency':currency,'routing_number':routing_number,
                'bank_account_no':bank_account_no}

                created_customer = create_customer(data)

                if created_customer['status'] == 200:
                    instance = super().create(validated_data)
                    bankaccount_obj = BankAccounts.objects.get(id=instance.id)
                    bankaccount_obj.funding_source_url = created_customer['funding_source_url']
                    bankaccount_obj.save()
                    
                    return instance



class TestClassSerializer(serializers.ModelSerializer):
    """
    Serializer for Transactions
    """
    photo = serializers.ImageField(required=False, allow_null=True,use_url=True)

    class Meta:
        model = TestClass
        fields = ('id','photo','reference_no')

    # def validate(self, attrs):
    #     attrs = super().validate(attrs)
    #     print ("ppppppppppppppppppppppppppppppppppp", attrs)
    #     return attrs

    # def to_representation(self, obj):
    #     data = {'amount': float(obj.amount),
    #         'currency': str(obj.currency),}
    #     return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        conn = S3Connection(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,host=AWS_HOST)
        #connecting to aws with specific endpoint reason
        bucket = conn.get_bucket(AWS_S3_BUCKET_NAME)
        #getting bucket from AWS
        key = bucket.get_key(instance.photo.name, validate=True)
        if key:
            url = key.generate_url(900)
            representation['photo'] = "{}".format(url)
        return representation

    # def to_internal_value(self, data):
    #     # data = json.loads(data)
    #     # photo = data.get('photo')

    #     # if self.context.get('request').method == "PUT" and not data.get('photo'):
    #     #     instance = TestClass.objects.get(id=data.get('id'))
    #     #     print ("aaaaaaaaaaaaaaaaaaaaaaaaaa", instance, data.get('id'))
    #     #     data = data.copy()
    #     #     data["photo"]= instance.photo

    #     # print ("llllllllllllllllllllllllll", err)

    #     # file = urllib.request.urlopen(photo)
    #     # # file = default_storage.open(photo, 'rb')
    #     # data = data.copy()
    #     # data["photo"]= file
    #     # data = super().to_internal_value(data)
    #     return data

    def create(self, validated_data):
        # print ("kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk", validated_data)

        instance = super().create(validated_data)

        return instance
