
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db.models.signals import post_save
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField
from django.dispatch import receiver

from google_places.models import Place
from core.utils import convert_file_to_base64

from phonenumber_field.modelfields import PhoneNumberField
from mptt.models import MPTTModel, TreeForeignKey
from sorl.thumbnail import get_thumbnail
from django.core.validators import MinLengthValidator

from rest_framework.response import Response

from .constants import (
    GENDER, MARITAL_STATUS, JOB_ROLE, PROJECT_LOCATION, EMPLOYEE_STATUS, RATING_CHOICES, BANK_ACCOUNT_TYPE, ROLES, QUESTION_TYPES
)

from common.models import (
    Expertise, Experience, HourlyBudget, HighestQualification, Role, Department, TeamSize, Availability, Country, State, AvailabilityDaysPerYear, Programs, University, Campus, Bank
)
import datetime
from django.core.validators import RegexValidator
from djmoney.settings import CURRENCY_CHOICES
# from django_iban.fields import IBANField
from localflavor.generic.models import IBANField
from djmoney.models.fields import MoneyField

HOURS_CHOICES = []

for h in range(1, 25):
    HOURS_CHOICES.append((h,h))

alphaSpaces = RegexValidator(r"^[a-zA-Z0-9., ']+$", 'Only alphanumerics are allowed.')

class MyUserManager(BaseUserManager):
    """
    A custom user manager to deal with emails or phones as unique identifiers
    for auth instead of usernames. The default that's used is "UserManager"
    """

    def _create_user(self, email, phone, password=None,id=None,provider=None,name=None,photoUrl=None, user_name=None, **extra_fields):


        """
        Creates and saves a User with the given email and password.
        """
        fname =''
        lname=''

        if email is None and phone is None and user_name is None:

            raise ValueError('The email or phone must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if name:
            fullname = name.split(' ')
            fname = fullname[0]
            lname = fullname[1]

        if email:
            try:
                if(User.objects.get(email=email)):
                    profile = User.objects.get(email=email)

                    UserProfile.objects.filter(user_id=profile.id).update(provider=provider)
                    UserProfile.objects.filter(user_id=profile.id).update(first_name=fname)
                    UserProfile.objects.filter(user_id=profile.id).update(last_name=lname)
                    #UserProfile.objects.filter(user_id=profile.id).update(photo=photoUrl)

                    if provider == 'GOOGLE':
                        UserProfile.objects.filter(user_id=profile.id).update(google_id=id)

                    elif provider == 'FACEBOOK':
                        UserProfile.objects.filter(user_id=profile.id).update(facebook_id=id)

                    elif provider == 'LINKEDIN':
                        UserProfile.objects.filter(user_id=profile.id).update(linkedin_id=id)

                    return user

            except User.DoesNotExist:
                pass

        if phone:
            try:
                if(User.objects.get(userprofile__phone_number=phone)):
                    profile = User.objects.get(userprofile__phone_number=phone)
                    UserProfile.objects.filter(user_id=profile.id).update(provider=provider)
                    UserProfile.objects.filter(user_id=profile.id).update(first_name=fname)
                    UserProfile.objects.filter(user_id=profile.id).update(last_name=lname)

                elif provider == 'FACEBOOK':
                        UserProfile.objects.filter(user_id=profile.id).update(facebook_id=id)

                elif provider == 'GOOGLE':
                        UserProfile.objects.filter(user_id=profile.id).update(google_id=id)

                elif provider == 'LINKEDIN':
                        UserProfile.objects.filter(user_id=profile.id).update(linkedin_id=id)

            except User.DoesNotExist:
                pass

        if user_name:
            try:
                User.objects.get(user_name=user_name)
                raise ValueError('This username has already been registered.')
            except User.DoesNotExist:
                pass



        if password is not None:
            user.set_password(password)
        user.save()

        # profile will be created by signal
        profile = UserProfile.objects.get(user=user)

        profile.phone_number = phone
        user.user_name = user_name
        profile.first_name = fname
        profile.last_name = lname
        profile.save(update_fields=['phone_number'])
        user.save(update_fields=['user_name'])
        profile.save(update_fields=['first_name'])
        profile.save(update_fields=['last_name'])


        profile.provider = provider
        profile.save(update_fields=['provider'])

        if provider == 'GOOGLE':
            profile.google_id = id
            profile.save(update_fields=['google_id'])

        elif provider == 'FACEBOOK':
            profile.facebook_id = id
            profile.save(update_fields=['facebook_id'])


        elif provider == 'LINKEDIN':
            profile.linkedin_id = id
            profile.save(update_fields=['linkedin_id'])

        return user

    def create_user(self, email=None, phone=None, password=None,id=None,provider=None,name=None,photoUrl=None,user_name=None,**extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_tempuser', False)
        return self._create_user(
                            email, phone, password,id,provider,name,photoUrl,user_name, **extra_fields)


    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class KeyVal(models.Model):
    value = models.CharField(max_length=240, db_index=True)
    key = models.CharField(max_length=240, db_index=True)

    def __str__(self):
        return self.value

class SecurityQuestion(models.Model):
    """
    Model for Security questions
    """
    title = models.CharField(max_length=300)
    question_type = models.CharField(choices=QUESTION_TYPES, max_length=20)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=-1)
    vals = models.ManyToManyField(
        KeyVal,
        blank=True,
        related_name='keyvals'
    )

    def __str__(self):
        return 'Q{} {}'.format(self.id, str(self.title)[:25] + '...')



class User(AbstractBaseUser, PermissionsMixin):
    """
    Email and phone are not required because user can login by email or phone.
    We need check unique of this fields in serializers
    """
    email = models.EmailField(blank=True, null=True)
    is_tempuser = models.BooleanField(
        _('tempuser status'),
        default=False,
        help_text=_('Designates whether this user is temporary user or permanent user.'),
    )

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_auth = models.BooleanField(
        _('Auth status'),
        default=False,
    )
    user_name = models.CharField(max_length=500, blank=True, null=True, validators=[MinLengthValidator(5)])
    security_question = models.ForeignKey(SecurityQuestion, related_name='users',blank=True, null=True, on_delete=models.SET_NULL)

    USERNAME_FIELD = 'email'
    objects = MyUserManager()

    def __str__(self):
        # print ("ssssssssssssssssssssssssssssssssssssssss", self.email, self.userprofile.phone_number)
        return self.email #or str(self.userprofile.phone_number)

    def rocket_username(self) -> str:
        """
        For user registration rocket.chat use first_name, last_name
        and username from user instance. But we can't set email as username,
        that's why want replace @ to at
        """
        if self.email:
            return self.email.replace('@', 'at')
        elif self.userprofile.phone_number:
            return str(self.userprofile.phone_number)
        elif self.user_name:
            return self.user_name

    @property
    def first_name(self) -> str:
        # for rocket.chat
        return self.userprofile.first_name or self.rocket_username()

    @property
    def last_name(self) -> str:
        # for rocket.chat
        return self.userprofile.last_name or ''

    @property
    def username(self) -> str:
        # for rocket.chat
        return self.rocket_username()

    def get_full_name(self) -> str:
        return '{} {}'.format(self.first_name, self.last_name) or self.username

    def get_short_name(self) -> str:
        return self.first_name or self.username

class Answer(models.Model):
    """
    Model for Security answers
    """
    security_question = models.ForeignKey(
        SecurityQuestion,
        related_name='answers',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, related_name='answer', null=True)
    response_text = models.TextField(blank=True, null=True, default='')


    def __str__(self):
        return 'Answer ({})'.format(self.response_text)

class Specialization(MPTTModel):
    """
    Model with employee specializations
    """
    title = models.CharField(max_length=50)
    parent = TreeForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
        db_index=True
    )

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=150, blank=True, null=True, default='')
    last_name = models.CharField(max_length=150, blank=True, null=True,  default='')
    phone_number = PhoneNumberField(blank=True, null=True)
    photo = models.ImageField(upload_to='pictures/userpic', blank=True, null=True)
    photo_bounds = JSONField(blank=True, null=True)
    passport_photo = models.ImageField(
        upload_to='pictures/passport',
        blank=True,
        null=True
    )
    driver_license_photo = models.ImageField(
        upload_to='pictures/drivers',
        blank=True,
        null=True
    )
    address = models.ForeignKey(Place, blank=True, null=True)
    role = models.CharField(choices=ROLES, max_length=10)
    # employee profile
    title = models.CharField(max_length=100, blank=True)
    summary = models.TextField(blank=True)
    specializations = models.ManyToManyField(Specialization, blank=True)
    skills = models.ManyToManyField(
        Specialization,
        blank=True,
        related_name='skills'
    )
    # creator profile
    employees = models.ManyToManyField(
        User,
        blank=True,
        related_name='employers'
    )

    facebook_id = models.CharField(max_length=50,blank=True, null=True)
    google_id = models.CharField(max_length=50,blank=True, null=True)
    twitter_id = models.CharField(max_length=50,blank=True, null=True)
    linkedin_id = models.CharField(max_length=50,blank=True, null=True)
    paypal_id = models.CharField(max_length=50,blank=True, null=True)
    snapchat_id = models.CharField(max_length=50,blank=True, null=True)
    angellist_id = models.CharField(max_length=50,blank=True, null=True)
    provider = models.CharField(max_length=50,blank=True, null=True)
    temp_password = models.CharField(max_length=20,blank=True, null=True)

    zip = models.CharField(max_length=6, blank=True, null=True)
    ssn = models.IntegerField(blank=True,null=True)

    token   = models.CharField(max_length=100,blank=True, null=True)
    secret  = models.CharField(max_length=100,blank=True, null=True)

    rating = models.IntegerField(choices=RATING_CHOICES, default=0)

    # access_token = models.CharField(max_length=255, blank=True, null=True, editable=False)
    # url = models.URLField(blank=True, null=True)


    def __str__(self):
        return 'UserProfile {} {} {}'.format(
            self.first_name, self.last_name, self.user.email
        )

    def get_photo_crop(self):
        """
        Resize user photo by bounds
        """
        if self.photo:
            img = get_thumbnail(
                self.photo,
                '{}x{}'.format(
                    self.photo_bounds['width'], self.photo_bounds['height']
                ),
                crop='{}px {}px {}px {}px'.format(
                    self.photo_bounds['x'],
                    self.photo_bounds['y'],
                    self.photo_bounds['width'] + self.photo_bounds['x'],
                    self.photo_bounds['height'] + self.photo_bounds['y']
                )
            )
            return convert_file_to_base64(img)
        return


class Education(models.Model):
    """
    Model for employee education
    """
    userprofile = models.ForeignKey(UserProfile, related_name='educations')
    date_start = models.DateField()
    date_end = models.DateField()
    degree = models.CharField(max_length=50)
    school = models.CharField(max_length=50)

    def __str__(self):
        return '{} - {}'.format(self.degree, self.school)


class WorkExperience(models.Model):
    """
    Model for employee work experience
    """
    userprofile = models.ForeignKey(UserProfile, related_name='works')
    date_start = models.DateField()
    date_end = models.DateField()
    company = models.CharField(max_length=50)
    position = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return '{} - {}'.format(self.company, self.position)


@receiver(post_save, sender=User)
def auto_create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


class EmployeeBasicDetails(models.Model):
    """
    Model for employee basic details
    """
    userprofile = models.OneToOneField(UserProfile, related_name='basic_details')
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=8, choices=GENDER)
    marital_status = models.CharField(max_length=8, choices=MARITAL_STATUS)
    # interests = models.TextField(max_length=250,blank=True, null=True)
    hobbies = models.TextField(max_length=250,blank=True, null=True, validators=[alphaSpaces])
    is_completed = models.BooleanField(
        _('Completed'),
        default=False,
    )
    employee_status = models.CharField(max_length=8, choices=EMPLOYEE_STATUS,blank=True, null=True)
    address_line1 = models.CharField(max_length=200, blank=True, null=True, default='')
    address_line2 = models.CharField(max_length=200, blank=True, null=True, default='')
    city = models.CharField(max_length=200, blank=True, null=True, default='')
    country = models.ForeignKey(Country, blank=True,null=True, related_name='employee_country')
    state = models.ForeignKey(State, blank=True,null=True, related_name='employee_state')
    pin_code = models.CharField(max_length=10, blank=True, null=True, default='')
    contact_details = PhoneNumberField(blank=True, null=True)
    alternate_contact_details = PhoneNumberField(blank=True, null=True)
    total_experience = models.ForeignKey(Experience,related_name='experience',blank=True, null=True)

class OtherQualification(models.Model):
    """
    Model for employee other qualification
    """
    userprofile = models.ForeignKey(UserProfile, related_name='other_qualifications')
    qualification_name = models.CharField(max_length=50)

    def __str__(self):
        return '{} - {}'.format(self.qualification_name)

class EmployeeProfessionalDetails(models.Model):
    """
    Model for employee professional details
    """
    userprofile = models.ForeignKey(UserProfile, related_name='professional_details')
    highest_qualification = models.ForeignKey(HighestQualification,blank=True,null=True,related_name='highest_qualifications')
    programs = models.ForeignKey(Programs, blank=True,null=True, related_name='programs')
    university = models.ForeignKey(University, blank=True,null=True, related_name='university_name')
    other_university = models.CharField(max_length=500, blank=True, null=True, default='')
    campus = models.ManyToManyField(Campus, blank=True,related_name='campus')
    other_campus = models.CharField(max_length=500, blank=True, null=True, default='')
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    present = models.BooleanField(
        _('Present'),
        default=False,
    )
    is_completed = models.BooleanField(
        _('Completed'),
        default=False,
    )


class Resume(models.Model):
    """
    Model for employee Resume
    """
    userprofile = models.OneToOneField(UserProfile, related_name='resume')
    resume = models.FileField(upload_to='employee/resume', blank=True, null=True)
    file_name = models.CharField(max_length=1000, blank=True, null=True, default='')

    def delete(self,*args,**kwargs):
        if os.path.isfile(self.resume.path):
            os.remove(self.resume.path)

        super(Resume, self).delete(*args,**kwargs)

class EmployeeEmploymentDetails(models.Model):
    """
    Model for employee employment details
    """
    userprofile = models.ForeignKey(UserProfile, related_name='employment_details')
    current_employer = models.CharField(max_length=100, blank=True, null=True, default='')
    date_start = models.DateField(blank=True, null=True)
    date_end = models.DateField(blank=True, null=True)
    current_designation = models.CharField(max_length=100, blank=True, null=True, default='')
    functional_areas = models.ManyToManyField(Expertise, blank=True, related_name='functional_areas')
    role = models.ManyToManyField(Role, blank=True, related_name='employee_roles')
    departments = models.ManyToManyField(Department, blank=True, related_name='emp_departments')
    job_role = models.CharField(max_length=15, choices=JOB_ROLE)
    present = models.BooleanField(
        _('Present'),
        default=False,
    )
    is_completed = models.BooleanField(
        _('Completed'),
        default=False,
    )

class EmployeeWorkDetails(models.Model):
    """
    Model for employee work details
    """
    userprofile = models.ForeignKey(UserProfile, related_name='work_details')
    client = models.CharField(max_length=100, blank=True, null=True, default='')
    project_title = models.CharField(max_length=100, blank=True, null=True, default='')
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    project_location = models.CharField(max_length=15, choices=PROJECT_LOCATION, blank=True, null=True)
    role = models.ManyToManyField(Role, blank=True, related_name='work_roles')
    employment_type = models.CharField(max_length=15, choices=JOB_ROLE)
    project_details = models.TextField(max_length=1000,blank=True, null=True)
    role_description = models.TextField(max_length=1000,blank=True, null=True)
    team_size = models.ForeignKey(TeamSize, blank=True,null=True, related_name='employees')
    skill_used = models.TextField(max_length=1000,blank=True, null=True)
    is_completed = models.BooleanField(
        _('Completed'),
        default=False,
    )

class EmployeeAvailability(models.Model):
    """
    Model for employee availability
    """
    userprofile = models.OneToOneField(UserProfile, related_name='availability_details')
    days_per_year = models.ForeignKey(AvailabilityDaysPerYear, blank=True,null=True, related_name='no_of_days')
    hours_per_day = models.ForeignKey(Availability,blank=True, null=True)
    hourly_charges = models.ForeignKey(HourlyBudget, null=True, related_name='employees_hourly_charges')
    is_completed = models.BooleanField(
        _('Completed'),
        default=False,
    )

class BankAccounts(models.Model):
    """
    Model for Bank Account details
    """
    user = models.ForeignKey(User, related_name='bank_account_details',blank=True,null=True)
    bank = models.ForeignKey(Bank, blank=True,null=True, related_name='bank')
    account_type = models.CharField(max_length=30, choices=BANK_ACCOUNT_TYPE, blank=True, null=True)
    iban = IBANField(max_length=34, blank=True, null=True)
    account_holder = models.CharField(max_length=100, blank=True, null=True)
    bank_account_no = models.CharField(max_length=17, blank=True, null=True)
    branch_identifier = models.CharField(max_length=12, blank=True, null=True)
    branch_address = models.CharField(max_length=300, blank=True, null=True)
    routing_number = models.CharField(max_length=9, blank=True, null=True)
    currency = models.CharField(max_length=100, choices=CURRENCY_CHOICES, blank=True, null=True)
    bank_code = models.CharField(max_length=12, blank=True, null=True)
    customer_url = models.URLField(max_length=100,blank=True,null=True)
    is_default = models.BooleanField(
        _('Default'),
        default=False,
    )
    funding_source = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return ('bank')

class TestClass(models.Model):
    """
    Model for transaction details
    """
    photo = models.ImageField(upload_to='test', blank=True, null=True)
    reference_no = models.CharField(max_length=100, blank=True, null=True)
