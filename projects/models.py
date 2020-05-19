from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .constants import (
    STAGE, QUESTION_GROUPS, QUESTION_TYPES, PROJECT_STATUS, DOCUMENT_TYPE,LOCATOR_YES_NO_CHOICES, FEATURE_VALUE_TYPE, TASK_ASSIGN_STATUS,
    RETURN_IN_FORM,DEBT_TYPE,PAYMENT_TYPES,NATURE_OF_DILUTION,REMIND_ME,REMIND,FREQUENCY,DAYS_OF_WEEK,MONTHS_IN_YEAR,TRANSACTION_MODE,
    TRANSACTION_STATUS
)
from accounts.models import User, BankAccounts
from accounts.constants import RATING_CHOICES
from django.apps import apps
from django.core.exceptions import ValidationError
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from djmoney.models.validators import MaxMoneyValidator, MinMoneyValidator
import moneyed
from moneyed.localization import _FORMATTER
from decimal import ROUND_HALF_EVEN
from django.contrib.postgres.fields import JSONField
from ckeditor.fields import RichTextField
import common
from common.models import Parameter
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from accounts.models import UserProfile
from datetime import timedelta, datetime, date
from django.utils.dates import MONTHS
from multiselectfield import MultiSelectField


MODEL_CHOICES = [('','')]

for model in apps.all_models['common']:
    MODEL_CHOICES.append((model,model))


class ProjectRegistrationFeature(models.Model):
    """
    Model for project registration features
    """
    title = models.CharField(max_length=500,null=True)
    order = models.IntegerField(default=-1)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.title

class ProjectRegistrationType(models.Model):
    """
    Model for project registration type
    """
    title = models.CharField(max_length=100,null=True)
    amount = models.CharField(max_length=100,null=True)
    description = models.CharField(max_length=500,null=True)
    # features = models.ManyToManyField(
    #     ProjectRegistrationFeature,
    #     blank=True,
    #     related_name='features'
    # )
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.title

class ProjectRegistrationPackage(models.Model):
    """
    Model for project registration packages
    """
    title = models.CharField(max_length=100,null=True)
    description = models.CharField(max_length=500,null=True)
    amount = models.IntegerField(null=True)
    currency = models.CharField(max_length=20,null=True)
    registration_type = models.ForeignKey(ProjectRegistrationType, related_name='registration_type_package',null=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.title

@receiver(post_save, sender=ProjectRegistrationPackage)
def generate_amount(sender, instance, created, **kwargs):
    amount_list = ProjectRegistrationPackage.objects.filter(registration_type=instance.registration_type, is_active=True).values_list('amount',flat=True)
    instance.registration_type.amount = "$" + str(min(list(amount_list)))
    instance.registration_type.save()


class PackageFeaturevalues(models.Model):
    """
    Model for package features values
    """

    registration_package = models.ForeignKey(ProjectRegistrationPackage, related_name='feature_package', null=True)
    feature = models.ForeignKey(ProjectRegistrationFeature, blank=True, related_name='feature_value', null=True)
    feature_value_type = models.CharField(choices=FEATURE_VALUE_TYPE, max_length=10, default='')
    value = models.CharField(max_length=100, null=True, blank=True)
    is_available = models.BooleanField(default=False)

    # def __str__(self):
    #     return self.title



class ProjectLaunchType(models.Model):
    """
    Model for project Launch type
    """
    #project = models.ForeignKey(Project, related_name='launch')
    title = models.CharField(max_length=100,null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class ProjectFundType(models.Model):
    """
    Model for project Fund type
    """
    title = models.CharField(max_length=100,null=True)
    description = models.TextField(blank=True, null=True)
    # launch_type = models.ForeignKey(ProjectLaunchType,related_name='projectfund', null=True)
    is_active = models.BooleanField(default=True)
    terms_condition = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class Project(models.Model):
    """
    Model for idea and startup projects
    """
    title = models.CharField(max_length=200)
    stage = models.CharField(max_length=8, choices=STAGE)
    owner = models.ForeignKey(User, related_name='projects')
    # FIXME: we really need it?
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='participants'
    )
    date_start = models.DateField(blank=True, null=True)
    date_end = models.DateField(blank=True, null=True)
    status = models.CharField(
        choices=PROJECT_STATUS,
        default=PROJECT_STATUS[0][0],
        max_length=10
    )
    is_visible = models.BooleanField(default=True)
    registration_type = models.ForeignKey(ProjectRegistrationType, related_name='projects',null=True)
    package = models.ForeignKey(ProjectRegistrationPackage, blank=True, related_name='project_package', null=True)
    is_registered = models.BooleanField(default=False)
    show_nda = models.BooleanField(
        _('nda_status'),
        default=True,
    )
    add_nda =  models.BooleanField(default=False)
    having_blockchain_entry = models.BooleanField(default=False)
    transaction_hash = models.CharField(max_length=100, blank=True, null=True)
    block_number = models.IntegerField(blank=True, null=True)
    market_price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')

    def __str__(self):
        return self.title

    def get_answers_progress(self) -> int:
        """
        Percentage of answers regarding project questions
        """
        # TODO: optimize queryset
        q_count = Question.objects.filter(
            Q(stage=self.stage) &
            Q(is_active=True)
            ).count()

        a_count = self.answers.filter(question__stage=self.stage,question__is_active=True,project_id=self.id).count()
        if q_count == 0:
            return 100
        return round(a_count * 100 / q_count)
        

class KeyVal(models.Model):
    value = models.CharField(max_length=240, db_index=True)

    def __str__(self):
        return self.value

class Question(models.Model):
    """
    Model for idea and startup questions
    """
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=300, default='')
    stage = models.CharField(max_length=30, choices=STAGE)
    group = models.CharField(choices=QUESTION_GROUPS, max_length=50)
    question_type = models.CharField(choices=QUESTION_TYPES, max_length=50)
    registration_type = models.ForeignKey(ProjectRegistrationType, related_name='registration_type',null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=-1)
    model = models.CharField(choices=MODEL_CHOICES, max_length=100, blank=True, null=True)
    parent_question = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        related_name='subquestions'
    )
    vals = models.ManyToManyField(
        KeyVal,
        blank=True,
        related_name='keyvals'
    )

    def __str__(self):
        return 'Q{} {}'.format(self.id, str(self.title)[:25] + '...')


class QuestionIdea(Question):
    """
    Proxy model for idea questions
    """
    class Meta:
        proxy = True


class QuestionStartup(Question):
    """
    Proxy model for startup questions
    """
    class Meta:
        proxy = True


class QuestionRegistration(Question):
    """
    Proxy model for Registration questions
    """
    class Meta:
        proxy = True


class Answer(models.Model):
    """
    Model for idea and startup answers
    """
    question = models.ForeignKey(
        Question,
        related_name='answers',
        on_delete=models.CASCADE
    )
    project = models.ForeignKey(Project, related_name='answers')
    response_text = models.TextField(blank=True, null=True, default='')
    is_private = models.BooleanField(default=False)
    boolean_text = models.NullBooleanField(choices=LOCATOR_YES_NO_CHOICES,
                                max_length=3,
                                blank=True, null=True, default=None,)

    parent_answer =  models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name='sub_question_answers'
    )

    class Meta:
        unique_together = ('question', 'project')

    def __str__(self):
        return 'Answer ({} {})'.format(self.response_text,self.boolean_text)

class AnswerSwot(models.Model):
    """
    Model for idea and startup swot answers
    """
    answer = models.OneToOneField(Answer, related_name='swot_answer')
    swot_answer = JSONField(blank=True, null=True)

    def __str__(self):
        return str(self.pk)


class AnswerImage(models.Model):
    """
    Model for idea and startup image answers
    """
    answer = models.OneToOneField(Answer, related_name='image')
    image = models.ImageField(upload_to='projects/answers')

    def __str__(self):
        return str(self.pk)


class AnswerSpreadsheet(models.Model):
    """
    Model for startup spreadsheet answers
    """
    answer = models.OneToOneField(Answer, related_name='spreadsheet')
    spreadsheet = models.FileField(upload_to='projects/spreadsheets')

    def __str__(self):
        return str(self.pk)

class AnswerPowerPoint(models.Model):
    """
    Model for startup spreadsheet answers
    """
    answer = models.OneToOneField(Answer, related_name='powerpoint')
    powerpoint = models.FileField(upload_to='projects/powerpoints')

    def __str__(self):
        return str(self.pk)


class AnswerDiagram(models.Model):
    """
    Model for startup diagram answers
    """
    answer = models.OneToOneField(Answer, related_name='diagram')
    # diagram = models.TextField()
    diagram = models.ImageField(upload_to='projects/diagrams')

    def __str__(self):
        return str(self.pk)

class AnswerList(models.Model):
    """
    Model for List answers
    """
    answer = models.OneToOneField(Answer, related_name='list', blank=True, null=True,)
    model = models.CharField(choices=MODEL_CHOICES, max_length=100, blank=True, null=True, default='')
    option_id = models.IntegerField(blank=True, null=True)


class AnswerDate(models.Model):
    """
    Model for Date answers
    """
    answer = models.OneToOneField(Answer, related_name='date')
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.pk)

class AnswerMultiList(models.Model):
    """
    Model for MultiList answers
    """
    answer = models.OneToOneField(Answer, related_name='multilist',null=True,)
    multilist = models.ManyToManyField(KeyVal,related_name='multilist',blank=True)

class AnswerRadio(models.Model):
    """
    Model for Radio answers
    """
    answer = models.OneToOneField(Answer, related_name='radio',null=True,blank=True)
    radio = models.ForeignKey(KeyVal, related_name='radio',null=True,blank=True)

    def __str__(self):
        return str(self.pk)

class AnswerOcr(models.Model):
    """
    Model for OCR type answers
    """
    answer = models.OneToOneField(Answer, related_name='ocr')
    ocr = models.FileField(upload_to='projects/ocr')

    def __str__(self):
        return str(self.pk)

# class AnswerSubQuestion(models.Model):
#     """
#     Model for Sub Questions answers
#     """
#     answer = models.ManyToManyField(Answer, related_name='sub_question',null=True,blank=True)
#     sub_questions = models.ManyToManyField(KeyVal,related_name='sub_question',null=True,blank=True)

#     def __str__(self):
#         return str(self.pk)

#Predefined milestones user can select a template(Predefined Milestone from this list)
class PredefinedMilestone(models.Model):
    """
    Model for project milestones
    """
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=100, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    icon_name = models.CharField(max_length=100, blank=True, null=True, default="default.png")
    icon_category = models.CharField(max_length=100, blank=True, null=True, default="default")

    def __str__(self):
        return self.title


class Milestone(models.Model):
    """
    Model for project milestones
    """
    project = models.ForeignKey(Project, related_name='milestones')
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=100, blank=True)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    is_milestone_in_startup_stage = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    icon_name = models.CharField(max_length=100, blank=True, null=True)
    icon_category = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return self.pk and self.title
    
    
class TaskStatus(models.Model):
    """
    Model storage tasks status for kanban board
    """
    title = models.CharField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'status'
        verbose_name_plural = 'tasks status'
        ordering = ('order',)

    def __str__(self):
        return self.pk and self.title


class TaskTag(models.Model):
    """
    Model for task tags
    """
    title = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'task tags'

    def __str__(self):
        return self.title




class Task(models.Model):
    """
    Model for kanban tasks
    """
    milestone = models.ForeignKey(
        Milestone,
        related_name='milestone_tasks',
        null=True
    )
    owner = models.ForeignKey(User, related_name='owner_tasks')
    parent_task = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='subtasks'
    )
    dependency_task = models.ManyToManyField(
        'projects.DependencyTask',
        blank=True,
        related_name='dependency_task',
    )
    title = models.CharField(max_length=100,blank=True,null=True)
    description = models.TextField(blank=True)
    status = models.ForeignKey(TaskStatus, related_name='status_tasks',blank=False,null=True)
    assignee = models.ForeignKey(User, blank=True, null=True)
    participants = models.ManyToManyField(
        User,
        related_name='tasks',
        blank=True
    )
    due_date = models.DateField(blank=True, null=True)
    tags = models.ManyToManyField(TaskTag, blank=True)
    complete_percent = models.SmallIntegerField(
        choices=[(x, x) for x in range(20, 120, 20)],
        blank=True,
        null=True
    )
    order = models.SmallIntegerField(default=0)
    is_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'task'
        verbose_name_plural = 'tasks'
        ordering = ('order',)

    def __str__(self):
        return 'Task ({})'.format(self.title)
    
class DependencyTask(models.Model):
    """
    Model to create relation between Goal and milestone
    """
    milestone = models.ForeignKey(Milestone,blank=False, related_name="dependent_milestone")
    task = models.ForeignKey(Task,blank=True,related_name="dependent_task", null=True)

    class Meta:
        verbose_name = 'Dependency Task'
        verbose_name_plural = 'Dependency Tasks'

    def __str__(self):
        return '%s-%s'  %(self.milestone,self.task)

class TaskRule(models.Model):
    """
    Model rule for kanban tasks
    """
    task = models.ForeignKey(Task, related_name='rules')
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class TaskDocument(models.Model):
    """
    Model for tasks documents
    """
    task = models.ForeignKey(Task, related_name='documents')
    doc_type = models.CharField(max_length=25, choices=DOCUMENT_TYPE)
    name = models.CharField(max_length=100)
    ext = models.CharField(max_length=10)
    document = models.FileField(upload_to='tasks/documents')

    def __str__(self):
        return '{}.{}'.format(self.name, self.ext)


@receiver(post_save, sender=Project)
def handler_create_default_milestone(
        sender, instance=None, created=False, **kwargs
):
    """
    We need create default milestone after creation new project
    """
    if created:
        Milestone.objects.create(
            project=instance,
            title='Complete the Startup Flow',
            date_start=timezone.now(),
            date_end=timezone.now(),
            is_milestone_in_startup_stage=True,
            icon_name = 'default.png',
            icon_category = 'default'          
        )

class TaskAssignDetails(models.Model):
    """
    Model for tasks assigns to employee details
    """
    task = models.ForeignKey(Task, related_name='task_assign_details', blank=True, null=True)
    employee = models.ForeignKey(User, related_name='task_assign_details',blank=True, null=True)
    assign_date = models.DateField(blank=True, null=True, auto_now_add=True)
    completed_date = models.DateField(blank=True, null=True)
    extended_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        choices=TASK_ASSIGN_STATUS,
        default=TASK_ASSIGN_STATUS[0][0],
        max_length=10
    )
    is_complete = models.BooleanField(default=False)
    reassign_date = models.DateField(blank=True, null=True, auto_now_add=True)
    reassign_completed_date = models.DateField(blank=True, null=True)


class ProjectCompanyRole(models.Model):
    """
    Model for Company Role
    """
    title = models.CharField(max_length=300, blank=True, null=True)
    description = models.CharField(max_length=500, default='')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class ProjectBuyCompanyShare(models.Model):
    """
    Model Offer buy-in for shares for a role in company
    """
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    percentage = models.IntegerField(null=True)
    role = models.ForeignKey(ProjectCompanyRole, blank=True,null=True, related_name='company_roles')
    project_fund = models.ForeignKey('projects.ProjectFund', related_name='company_shares',null=True)
    project_backer_fund = models.ForeignKey('projects.ProjectBackerFund', related_name='company_shares_backer',null=True)

class ProjectFund(models.Model):
    """
    Model for project Fund Form
    """
    project = models.ForeignKey(Project, related_name='project_fund',null=True)
    fund = models.ForeignKey(ProjectFundType, related_name='project_fund',null=True)
    owner = models.ForeignKey(User, related_name='project_fund',null=True)
    terms_condition = models.TextField(blank=True,null=True)
    is_confirmed = models.BooleanField(default=False)

    ############ Equality crowd funding and Normal Funding ###########
    min_target_offering_amt = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)
    amount_equity = models.IntegerField(null=True)
    due_by = models.DateField(blank=True, null=True)
    return_form = models.CharField(choices=RETURN_IN_FORM, max_length=50, default='')
    price_security = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)

    ############ Loans services and P2P loan/lend ###########
    payment_type = models.CharField(choices=PAYMENT_TYPES, max_length=50, default='')
    loan_amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)
    interest_rate = models.IntegerField(null=True)

    ############ P2P loan/lend ###########
    min_peer_amt = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)

    ############ Company buy offer ###########
    organization_details = models.CharField(max_length=500, blank=True, null=True)
    current_valuation = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)

class ProjectBackerFund(models.Model):
    """
    Model for project Backer Fund Form
    """
    fund = models.ForeignKey(ProjectFund, related_name='backer_fund',null=True)
    backer = models.ForeignKey(User, related_name='backer_fund',null=True)
    quantity = models.IntegerField(null=True)
    sanction_amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)

    loan_amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)
    interest_rate = models.IntegerField(null=True)
    min_peer_amt = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)
    return_form = models.CharField(choices=RETURN_IN_FORM, max_length=50, default='')
    payment_type = models.CharField(choices=PAYMENT_TYPES, max_length=50, default='')
    create_date = models.DateField(blank=True, null=True, auto_now_add=True)
    is_closed = models.BooleanField(
        _('Is Closed'),
        default=False,
    )
    next_interest_payable_date = models.DateField(blank=True, null=True,)


class PackageList(models.Model):
    """
    Model for Package List
    """
    title = models.CharField(max_length=100,null=True)
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    position_name = models.CharField(max_length=50,null=True)
    position_number = models.IntegerField(null=True)
    days = models.IntegerField(null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_positions(self):
        """
        Resize user photo by bounds
        """
        acquire_positions = ProjectPackageDetails.objects.filter(package=self.id, expiry_date__gt=datetime.now().date(), is_active=True)
        return len(acquire_positions)

class ProjectPackageDetails(models.Model):
    """
    Model for Project Package Details
    """
    project = models.ForeignKey(Project, related_name='package_details', blank=True, null=True)
    package = models.ForeignKey(PackageList, related_name='package_details', blank=True, null=True)
    create_date = models.DateField(blank=True, null=True, auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

@receiver(post_save, sender=ProjectPackageDetails)
def auto_generate_expiry(sender, instance, created, **kwargs):
    if created:
        expiry_date = instance.create_date + timedelta(days=instance.package.days)
        instance.expiry_date = expiry_date
        instance.save()


class Time(models.Model):
    time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.time)

class ToDoList(models.Model):
    """
    Model for To Do List for creator
    """
    project = models.ForeignKey(Project, related_name='to_do_list',blank=True, null=True)
    task = models.CharField(max_length=500,null=True)
    task_description = models.CharField(max_length=500,null=True,default=None,blank=False)
    remind = models.CharField(max_length=50, choices=REMIND,null=True)
    remind_me = models.CharField(max_length=50, choices=REMIND_ME, default='Between 09:00 - 17:00',blank=True)
    start_on = models.DateField(blank=False, null=True)
    end_on = models.DateField(blank=False, null=True)
    frequency = models.CharField(max_length=50, choices=FREQUENCY,null=True)
    frequency_time =  models.ManyToManyField(Time, blank=True,related_name='frequency')
    let_system_do_it = models.BooleanField(default=True)
    repeat_months = MultiSelectField(choices=MONTHS_IN_YEAR,default=None,blank=True)
    repeat_days = MultiSelectField(max_length=50, choices=DAYS_OF_WEEK, default=None,blank=True)
    is_complete= models.BooleanField(default=False)

    def __str__(self):
        return self.task

class Notification(models.Model):
    """
    Notification on Dashboard
    """
    title = models.CharField(max_length=500,blank=True)
    to_do_list = models.ForeignKey(ToDoList,blank=False,null=True)
    read = models.BooleanField(default=False)
    read_date = models.DateTimeField(blank=False, null=True)

    def __str__(self):
        return self.title

class NdaDetails(models.Model):
    """
    Model for Nda Details
    """
    project = models.ForeignKey(Project, related_name='nda')
    description = RichTextField()
    create_date = models.DateField(blank=True, null=True, auto_now_add=True)
    docusign_envelop = models.CharField(max_length=500, blank=True, null=True)
    creator_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.description

class NdaHistoryDetails(models.Model):
    """
    Model for Nda History Details
    """
    project = models.ForeignKey(Project, related_name='nda_history')
    description = RichTextField()
    #nda = models.ForeignKey(NdaDetails, related_name='nda_history')
    updated_date = models.DateField(blank=True, null=True, auto_now=True)


class EmployeeRatingDetails(models.Model):
    """
    Model for Task related Employee Rating Details
    """
    task = models.ForeignKey(Task, related_name='employee_ratings', blank=True, null=True)
    employee = models.ForeignKey(User, related_name='employee_ratings', blank=True, null=True)
    creator = models.ForeignKey(User, related_name='ratings', blank=True, null=True)

class Ratings(models.Model):
    """
    Model with employee ratings according to parameter
    """
    parameter = models.ForeignKey(Parameter, related_name='ratings', blank=True, null=True)
    rating = models.IntegerField(choices=RATING_CHOICES, default=0)
    employee_rating_details = models.ForeignKey(EmployeeRatingDetails, blank=True, null=True,related_name='employee_ratings')

    def __str__(self):
        return self.title

@receiver(post_save, sender=Ratings)
def auto_generate_ratings(sender, instance, created, **kwargs):
    if created:
        parameter_rating = 0
        parameters = Parameter.objects.all()
        for p in parameters:
            emp_rating_details = EmployeeRatingDetails.objects.filter(employee=instance.employee_rating_details.employee,employee_ratings__parameter=p).values_list('employee_ratings', flat=True)
            rating_details = Ratings.objects.filter(id__in=list(emp_rating_details)).values_list('rating', flat=True)
            if rating_details.exists():
                rating = sum(list(rating_details)) / float(len(rating_details))
                parameter_rating += rating

        employee = UserProfile.objects.get(user=instance.employee_rating_details.employee)
        avg_rating = parameter_rating / float(len(parameters))
        employee.rating = round(avg_rating)
        employee.save()

class NotarizationDetails(models.Model):
    """
    Model for notarization details
    """
    project = models.OneToOneField(Project, related_name='document',blank=True,null=True)
    transaction_id = models.CharField(max_length=200,null=True,blank=True)
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=50,null=True,blank=True)
    last_name = models.CharField(max_length=50,null=True,blank=True)
    address_line1 = models.CharField(max_length=100,null=True,blank=True)
    address_line2 = models.CharField(max_length=100,null=True,blank=True)
    city = models.CharField(max_length=100,null=True,blank=True)
    state = models.CharField(max_length=100,null=True,blank=True)
    country = models.CharField(max_length=100,null=True,blank=True)
    pincode = models.IntegerField(null=True,blank=True) 
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    notary_name = models.CharField(max_length=200,null=True,blank=True)
    notary_city = models.CharField(max_length=200,null=True,blank=True)
    notary_registration = models.CharField(max_length=200,null=True,blank=True)

class DocumentsToNotarisation(models.Model):
    """
    Model for documents which are uploaded to online notarization
    """
    notarization_details = models.ForeignKey(NotarizationDetails, related_name='uploaded_documents',null=True, blank=True)  
    document = models.FileField(upload_to='notarization/documents', blank=True, null=True)
    is_draft = models.BooleanField(default=False,blank=True)
    document_name = models.CharField(max_length=100, blank=True, null=True)
    document_id = models.CharField(max_length=100, blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)

class NotarizedDocuments(models.Model):
    """
    Model for notarised documents
    """
    notarization_details = models.ForeignKey(NotarizationDetails, related_name='notarised_documents',null=True, blank=True)  
    document = models.FileField(upload_to='notarized/documents', blank=True, null=True)
    document_name = models.CharField(max_length=100, blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)
    
class ProjectLaunch(models.Model):
    """
    Model for launch projects
    """
    project = models.ForeignKey(Project, related_name='project_launch',null=True)
    launch = models.ForeignKey(ProjectLaunchType, related_name='project_launch',null=True)
    fund_amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', null=True)
    percentage = models.IntegerField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    price_per_share = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', null=True)
    terms_condition = models.TextField(blank=True, null=True)

class ProjectBackerLaunch(models.Model):
    """
    Model for project Backer Launch Form
    """
    project_launch = models.ForeignKey(ProjectLaunch, related_name='backer_launch',null=True)
    backer = models.ForeignKey(User, related_name='backer_launch',null=True)
    quantity = models.IntegerField(blank=True, null=True)
    create_date = models.DateField(blank=True, null=True, auto_now_add=True)
    is_closed = models.BooleanField(
        _('Is Closed'),
        default=False,
    )

class FinalProduct(models.Model):
    """
    Model for idea and startup product compare answers
    """
    answer = models.OneToOneField(Answer, related_name='productcompare_answer',null=True)
    productcompare_answer = JSONField(blank=True, null=True)

    def __str__(self):
        return str(self.pk)

class NdaToDocusign(models.Model):

	nda_details = models.ForeignKey(NdaDetails, related_name='nda_documents',null=True, blank=True)
	document = models.FileField(upload_to='nda/docusign/documents', blank=True, null=True)
	document_name = models.CharField(max_length=100, blank=True, null=True)
	enveloped = models.CharField(max_length=500, blank=True, null=True)

class ProductExpenses(models.Model):
    """
    Model for material expenses product
    """
    name = models.CharField(max_length=500,null=True)
    project = models.ForeignKey(Project, related_name='project_product_budget',null=True)
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', null=True)
    qty = models.IntegerField(null=True)
    #totalprice = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', null=True)
    shortdescription = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='product/images',blank=True,null=True)
    product_id = models.IntegerField(null=True)
    product_image = models.ImageField(upload_to='customproduct/images', blank=True, null=True)

    def __str__(self):
        return self.name

class WorkSession(models.Model):
    """
    Model for daily Work Session of employee 
    """
    task = models.ForeignKey(Task, related_name='work_session', blank=True, null=True)
    employee = models.ForeignKey(User, related_name='work_session',blank=True, null=True)
    start_datetime = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    loggedin_hours = models.CharField(blank=True, null=True, max_length=50)

class Transactions(models.Model):
    """
    Model for transaction details
    """
    user = models.ForeignKey(User, related_name='transaction_details',blank=True,null=True)
    bank_account = models.ForeignKey(BankAccounts, related_name='transaction_details',blank=True,null=True)
    reference_no = models.CharField(max_length=20, blank=True, null=True)
    create_datetime = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    amount =  MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    remark = models.CharField(max_length=500, blank=True, null=True)
    mode = models.CharField(max_length=15, choices=TRANSACTION_MODE, blank=True, null=True)
    account_no = models.CharField(max_length=34, blank=True, null=True)
    status = models.CharField(max_length=15, choices=TRANSACTION_STATUS, default='success', blank=True, null=True)
    is_external = models.BooleanField(
        _('Is External'),
        default=False,
    )
    project = models.ForeignKey(Project, related_name='transaction_details',null=True)

    def get_wallet_amount(self,user=None):
        """
        Calculate wallet amount
        """
        debit_transactions = Transactions.objects.filter(user=user,status="success",mode="withdrawal").values_list("amount",flat=True)
        credit_transactions = Transactions.objects.filter(user=user,status="success",mode="deposite").values_list("amount",flat=True)

        wallet_amount = sum(credit_transactions)-sum(debit_transactions)
        return wallet_amount

    def save(self, *args, **kwargs):
        if self.is_external== False:
            if self.__class__.objects.filter(~Q(reference_no=''),~Q(reference_no=None),is_external=False).count() == 0:
                # First object need to be set like this
                letter =  'REF/' + str(date.today().strftime("%Y")) + '/'
                number = 1
                self.reference_no = '{0}{1:07d}'.format(letter,number)
            else:
                last_id = self.__class__.objects.filter(~Q(reference_no=''),~Q(reference_no=None),is_external=False).order_by("-reference_no")[0].reference_no
                last_year = int(last_id[:8][4:])
                current_year = int(date.today().strftime("%Y"))

                letter = last_id[:3] + '/' +str(date.today().strftime("%Y")) + '/'
                number = int(last_id[9:])
                number = number + 1
                if current_year == last_year+1:
                    letter = last_id[:3] + '/' + str(date.today().strftime("%Y")) + '/'
                    number = 1
                   
                    self.reference_no = '{0}{1:07d}'.format(letter,number)
                self.reference_no = '{0}{1:07d}'.format(letter,number)
            
        super(self.__class__, self).save(*args, **kwargs)


class UserCompanyShares(models.Model):
    """
    Model for User Company Share details
    """
    user = models.ForeignKey(User, related_name='share_details',blank=True,null=True)
    isx_shares = models.IntegerField(blank=True, null=True, default=0)
    isx_share_to_sell = models.IntegerField(blank=True, null=True, default=0)
    lsx_shares = models.IntegerField(blank=True, null=True, default=0)
    lsx_share_to_sell = models.IntegerField(blank=True, null=True, default=0)
    project = models.ForeignKey(Project, related_name='share_details',null=True)

class FundInterestPay(models.Model):
    """
    Model for Project Fund Interest Pay to backer
    """
    backer_fund = models.ForeignKey(ProjectBackerFund, related_name='backer_fund',null=True)
    from_date = models.DateField(blank=True, null=True, auto_now_add=True)
    to_date = models.DateField(blank=True, null=True)
    amount_to_pay = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', blank=True, null=True)
    interest_rate = models.IntegerField(null=True)
    is_closed = models.BooleanField(
        _('Is Closed'),
        default=False,
    )
        