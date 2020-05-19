from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework.serializers import ValidationError
from rest_framework import serializers, fields
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueValidator
import json
from .models import (
    Question, Answer, Project, Task, TaskTag, TaskStatus, TaskRule, Milestone,
    AnswerImage, AnswerSpreadsheet, AnswerDiagram, TaskDocument ,  KeyVal , ProjectRegistrationType, AnswerDate
    ,AnswerMultiList, AnswerRadio, AnswerList, ProjectRegistrationPackage, PackageFeaturevalues, TaskAssignDetails
    ,ProjectLaunchType ,ProjectFundType , ProjectFund , PackageList, ProjectPackageDetails, AnswerPowerPoint,ToDoList, DependencyTask
    ,ProjectCompanyRole,NdaDetails,NdaHistoryDetails,AnswerSwot, EmployeeRatingDetails,PredefinedMilestone,NotarizationDetails,DocumentsToNotarisation,
    NotarizedDocuments,ProjectLaunch,Ratings,FinalProduct,ProjectBuyCompanyShare,Time,Notification, ProjectBackerFund, ProjectBackerLaunch,
    NdaToDocusign,ProductExpenses, WorkSession, Transactions, AnswerOcr, FundInterestPay
)
# ProjectEquityCrowdFunding,ProjectsLoanServices,ProjectNormalFunding,ProjectsP2P,ProjectsCompanyBuyOffer,ProjectBuyInCompanyRoll,ProjectSplitEquity
from .constants import DAYS_OF_WEEK,MONTHS_IN_YEAR
from accounts.serializers import UserProfileShortDataSerializer
from core.serializers import Base64ImageField, Base64FileField
from django.shortcuts import get_list_or_404, get_object_or_404
from actstream.models import Action
from rest_framework.response import Response
# import common
from rest_framework import status
from django.apps import apps
from .constants import (
    LOCATOR_YES_NO_CHOICES
)
from accounts.models import User
from collections import OrderedDict
from rest_framework.fields import Field
from django.conf import settings
from datetime import datetime,date,timedelta
from django.db.models import Q
from djmoney.money import Money
import pytz
from dateutil.relativedelta import relativedelta
#Temporary Comment changes related to Dowlla Payment
from projects.task import create_transactions


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
        # data = json.loads(data)
        amount = data.get('amount')
        currency = data.get('currency')

        if not amount :
            amount = 0.0
        if not currency :
            currency = "USD"

        try:
            obj = Money(amount, currency)
        except decimal.InvalidOperation:
            self.fail('not_a_number')

        if obj < Money('0', currency) and self.positive_only:
            self.fail('positive_only')
        return obj

class KeyValSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyVal
        fields = ('id', 'value')

class SubQuestionSerializer(serializers.ModelSerializer):

    vals = KeyValSerializer(required=False, many = True, read_only=True)
    option_list = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('group', 'id', 'order','vals', 'title', 'subtitle', 'question_type','registration_type',
                  'is_active', 'stage','model','option_list')

    def get_option_list(self, obj):
        new_list = []
        if obj.model:
            for i in apps.get_model(app_label='common', model_name=obj.model).objects.all():
                new_list.append(({'id':i.id,'title': i.title}))
        return new_list

class QuestionSerializer(serializers.ModelSerializer):

    vals = KeyValSerializer (required=False, many = True, read_only=True)
    option_list = serializers.SerializerMethodField()
    sub_question = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('group', 'id', 'order','vals', 'title', 'subtitle', 'question_type','registration_type',
                  'is_active', 'stage','model','option_list','sub_question',)

    def get_option_list(self, obj):
        new_list = []
        if obj.model:
            if obj.model == 'state':
                for i in apps.get_model(app_label='common', model_name=obj.model).objects.filter(country__title="United States").order_by('title'):
                    new_list.append(({'id':i.id,'title': i.title}))
            else:
                for i in apps.get_model(app_label='common', model_name=obj.model).objects.all():
                    new_list.append(({'id':i.id,'title': i.title}))
        return new_list

    def get_sub_question(self, obj):
        """
        Get current question sub_questions
        """
        qs = Question.objects.filter(parent_question=obj)
        return SubQuestionSerializer(qs, many=True).data

class RadioRelatedField(Field):
    def to_representation(self, value):
        if isinstance(value, KeyVal):
            serializer = KeyValSerializer(value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data.get('id')

    def to_internal_value(self, data):
        keyval_obj = KeyVal.objects.get(id=data)
        return keyval_obj

class OcrField(Field):
    def to_representation(self, obj):
        data = {'file_name': obj.name,
            'content': obj}
        return data

    def to_internal_value(self, data):
        return data

class AnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for project answers
    """
    project = serializers.ReadOnlyField(source='project_id')
    keyval = KeyVal()

    boolean_text = serializers.NullBooleanField()

    image = Base64ImageField(
        required=False, source='image.image', allow_null=True
    )
    spreadsheet = Base64FileField(
        required=False, source='spreadsheet.spreadsheet', allow_null=True
    )

    powerpoint = Base64FileField(
        required=False, source='powerpoint.powerpoint', allow_null=True
    )
    diagram = Base64ImageField(
        required=False, source='diagram.diagram', allow_null=True
    )
    model = serializers.CharField(
        required=False, source='list.model', allow_null=True
    )
    option_id = serializers.IntegerField(
        required=False, source='list.option_id', allow_null=True
    )
    selected_option = serializers.SerializerMethodField()

    date = serializers.DateField(
        required=False, source='date.date', allow_null=True
    )
    radio = RadioRelatedField(source='radio.radio',required=False, allow_null=True,)
    multilist = serializers.PrimaryKeyRelatedField(queryset=KeyVal.objects.all(),source='multilist.multilist', required=False, many=True, allow_null=True)
    swot_answer = serializers.JSONField(source='swot_answer.swot_answer', required=False, allow_null=True)
    productcompare_answer = serializers.JSONField(source='productcompare_answer.productcompare_answer', required=False, allow_null=True)

    # parent_answer = AnswerSerializer()
    ocr = OcrField(
        required=False, source='ocr.ocr', allow_null=True
    )

    class Meta:
        model = Answer

        fields = ('id', 'question', 'project', 'response_text', 'is_private','image', 'spreadsheet', 'diagram','boolean_text',
                 'date','radio','multilist', 'model','option_id','selected_option','parent_answer','powerpoint','swot_answer','ocr','productcompare_answer')

    def create(self, validated_data):
        model = None
        option_id = None
        image = validated_data.pop('image', None)
        spreadsheet = validated_data.pop('spreadsheet', None)
        powerpoint = validated_data.pop('powerpoint', None)
        diagram = validated_data.pop('diagram', None)
        list_data = validated_data.pop('list', None)
        date = validated_data.pop('date', None)
        radio = validated_data.pop('radio', None)
        multi = validated_data.pop('multilist', None)
        swot_answer = validated_data.pop('swot_answer', None)
        ocr = validated_data.pop('ocr', None)
        productcompare_answer = validated_data.pop('productcompare_answer', None)

        if list_data:
            model = list_data.get('model')
            option_id = list_data.get('option_id')

        answer, created = Answer.objects.update_or_create(
            question=validated_data.pop('question'),
            project_id=validated_data.pop('project_id'),
            defaults=validated_data
        )

        if swot_answer is not None and swot_answer['swot_answer'] is not None:
            AnswerSwot.objects.update_or_create(
                answer=answer, defaults={'swot_answer': swot_answer['swot_answer']}
            )

        if productcompare_answer is not None and productcompare_answer['productcompare_answer'] is not None:
            FinalProduct.objects.update_or_create(
                answer=answer, defaults={'productcompare_answer': productcompare_answer['productcompare_answer']}
            )

        if image is not None and image['image'] is not None:
            AnswerImage.objects.update_or_create(
                answer=answer, defaults={'image': image['image']}
            )

        if spreadsheet is not None and spreadsheet['spreadsheet'] is not None:
            AnswerSpreadsheet.objects.update_or_create(
                answer=answer,
                defaults={'spreadsheet': spreadsheet['spreadsheet']}
            )

        if powerpoint is not None and powerpoint['powerpoint'] is not None:
            AnswerPowerPoint.objects.update_or_create(
                answer=answer,
                defaults={'powerpoint': powerpoint['powerpoint']}
            )

        if diagram is not None and diagram['diagram'] is not None:
            AnswerDiagram.objects.update_or_create(
                answer=answer,
                defaults={'diagram': diagram['diagram']}
            )

        if option_id is not None:
            AnswerList.objects.update_or_create(
                answer=answer,
                defaults={'model': model,'option_id': option_id}
            )

        if date is not None:
            AnswerDate.objects.update_or_create(
                answer=answer,
                defaults={'date': date.get('date')}
            )

        if multi is not None:
            d, created = AnswerMultiList.objects.update_or_create(answer=answer)
            if multi.get('multilist'):
                for a in multi.get('multilist'):
                    d.multilist.add(a)
                    d.save()

        if radio is not None:
            AnswerRadio.objects.update_or_create(
                answer=answer,
                defaults={'radio': radio.get('radio')}
            )

        if ocr is not None and ocr['ocr'] is not None:
            AnswerOcr.objects.update_or_create(
                answer=answer,
                defaults={'ocr': ocr["ocr"].get("file_name")}
            )

        return answer

    def get_selected_option(self, obj):
        try:
            answer = AnswerList.objects.get(answer=obj)
            if answer.model and answer.option_id:
                selected_option = apps.get_model(app_label='common', model_name=answer.model).objects.get(id=answer.option_id)
                return selected_option.title
        except AnswerList.DoesNotExist:
            pass


class QuestionListSerializer(serializers.ModelSerializer):

    vals = KeyValSerializer(required=False, many=True)
    option_list = serializers.SerializerMethodField()
    sub_question = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('pk', 'order', 'title', 'subtitle', 'question_type','registration_type','vals',
                  'is_active', 'group', 'stage','model','option_list','sub_question')


    def get_option_list(self, obj):
        new_list = []
        if obj.model:
            for i in apps.get_model(app_label='common', model_name=obj.model).objects.all():
                new_list.append(({'id':i.id,'title': i.title}))
        return new_list

    def get_sub_question(self, obj):
        """
        Get current question sub_questions
        """
        return Question.objects.filter(parent_question=obj)\
                            .values('group', 'id', 'order','vals', 'title', 'subtitle', 'question_type','registration_type',
                            'is_active', 'stage','model')


class ProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for project list viewset
    """
    progress = serializers.IntegerField(
        read_only=True, source='get_answers_progress'
    )

    class Meta:
        model = Project
        fields = ('id', 'title', 'stage', 'participants', 'date_start','date_end', 'status', 'registration_type', 'is_visible', 'progress', 'milestones','package','is_registered','show_nda','add_nda')

    def create(self, validated_data):
        instance = super().create(validated_data)
        predefined_milestone = PredefinedMilestone.objects.all()
        for premilestone in predefined_milestone:
             Milestone.objects.create(
                        project=instance,
                        title=premilestone.title,
                        description=premilestone.description,
                        order=premilestone.order,
                        date_start=timezone.now(),
                        date_end=timezone.now()+timedelta(days=30),
                        icon_name =premilestone.icon_name,
                        icon_category =premilestone.icon_category
                    )
        return instance


class ProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for project detail viewset
    """
    owner = serializers.SerializerMethodField()
    progress = serializers.IntegerField(
        read_only=True, source='get_answers_progress'
    )
    launch_type = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'stage', 'participants', 'date_start',
                  'date_end', 'status', 'registration_type', 'is_visible', 'progress', 'milestones',
                  'package','is_registered','show_nda','owner','add_nda','launch_type')

    def get_owner(self, obj):
        return UserProfileShortDataSerializer(obj.owner.userprofile).data

    def get_launch_type(self, obj):
        launch_obj = obj.project_launch.all().first()
        if launch_obj:
            return launch_obj.launch.id
        


class ProjectPublishedSerializer(serializers.ModelSerializer):
    """
    Serializer for published projects
    """
    owner = serializers.SerializerMethodField()
    progress = serializers.IntegerField(
        read_only=True, source='get_answers_progress'
    )

    class Meta:
        model = Project
        fields = ('id', 'title', 'participants', 'date_start', 'date_end',
                  'stage', 'progress', 'milestones', 'owner', 'show_nda','add_nda')

    def get_owner(self, obj):
        return UserProfileShortDataSerializer(obj.owner.userprofile).data



class GanttProjectsSerializer(serializers.ModelSerializer):
    """
    Serializer for gantt projects list
    """
    class Meta:
        model = Project
        fields = '__all__'



class TaskTagSerializer(serializers.ModelSerializer):
    """
    Serializer for task tags.
    Use with TaskSerializer
    """
    class Meta:
        model = TaskTag
        fields = '__all__'


class TaskRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for task rules.
    Use with TaskSerializer
    """
    class Meta:
        model = TaskRule
        fields = ('title',)

class TaskDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks documents
    """
    document = serializers.FileField()
    class Meta:
        model = TaskDocument
        fields = '__all__'


    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['document'] = '{}?f={}'.format(
            reverse('task_document_proxy'), str(instance.document)
        )
        return representation

    def validate_task(self, value):
        if value.owner != self.context['request'].user:
            if self.context['request'].user not in value.milestone.project.participants.all():
                raise serializers.ValidationError('You can\'t do it')
        return value

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Code for get Task-DependentTask
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class DependentTask(serializers.ModelSerializer):
        """
        Serializer for Dependency Task.
        Use with TaskSerializer
        """
        class Meta:
            model = DependencyTask
            fields = '__all__'
            depth = 1


class WorkSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for Work Session
    """
    project_title = serializers.SerializerMethodField()
    goal_title = serializers.SerializerMethodField()
    task_title = serializers.SerializerMethodField()

    class Meta:
        model = WorkSession
        fields = ('id','start_datetime','end_datetime','loggedin_hours','task','employee','project_title','goal_title','task_title')


    def create(self, validated_data):
        obj = WorkSession.objects.filter(employee=self.context['request'].user,loggedin_hours=None).first()
        if obj:
            raise serializers.ValidationError('You have already start the session. If you want to create new session then first end the existing session.')
        instance = super().create(validated_data)
        # instance.start_datetime = timezone.now()
        work_obj = WorkSession.objects.filter(employee=self.context['request'].user,task=self.context['request'].data['task']).first()
        if work_obj:
            task_obj = Task.objects.get(id=self.context['request'].data['task'],participants=self.context['request'].user)
            parenttask_obj = Task.objects.get(id=task_obj.parent_task.id)
            taskstatus_obj = TaskStatus.objects.get(id =2)
            parenttask_obj.status=taskstatus_obj
            parenttask_obj.save()
        return instance

    def update(self, instance, validated_data):
        if validated_data.get("loggedin_hours"):
            time = validated_data.get("loggedin_hours").split(':')
            end_datetime = instance.start_datetime + timedelta(hours=int(time[0]),minutes=int(time[1]))
            instance.end_datetime = end_datetime

        instance = super().update(instance, validated_data)
        return instance

    def get_project_title(self, obj):
        """
        Get project title
        """
        return obj.task.milestone.project.title

    def get_goal_title(self, obj):
        """
        Get goal title
        """
        if obj.task.parent_task:
            return obj.task.parent_task.title

    def get_task_title(self, obj):
        """
        Get task title
        """
        return obj.task.title



class DependentTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task
    """
    tags = TaskTagSerializer(many=True, required=False)
    rules = TaskRuleSerializer(many=True, required=False)
    documents = TaskDocumentSerializer(many=True, read_only=True)
    dependency_task = DependentTask(many=True,required=False)
    subtasks = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()
    active_session = serializers.SerializerMethodField()
    process_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ('id', 'milestone', 'title', 'description', 'status',
                  'assignee', 'participants', 'due_date', 'tags', 'order',
                  'complete_percent', 'rules', 'parent_task', 'subtasks',
                  'documents','dependency_task','is_complete','active_session','process_percentage')
        read_only_fields = ('subtasks',)
        extra_kwargs = {'milestone': {'allow_null': False, 'required': True}}

    def get_is_complete(self, obj):
        """
        Get current user task completion status
        """
        assign_details = TaskAssignDetails.objects.filter(task=obj,employee=self.context['request'].user).first()
        if assign_details:
            return assign_details.is_complete
        else:
            return False

    def get_active_session(self, obj):
        """
        Get current user task active session
        """
        res = WorkSession.objects.filter(loggedin_hours=None,employee=self.context['request'].user).first()
        if res:
            return WorkSessionSerializer(res).data

    def get_subtasks(self, obj):
        """
        Get current task subtasks
        """
        return Task.objects.filter(Q(participants=self.context['request'].user)| Q(owner=self.context['request'].user,milestone__project=obj.milestone.project),parent_task=obj)\
                           .values_list('id', flat=True).order_by('-id').distinct()

    def get_process_percentage(self,obj):
        """
        Percentage of individual process
        """
        p_completed_count = TaskAssignDetails.objects.filter(task=obj,is_complete=True).count()
        p_total_count = TaskAssignDetails.objects.filter(task_id=obj).count()
        if p_total_count:
            p_percentage = (p_completed_count / p_total_count) * 100
            return p_percentage

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#Code for get Task-DependentTask
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class DependencyTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Dependency Task.
    Use with TaskSerializer
    """

    class Meta:
        model = DependencyTask
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task
    """
    tags = TaskTagSerializer(many=True, required=False)
    rules = TaskRuleSerializer(many=True, required=False)
    documents = TaskDocumentSerializer(many=True, read_only=True)
    dependency_task = DependencyTaskSerializer(many=True,required=False)
    parent_dependent_tasks = serializers.SerializerMethodField()
    goal_percentage = serializers.SerializerMethodField()
    #creator_is_complete = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Task
        fields = ('id', 'milestone', 'title', 'description', 'status',
                  'assignee', 'participants', 'due_date', 'tags', 'order',
                  'complete_percent', 'rules', 'parent_task', 'subtasks',
                  'documents','dependency_task','is_complete', 'parent_dependent_tasks','goal_percentage')#,'is_reassign','is_creator')
        read_only_fields = ('subtasks',)

        extra_kwargs = {'milestone': {'allow_null': False, 'required': True}}

    def get_goal_percentage(self,obj):
        """
        Percentage of process regarding project milestones
        """
        # TODO: optimize queryset
        subtask_count = Task.objects.filter(parent_task__id=obj.id).count()
        subtask_obj = Task.objects.filter(parent_task__id=obj.id).order_by('id')
        if subtask_count:
            total_subtask = 100 / subtask_count
        total = 0
        task_list = []
        for task in subtask_obj:
            task_list.append(task.is_complete)
            p_completed_count = TaskAssignDetails.objects.filter(task_id=task,is_complete=True).count()
            p_total_count = TaskAssignDetails.objects.filter(task_id=task).count()
            if p_total_count:
                p_percentage = (p_completed_count / p_total_count) * 100
                final_calculation = (total_subtask / 100) * p_percentage
                total = total + final_calculation



        if task_list and False not in task_list:
            taskstatus_obj = TaskStatus.objects.get(id =5)
            obj.status= taskstatus_obj
            obj.is_complete = True
            obj.save()
 
        elif total>20 and total<95:
            taskstatus_obj = TaskStatus.objects.get(id =3)
            obj.status=taskstatus_obj
            obj.save()

        elif total > 95 and  total == 100:
            taskstatus_obj = TaskStatus.objects.get(id =4)
            obj.status=taskstatus_obj
            obj.is_complete= False
            obj.save()

        return total

    def get_parent_dependent_tasks(self, obj):
        """
        Get current task subtasks
        """
        dependent_task_list = DependencyTask.objects.filter(task=obj).values_list('id',flat=True).order_by('-id').distinct()
        parent_dependent_tasks = Task.objects.filter(dependency_task__id__in=dependent_task_list).values('id','title').order_by('-id').distinct()
        return parent_dependent_tasks

    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError('Please set title')
        return value

    def validate_project(self, value):
        if self.context['request'].user != value.owner:
            raise serializers.ValidationError('You haven\'t access for it')
        return value


    def create(self, validated_data):
        task = validated_data.pop('task', None)
        tags_data = validated_data.pop('tags', None)
        dependent_tasks_data = validated_data.pop('dependency_task',None)
        rules_data = validated_data.pop('rules', None)
        participants_data = validated_data.get('participants', None)
        instance = super().create(validated_data)

        dependent_tasks = []
        if dependent_tasks_data:
            for task in dependent_tasks_data:
                dependent_tasks.append(DependencyTask(
                    milestone = task['milestone'],
                    task = task['task'],
                ))
            task_created = DependencyTask.objects.bulk_create(dependent_tasks)
            instance.dependency_task.add(*task_created)

        if tags_data is not None:
            tags = []
            for tag in tags_data:
                p, created = TaskTag.objects.get_or_create(title=tag['title'])
                tags.append(p)

            instance.tags.add(*tags)

        if rules_data is not None:
            s = TaskRuleSerializer(data=rules_data, many=True)
            s.is_valid(raise_exception=True)
            s.save(task=instance)

        if participants_data is not None:
            instance.milestone.project.participants.add(*participants_data)
            instance.milestone.project.save()
            for participant in participants_data:
                p, created = TaskAssignDetails.objects.get_or_create(task=instance,employee=participant)

        return instance


    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        rules_data = validated_data.pop('rules', None)
        dependent_tasks_data = validated_data.pop('dependency_task',None)
        participants_data = validated_data.get('participants', None)
        is_complete = validated_data.pop('is_complete', False)
        is_reassign = validated_data.pop('is_reassign', False)
        instance = super().update(instance, validated_data)

        dependent_tasks=[]
        def add_dependency(self,dependent_tasks_data):
            for task in dependent_tasks_data:
                    dependent_tasks.append(DependencyTask(
                        milestone = task['milestone'],
                        task = task['task'],
                    ))
            task_created = DependencyTask.objects.bulk_create(dependent_tasks)
            instance.dependency_task.add(*task_created)
            return Response(status=status.HTTP_201_CREATED)

        if dependent_tasks_data:
            for child_data in dependent_tasks_data:
                milestone_obj = child_data.get("milestone")
                task_obj = child_data.get("task")
                instance_task = instance.id
                direct = Task.objects.filter(id=instance_task,dependency_task__milestone = milestone_obj.id, dependency_task__task = task_obj.id)
                reverse = Task.objects.filter(id=instance_task,dependency_task__milestone = task_obj.id, dependency_task__task = milestone_obj.id)
                if direct.exists() or reverse.exists():
                    raise ValidationError({"milestone":"Relation Already Exist"})
                else:
                    add_dependency(self,dependent_tasks_data)



        if tags_data is not None:
            tags = []
            for tag in tags_data:
                p, created = TaskTag.objects.get_or_create(title=tag['title'])
                tags.append(p)

            instance.tags.add(*tags)
            remove_tags = instance.tags.exclude(pk__in=[x.pk for x in tags])
            if remove_tags:
                instance.tags.remove(*remove_tags)

        if rules_data is not None:
            s = TaskRuleSerializer(data=rules_data, many=True)
            s.is_valid(raise_exception=True)

            rule_ids = []
            for rule in rules_data:
                p, created = TaskRule.objects.get_or_create(
                    task=instance, title=rule['title']
                )
                rule_ids.append(p.pk)
            TaskRule.objects.filter(task=instance)\
                            .exclude(pk__in=rule_ids)\
                            .delete()

        if participants_data is not None:
            instance.milestone.project.participants.add(*participants_data)
            instance.milestone.project.save()
            for participant in participants_data:
                p, created = TaskAssignDetails.objects.get_or_create(task=instance,employee=participant)

        # if self.context['request'].data['is_creator']:
        if self.context['request'].user.userprofile.role == "creator":
            if is_complete:
                obj = Task.objects.filter(id=instance.id).first()
                if obj:
                    obj.is_complete = True
                    obj.save()

        if self.context['request'].user.userprofile.role == "employee":
            if is_complete:
                obj = TaskAssignDetails.objects.filter(task=instance,employee=self.context['request'].user).first()
                if obj:
                    obj.is_complete = True
                    obj.completed_date = date.today()
                    obj.save()

        if is_reassign:
            obj = TaskAssignDetails.objects.filter(task=instance,employee=self.context['request'].user).first()
            if obj:
                obj.is_complete = False
                obj.status = 'reassign'
                obj.reassign_completed_date = date.today()
                obj.completed_date = None
                obj.save() 
        return instance

    def put(self, request, pk, format=None):
        dependent_tasks_data = validated_data.pop('dependency_task',None)

        snippet = self.get_object(pk)
        serializer = SnippetSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class FeedSerializer(serializers.ModelSerializer):
    """
    Serializer for project feeds
    """
    actor = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = ('id', 'actor', 'message', 'timestamp')

    def get_actor(self, obj):
        return UserProfileShortDataSerializer(obj.actor.userprofile).data

    def get_message(self, obj):
        ctx = {
            'verb': obj.verb,
            'action_object': obj.action_object,
            'target': obj.target
        }
        if obj.target:
            if obj.action_object:
                return '%(verb)s %(action_object)s on %(target)s' % ctx
            return '%(verb)s %(target)s' % ctx
        if obj.action_object:
            return '%(verb)s %(action_object)s' % ctx
        return '%(verb)s' % ctx


class ProcessesSerializer(serializers.ModelSerializer):
    """
    Serializer for project processes (tasks)
    """
    message = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ('id', 'message', 'timestamp')

    def get_message(self, obj):
        return obj.title

    def get_timestamp(self, obj):
        return obj.due_date


class ProjectActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for project activity
    """
    feed = serializers.SerializerMethodField()
    processes = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'feed', 'processes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.answer_ct = ContentType.objects.get_for_model(Answer)
        self.task_ct = ContentType.objects.get_for_model(Task)

    def get_feed(self, obj):
        """
        Get current project feeds
        """
        return FeedSerializer(
            obj.target_actions.filter(
                action_object_content_type=self.answer_ct
            ).order_by('-pk')[:3], many=True
        ).data

    def get_processes(self, obj):
        """
        Get current project processes
        """
        return ProcessesSerializer(
            Task.objects.filter(
                milestone__project=obj,
                due_date__gte=timezone.now(),
                parent_task__isnull=False
            ).order_by('due_date')[:3],
            many=True
        ).data

#lists all the activities in project
class AllProjectActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for project activity
    """
    feed = serializers.SerializerMethodField()
    processes = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'feed', 'processes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.answer_ct = ContentType.objects.get_for_model(Answer)
        self.task_ct = ContentType.objects.get_for_model(Task)

    def get_feed(self, obj):
        """
        Get current project feeds
        """

        return FeedSerializer(
            obj.target_actions.filter(
                action_object_content_type=self.answer_ct
            ).order_by('-pk'), many=True
        ).data

    def get_processes(self, obj):
        """
        Get current project processes
        """
        return ProcessesSerializer(
            Task.objects.filter(
                milestone__project=obj,
                due_date__gte=timezone.now(),
                parent_task__isnull=False
            ).order_by('due_date'),many=True
        ).data

class TaskStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks statuses
    """
    class Meta:
        model = TaskStatus
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    """
    Serializer for project milestones
    """
    tasks = serializers.SerializerMethodField()
    place_it_after = serializers.SerializerMethodField()
   
    class Meta:
        model = Milestone
        fields = ('id', 'title', 'description', 'date_start','date_end','is_milestone_in_startup_stage','tasks','project','icon_name','order','icon_category','place_it_after')

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs.get('title'):
            raise serializers.ValidationError('Please set title')
        if not attrs.get('date_start'):
            raise serializers.ValidationError('Please set start date')
        if not attrs.get('date_end'):
            raise serializers.ValidationError('Please set end date')
        if attrs.get('date_start') and attrs.get('date_end'):
            if attrs.get('date_end') < attrs.get('date_start'):
                raise serializers.ValidationError('Please select start date less than end date')
        # if not attrs.get('order'):
        #     raise serializers.ValidationError('Please set order')
        return attrs

    #################### Temproray Commented Code #########################################
    def create(self, validated_data):
        order = validated_data.pop('order', None)
        milestone_order = Milestone.objects.get(id=self.context['request'].data['place_it_after'])
        order_no = milestone_order.order
        order =  order_no + 1
        milestone = self.Meta.model(**validated_data)
        milestone.order = order
        milestone.save()
        milestone_list = []

        order_data = Milestone.objects.filter(~Q(id = milestone.id),Q(order__gte = milestone.order),project=self.context['request'].data['project'])
        for mile in order_data:
            mile_obj = Milestone.objects.get(id=mile.id)
            mile_obj.order = mile_obj.order +1
            mile_obj.save()
            milestone_list.append(mile_obj)

        return milestone

    def update(self, instance, validated_data):
        order = validated_data.pop('order', None)
        instance = super().update(instance, validated_data)

        if self.context['request'].data['isPlaceAfterChanged'] == True:
            milestone_order = Milestone.objects.get(id=self.context['request'].data['place_it_after'])
            order_no = milestone_order.order
            order =  order_no + 1
            instance.order = order
            instance.save()
            order_data = Milestone.objects.filter(~Q(id = instance.id),Q(order__gte = instance.order),project=self.context['request'].data['project'])
            for mile in order_data:
                mile_obj = Milestone.objects.get(id=mile.id)
                mile_obj.order = mile_obj.order +1 
                mile_obj.save()

        return instance

    def get_tasks(self, obj):
        return TaskSerializer(
            obj.milestone_tasks.filter(parent_task__isnull=True), many=True
        ).data

    def get_place_it_after(self, obj):
        milestones =  Milestone.objects.filter(project=obj.project)
        for i in milestones:
            if i.order == (obj.order-1):
                return i.id

class PredefinedMilestoneSerializer(serializers.ModelSerializer):
    """
    Predefined Templates for Milestone
    """
    class Meta:
        model = PredefinedMilestone
        fields = '__all__'

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs.get('title'):
            raise serializers.ValidationError('Please set title')
        if not attrs.get('order'):
            raise serializers.ValidationError('Please set order')
        return attrs

class ProjectTasksScopeSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks and subtasks.
    Use with ProjectMilestonesScopeSerializer
    """
    subtasks = serializers.SerializerMethodField()
    goal_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ('id', 'title','goal_percentage','order', 'subtasks')#'goal_count',

    def get_subtasks(self, obj):
        """
        Get current task subtasks
        """
        return Task.objects.filter(Q(participants=self.context['request'].user)| Q(owner=self.context['request'].user,milestone__project=obj.milestone.project),parent_task=obj)\
                           .values('id', 'title', 'order').order_by('-id').distinct()

    def get_goal_percentage(self,obj):
        """
        Percentage of process regarding project milestones
        """
        # TODO: optimize queryset
        task_count = Task.objects.filter(parent_task__isnull=True,milestone=obj.milestone).count()
        subtask_count = Task.objects.filter(parent_task__id=obj.id).count()

        subtask_obj = Task.objects.filter(parent_task__id=obj.id).order_by('id')
        if subtask_count:
            total_subtask = 100 / subtask_count
        total = 0
        for task in subtask_obj:
            p_completed_count = TaskAssignDetails.objects.filter(task_id=task,is_complete=True).count()
            p_total_count = TaskAssignDetails.objects.filter(task_id=task).count()
            if p_total_count:
                p_percentage = (p_completed_count / p_total_count) * 100
                final_calculation = (total_subtask / 100) * p_percentage
                total = total + final_calculation

        return total

class ProjectMilestonesScopeSerializer(serializers.ModelSerializer):
    """
    Serializer for milestones-tasks-subtasks
    """
    tasks = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    

    class Meta:
        model = Milestone
        fields = ('id', 'project', 'title', 'description', 'date_start',
                  'date_end','is_milestone_in_startup_stage', 'tasks','order','icon_name','icon_category','progress')

    def get_tasks(self, obj):
        """
        Get current milestone tasks
        """
        qs = Task.objects.filter(milestone=obj, parent_task__isnull=True)
        tasks = []
        res = ProjectTasksScopeSerializer(qs, many=True, context=self.context).data
        if self.context['request'].user.userprofile.role == "employee":
            for i in res:
                if i['subtasks'].exists():
                    tasks.append(i)
            return tasks
        else:
            return ProjectTasksScopeSerializer(qs, many=True, context=self.context).data

    def get_progress(self,obj):
        """
        Percentage of milestone based on goal and their process
        """
        milestone_total=0
        task_count = Task.objects.filter(parent_task__isnull=True,milestone=obj).count()
        if task_count:
            total_task = 100 / task_count
        task_obj = Task.objects.filter(parent_task__isnull=True,milestone=obj)
        for task in task_obj:
            subtask_count = Task.objects.filter(parent_task__id=task.id).count()
            subtask_obj = Task.objects.filter(parent_task__id=task.id).order_by('id')
            if subtask_count:
                total_subtask = 100 / subtask_count
                for task in subtask_obj:
                    p_completed_count = TaskAssignDetails.objects.filter(task_id=task,is_complete=True).count()
                    p_total_count = TaskAssignDetails.objects.filter(task_id=task).count()
                    if p_total_count:
                        p_percentage = (p_completed_count / p_total_count) * 100
                        final_calculation = (total_subtask / 100) * p_percentage
                        #total = total + final_calculation
                        milestone_cal = (total_task/100) * final_calculation
                        milestone_total =  milestone_total + milestone_cal

        return milestone_total

class RegistrationListSerializer(serializers.ModelSerializer):
    """
    Serializer for Registration Type
    """

    class Meta:
        model = ProjectRegistrationType
        fields = ('id', 'title', 'amount','description','is_active')


class PackageFeaturevaluesSerializer(serializers.ModelSerializer):
    feature = serializers.SerializerMethodField()
    feature_id = serializers.SerializerMethodField()

    class Meta:
        model = PackageFeaturevalues
        fields = ('feature_id','feature','feature_value_type','value','is_available')

    def get_feature_id(self, obj):
        if obj.feature:
            return obj.feature.id

    def get_feature(self, obj):
        if obj.feature:
            return obj.feature.title

class RegistrationPackageSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = ProjectRegistrationPackage
        fields = ('id', 'title', 'description','amount','registration_type','is_active','features')

    def get_features(self, obj):

        serializer = PackageFeaturevaluesSerializer(
            PackageFeaturevalues.objects.filter(registration_package=obj.id), many=True
        )
        return serializer.data


class EmployeeProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for employee task
    """
    # project = serializers.SerializerMethodField()
    goal = serializers.SerializerMethodField()
    process = serializers.SerializerMethodField()
    date_start = serializers.SerializerMethodField()
    date_end = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'participants', 'date_start',
                  'date_end', 'goal','process','owner')  #'milestones'


    def get_goal(self, obj):
        goal = ''
        milestones = MilestoneSerializer(obj.milestones, many=True).data
        if milestones:
            if milestones[0].get('tasks'):
                goal = milestones[0].get('tasks')[0].get('title')
        return goal

    def get_process(self, obj):
        process = ''
        milestones = MilestoneSerializer(obj.milestones, many=True).data
        if milestones:
            if milestones[0].get('tasks'):
                goal = milestones[0].get('tasks')[0]
                if goal.get('subtasks'):
                    process = Task.objects.get(id=milestones[0].get('tasks')[0].get('subtasks')[0])
                    process = process.title
        return process

    def get_date_start(self, obj):
        date_start = ''
        milestones = MilestoneSerializer(obj.milestones, many=True).data
        date_start_list = [m.get('date_start') for m in milestones]
        if min(date_start_list):
            date_start= datetime.strptime(min(date_start_list).split('T')[0],'%Y-%m-%d').strftime('%B %d, %Y')
        return date_start

    def get_date_end(self, obj):
        date_end = ''
        milestones = MilestoneSerializer(obj.milestones, many=True).data
        date_end_list = [m.get('date_end') for m in milestones]
        if max(date_end_list):
            date_end = datetime.strptime(max(date_end_list).split('T')[0],'%Y-%m-%d').strftime('%B %d, %Y')
        return date_end

    def get_owner(self, obj):
        return UserProfileShortDataSerializer(obj.owner.userprofile).data

class LaunchListSerializer(serializers.ModelSerializer):
    """
    Serializer for Launch Type
    """
    class Meta:
        model = ProjectLaunchType
        fields = ('id', 'title','description','is_active')

class ProjectFundTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for Fund Type
    """
    class Meta:
        model = ProjectFundType
        fields = ('id', 'title','description','terms_condition','is_active')

class ProjectCompanyRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for company role
    """
    class Meta:
        model = ProjectCompanyRole
        fields = ('id','title','description')

class ProjectBuyCompanyShareSerializer(serializers.ModelSerializer):
    """
    Serializer for Project Buy Company Share
    """
    amount = MoneyField(required=False, allow_null=True,)
    roleString = serializers.SerializerMethodField()
    sold = serializers.SerializerMethodField()

    class Meta:
        model = ProjectBuyCompanyShare
        fields = ('id','amount','percentage','role','roleString','project_fund','project_backer_fund','sold')

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs.get('amount'):
            raise serializers.ValidationError('Please set amount')
        if not attrs.get('percentage'):
            raise serializers.ValidationError('Please set percentage')
        if not attrs.get('role'):
            raise serializers.ValidationError('Please set role')
        return attrs

    def get_roleString(self, obj):
        return obj.role.title

    def get_sold(self, obj):
        if obj.project_backer_fund:
            return True
        else:
            return False

class TransactionsSerializer(serializers.ModelSerializer):
    """
    Serializer for Transactions
    """
    amount = MoneyField(required=False, allow_null=True,)
    bank_name = serializers.SerializerMethodField()

    class Meta:
        model = Transactions
        fields = ('id', 'user', 'bank_account','bank_name', 'reference_no', 'create_datetime', 'amount', 'remark', 'mode','account_no','status','is_external')

    def get_bank_name(self, obj):
        if obj.bank_account:
            if obj.bank_account.bank:
                return obj.bank_account.bank.title

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('amount') and attrs.get('mode')=="withdrawal" and attrs.get("is_external"):
            wallet_amount = Transactions.get_wallet_amount(self,user=self.context['request'].user)
            if wallet_amount < attrs.get('amount').amount:
                raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')
        return attrs

    ###############################Temporary Comment changes related to Dowlla Payment##############################
    def create(self, validated_data):
        amount = validated_data.get('amount', None)
        mode = validated_data.get('mode', None)
        bank_account = validated_data.get('bank_account', None)

        data = {'amount':amount,'mode':mode,'bank_account':bank_account}

        transaction_status = create_transactions(data)
        
        instance = super().create(validated_data)
        transaction_obj = Transactions.objects.get(id=instance.id)
        transaction_obj.status = transaction_status
        transaction_obj.save()

        return instance

class ProjectFundSerializer(serializers.ModelSerializer):
    """
    Serializer for Project Fund Form
    """
    min_target_offering_amt = MoneyField(required=False, allow_null=True,)
    price_security = MoneyField(required=False, allow_null=True,)
    loan_amount = MoneyField(required=False, allow_null=True,)
    min_peer_amt = MoneyField(required=False, allow_null=True,)
    current_valuation = MoneyField(required=False, allow_null=True,)
    company_shares = ProjectBuyCompanyShareSerializer(required=False, many=True)
    sold = serializers.SerializerMethodField()

    class Meta:
        model = ProjectFund
        fields = ('id','project','fund','owner','terms_condition','min_target_offering_amt','amount_equity','due_by','return_form','price_security',
                'payment_type','loan_amount','interest_rate','min_peer_amt','current_valuation','organization_details','company_shares','is_confirmed','sold')

    # (1,'Equality Crowdfunding/exchangeable equality')
    # (2,'Debt financing / corporate bond long term debt instruments')
    # (3,'Loan services')
    # (4,'Normal Crowdfunding')
    # (5,'p2p loan lend')
    # (6,'Company Buy Offer')
    # (7,'Offer buy-in for shares for a role in a company')
    # (8,'Split equality with new funders')
    # (9,'Initial bond offering')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('project') and attrs.get('project').is_registered == False and attrs.get("fund").id not in [4,5]:
            raise serializers.ValidationError('This funding requires your idea to complete the company registration phase.')
        if not attrs.get('fund'):
            raise serializers.ValidationError('Please set fund')
        if not attrs.get('project'):
            raise serializers.ValidationError('Please set project')

        if attrs.get("fund") and attrs.get("fund").id in [1] :
            if not attrs.get('amount_equity'):
                raise serializers.ValidationError('Please set Equity amount')
        if attrs.get("fund") and attrs.get("fund").id in [1,4] :
            if not attrs.get('min_target_offering_amt'):
                raise serializers.ValidationError('Please set min targetting amount')
            if not attrs.get('due_by'):
                raise serializers.ValidationError('Please set due date')
            if not attrs.get('return_form'):
                raise serializers.ValidationError('Please set form return')
            if not attrs.get('price_security'):
                raise serializers.ValidationError('Please set price security')
        elif attrs.get("fund") and attrs.get("fund").id in [3,5] :
            if not attrs.get('payment_type'):
                raise serializers.ValidationError('Please set type of payment')
            if not attrs.get('loan_amount'):
                raise serializers.ValidationError('Please set Loan amount')
            if not attrs.get('interest_rate'):
                raise serializers.ValidationError('Please set Interest Rate')
        elif attrs.get("fund") and attrs.get("fund").id == 5 :
            if not attrs.get('min_peer_amt'):
                raise serializers.ValidationError('Please set min amount for peer')
        elif attrs.get("fund") and attrs.get("fund").id == 6 :
            if not attrs.get('current_valuation'):
                raise serializers.ValidationError('Please set current valuation')
            if not attrs.get('organization_details'):
                raise serializers.ValidationError('Please set organization details')
        return attrs

    def update(self, instance, validated_data):
        company_shares_data = validated_data.pop('company_shares', None)
        instance = super().update(instance, validated_data)
        if company_shares_data is not None:
            data = []
            for i in company_shares_data:
                share_obj = ProjectBuyCompanyShare.objects.filter(role = i['role'],project_fund=instance).first()
                share = {
                        "amount": {'amount': float(i['amount'].amount),'currency': str(i['amount'].currency)},
                        "percentage": i['percentage'],
                        "role": i['role'].id
                    }
                if share_obj:
                    s = ProjectBuyCompanyShareSerializer(share_obj, data=share, partial=True)
                    s.is_valid(raise_exception=True)
                    s.save()
                else:
                    data.append(share)
            s = ProjectBuyCompanyShareSerializer(data=data, many=True)
            s.is_valid(raise_exception=True)
            s.save(project_fund= instance)
        return instance

    def create(self, validated_data):
        company_shares_data = validated_data.pop('company_shares', None)
        instance = super().create(validated_data)
        if company_shares_data is not None:
            data = []
            for i in company_shares_data:
                share = {
                    "amount":{'amount': float(i['amount'].amount),'currency': str(i['amount'].currency)},
                    "percentage": i['percentage'],
                    "role": i['role'].id
                }
                data.append(share)
            s = ProjectBuyCompanyShareSerializer(data=data, many=True)
            s.is_valid(raise_exception=True)
            s.save(project_fund= instance)

        return instance

    def get_sold(self, obj):
        if obj.fund.id == 6:
            project_backer_fund = ProjectBackerFund.objects.filter(fund=obj)
            if project_backer_fund.exists():
                return True
            else:
                return False
        else:
            return False

class ProjectBackerFundSerializer(serializers.ModelSerializer):
    """
    Serializer for Project Backer Fund
    """
    sanction_amount = MoneyField(required=False, allow_null=True,)
    loan_amount = MoneyField(required=False, allow_null=True,)
    min_peer_amt = MoneyField(required=False, allow_null=True,)
    company_shares_backer = ProjectBuyCompanyShareSerializer(required=False, many=True)

    class Meta:
        model = ProjectBackerFund
        fields = ('id','fund','backer','quantity','return_form', 'payment_type', 'sanction_amount','loan_amount','interest_rate','min_peer_amt', 'company_shares_backer', 'create_date', 'is_closed')

    def create(self, validated_data):
        company_shares_backer_data = validated_data.pop('company_shares_backer', None)
        if validated_data.get("fund").fund.id in [3,5]:
            if validated_data.get("payment_type") == "monthly":
                validated_data.update({'next_interest_payable_date':date.today() + relativedelta(months=1)})
            elif validated_data.get("payment_type") == "quarterly":
                validated_data.update({'next_interest_payable_date':date.today() + relativedelta(months=3)})
            elif validated_data.get("payment_type") == "yearly":
                validated_data.update({'next_interest_payable_date':date.today() + relativedelta(months=12)})

        instance = super().create(validated_data)

        amount = 0
        if  validated_data.get("fund").fund.id in [1,4]:
            amount = validated_data.get("quantity") * validated_data.get("fund").price_security.amount
        elif  validated_data.get("fund").fund.id in [3,5]:
            amount = validated_data.get("sanction_amount").amount
        elif validated_data.get("fund").fund.id in [7,8]:
            amount = sum([i.get("amount").amount for i in company_shares_backer_data])
        else:
            amount = validated_data.get("fund").current_valuation.amount

        data = [{
                    "reference_no": "",
                    "remark": "Project fund",
                    "mode": "withdrawal",
                    "status": "success",
                    "amount":{"amount":amount,"currency":"USD"},
                    "user": self.context['request'].user.id
                },
                {
                    "reference_no": "",
                    "remark": "Project fund",
                    "mode": "deposite",
                    "status": "success",
                    "amount":{"amount":amount,"currency":"USD"},
                    "user": 1 if validated_data.get("fund").fund.id in [1,4] else validated_data.get('fund').owner.id
                }
            ]
        s = TransactionsSerializer(data=data,many=True)
        s.is_valid(raise_exception=True)
        s.save(project=validated_data.get('fund').project)

        if company_shares_backer_data is not None:
            for i in company_shares_backer_data:
                share_obj = ProjectBuyCompanyShare.objects.filter(role__id = i['role'].id,project_fund=validated_data.get('fund')).first()
                if share_obj:
                    share_obj.project_backer_fund = instance
                    share_obj.save()

        return instance

    def validate(self, attrs):
        attrs = super().validate(attrs)
        company_shares_backer_data = attrs.get('company_shares_backer', None)
        if company_shares_backer_data is not None:
            for i in company_shares_backer_data:
                share_obj = ProjectBuyCompanyShare.objects.filter(role__id = i['role'].id,project_fund=attrs.get('fund')).first()
                if share_obj:
                    if share_obj.project_backer_fund == None:
                        pass
                    else:
                        raise serializers.ValidationError(i['role'].title + ' role of company is not available.')
        if attrs.get('fund'):
            if attrs.get('fund').due_by:
                if attrs.get('fund').due_by < date.today():
                    raise serializers.ValidationError('Due date is expired.')
        if attrs.get('fund').fund.id == 6:
            project_backer_fund = ProjectBackerFund.objects.filter(fund=attrs.get('fund'))
            if project_backer_fund.exists():
                raise serializers.ValidationError(attrs.get('fund').fund.title + ' fund is not available.')
        return attrs

class ProjectBackerFundListSerializer(serializers.ModelSerializer):
    """
    Serializer for Project Backer Fund list viewset
    """
    fund_type = serializers.SerializerMethodField()
    funded_to = serializers.SerializerMethodField()
    funded_by = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    output = serializers.SerializerMethodField()
    funded_on = serializers.SerializerMethodField()
    due_on = serializers.SerializerMethodField()

    class Meta:
        model = ProjectBackerFund
        fields = ('fund_type','funded_to','funded_by','amount','output','funded_on','due_on')

    def get_fund_type(self, obj):
        """
        Get fund type
        """
        return obj.fund.fund.title

    def get_funded_to(self, obj):
        """
        Get Company name
        """
        return obj.fund.project.title

    def get_funded_by(self, obj):
        """
        Get backer name
        """
        return obj.backer.first_name + " " + obj.backer.last_name

    def get_funded_on(self, obj):
        """
        Get create fund date of backer
        """
        if obj.create_date:
            return obj.create_date.strftime('%d %B %Y')

    def get_due_on(self, obj):
        """
        Get due on date of fund
        """
        if obj.fund.due_by:
            return obj.fund.due_by.strftime('%d %B %Y')

    def get_output(self, obj):
        """
        Get output of fund
        """
        if obj.fund.fund.id in (1,4):
            return str(obj.quantity) + ' Equity'
        elif obj.fund.fund.id in (3,5):
            return str(obj.interest_rate) + '% Interest Rate'
        elif obj.fund.fund.id in (7,8):
            role_list = ','.join([i.role.title for i in obj.company_shares_backer.all()])
            return role_list

    def get_amount(self, obj):
        """
        Get amount fund
        """
        if obj.fund.fund.id in (1,4):
            amount = "$" + str(obj.fund.price_security.amount * obj.quantity)
            return amount
        elif obj.fund.fund.id in (3,5) and obj.sanction_amount:
            return "$" + str(obj.sanction_amount.amount)
        elif obj.fund.fund.id in (7,8):
            total_amount = 0.0
            for i in obj.company_shares_backer.all():
                total_amount += float(i.amount.amount)
            return "$" + str(total_amount)

class ProjectBackerLaunchListSerializer(serializers.ModelSerializer):
    """
    Serializer for Project Backer launch list viewset
    """
    project = serializers.SerializerMethodField()
    share_holder = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    price_per_share = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

    class Meta:
        model = ProjectBackerLaunch
        fields = ('project','share_holder','percentage','price_per_share','quantity','amount','create_date')

    def get_project(self, obj):
        """
        Get project
        """
        return obj.project_launch.project.title

    def get_share_holder(self, obj):
        """
        Get share holder
        """
        return obj.backer.first_name + " " + obj.backer.last_name

    def get_percentage(self, obj):
        """
        Get percentage
        """
        return obj.project_launch.percentage

    def get_price_per_share(self, obj):
        """
        Get create fund date of backer
        """
        return "$" + str(obj.project_launch.price_per_share.amount)


    def get_amount(self, obj):
        """
        Get amount fund
        """
        if obj.quantity and obj.project_launch.price_per_share:
            total_amount = obj.quantity * obj.project_launch.price_per_share.amount
            return "$" + str(total_amount)



class FundListSerializer(serializers.ModelSerializer):
    """
    Serializer for Fund list of particular project
    """
    funds = serializers.SerializerMethodField()
    fund_details = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'is_registered', 'funds', 'fund_details')


    def get_funds(self, obj):
        """
        Get current project funds
        """
        data = []
        funds = ProjectFund.objects.filter(project=obj.id).values_list('fund',flat=True)
        fund_list = ProjectFundTypeSerializer(ProjectFundType.objects.all(),many=True).data
        for i in fund_list:
            if i['id'] in funds:
                i.update(flag=True)
            else:
                i.update(flag=False)
            data.append(i)
        return data

    def get_fund_details(self, obj):
        """
        Get current project fund details
        """
        return ProjectFundSerializer(ProjectFund.objects.filter(project=obj.id),many=True).data

class ProjectFundScopeSerializer(serializers.ModelSerializer):
    """
    Searlizer for listing selected Fund data for backer
    """

    funds = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'is_registered', 'funds')


    def get_funds(self, obj):
        """
        Get current project selected fund
        """
        fund_obj = ProjectFund.objects.filter(Q(due_by__gt=date.today())| Q(due_by=None), project=obj).values_list('fund',flat=True)
        fund_list = ProjectFundTypeSerializer(ProjectFundType.objects.filter(id__in=fund_obj),many=True).data
        for i in fund_list:
            if i.get('id') == 6:
                company_buy_fund_obj = ProjectFund.objects.filter(Q(due_by__gt=date.today())| Q(due_by=None), project=obj, fund__id=i.get('id'))
                project_backer_fund = ProjectBackerFund.objects.filter(fund__in = company_buy_fund_obj)
                if project_backer_fund.exists():
                    i.update({'sold': True})
        return fund_list

class PackageListSerializer(serializers.ModelSerializer):
    """
    Serializer for Package Listing
    """

    amount = MoneyField(required=False, allow_null=True)
    acquire_positions = serializers.IntegerField(source='get_positions', read_only=True)
    message = serializers.SerializerMethodField()

    class Meta:
        model = PackageList
        fields = ('id', 'title','amount','position_name','position_number','days','acquire_positions','message')

    def get_message(self, obj):
        """
        set slot available message
        """
        message = None
        package_details_obj = ProjectPackageDetails.objects.filter(package=obj, expiry_date__gte=datetime.now().date()).order_by('expiry_date')
        end_date = datetime.now().date() + timedelta(days=3)
        released_positions = []

        for p in package_details_obj:
            if p.expiry_date <= end_date and p.expiry_date >= datetime.now().date():
                released_positions.append(p.expiry_date)
        if released_positions:
            message = 'This package is available on ' + str(released_positions[0])
        return message

class ProjectPackageDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer Project Package Details serializer
    """
    class Meta:
        model = ProjectPackageDetails
        fields = ('id', 'project', 'package', 'create_date', 'expiry_date', 'is_active',)

class ToDoListSerializer(serializers.ModelSerializer):
    """
    Serializer for To Do List of Creator
    """

    class Meta:
        model = ToDoList
        fields = ('id', 'is_recurring', 'task', 'remind_on', 'due_date', 'snooze_option', 'snooze_time','repeat', 'project','is_complete')

class NdaSerializer(serializers.ModelSerializer):
    """
    Serializer for NDA based on projects
    """

    class Meta:
        model = NdaDetails
        fields = ('id','description','create_date','creator_email')

class NdaHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for NDA History
    """

    class Meta:
        model = NdaHistoryDetails
        fields = ('id','description','updated_date')

class RatingSerializer(serializers.ModelSerializer):
    """
    Serializer for Employee Ratings
    """

    class Meta:
        model = Ratings
        fields = '__all__'

class EmployeeRatingDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for Employee Rating Details
    """
    employee_ratings = RatingSerializer(many=True, required=False)

    class Meta:
        model = EmployeeRatingDetails
        fields = ('id','task','employee','creator','employee_ratings')

    def create(self, validated_data):
        ratings_data = validated_data.pop('employee_ratings', None)
        instance = super().create(validated_data)
        if ratings_data is not None:
            data = []
            for r in ratings_data:
                d={
                    'parameter': r.get('parameter').id,
                    'rating': r.get('rating'),
                }
                data.append(d)
            s = RatingSerializer(data=data, many=True)
            s.is_valid(raise_exception=True)
            s.save(employee_rating_details= instance)

        return instance

    def update(self, instance, validated_data):
        ratings_data = validated_data.pop('employee_ratings', None)
        instance = super().update(instance, validated_data)
        if ratings_data is not None:
            data = []
            for r in ratings_data:
                d={
                    'parameter': r.get('parameter').id,
                    'rating': r.get('rating'),
                }
                data.append(d)
            s = RatingSerializer(data=data, many=True)
            s.is_valid(raise_exception=True)
            s.save(employee_rating_details= instance)
        return instance

class DocumentsToNotarisationSerializer(serializers.ModelSerializer):
    document = Base64FileField(
        required=False, allow_null=True, label="notarized_document"
    )

    class Meta:
        model = DocumentsToNotarisation
        fields = ('id','document_name','document','size','document_id','notarization_details')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('document_name'):
            file_extension = attrs.get('document_name').split('.')[1]
            if file_extension not in ['pdf']:
                raise serializers.ValidationError('This type of file is not valid.')
        return attrs

class NotarizedDocumentsSerializer(serializers.ModelSerializer):
    flag = "notarization"
    document = Base64FileField(
        required=False, allow_null=True, label="notarized_document"
    )

    class Meta:
        model = NotarizedDocuments
        fields = ('id','document_name','document','size','notarization_details')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('document_name'):
            file_extension = attrs.get('document_name').split('.')[1]
            if file_extension not in ['pdf']:
                raise serializers.ValidationError('This type of file is not valid.')
        return attrs

class NotarizationDetailsSerializer(serializers.ModelSerializer):
    uploaded_documents = serializers.SerializerMethodField()
    notarised_documents = serializers.SerializerMethodField()

    class Meta:
        model = NotarizationDetails
        fields = ('id','project','transaction_id','email','first_name','last_name','address_line1',
            'address_line2','city','state','country','pincode','start','end','notary_name',
            'notary_city','notary_registration','uploaded_documents','notarised_documents')

    def get_uploaded_documents(self, obj):
        """
        Get uploaded documents
        """
        return DocumentsToNotarisationSerializer(
            DocumentsToNotarisation.objects.filter(notarization_details=obj.id),many=True
        ).data

    def get_notarised_documents(self, obj):
        """
        Get notarised documents
        """
        return NotarizedDocumentsSerializer(
            NotarizedDocuments.objects.filter(notarization_details=obj.id),many=True
        ).data


class ProjectLaunchSerializer(serializers.ModelSerializer):
    """
    Serializer for Project Launch
    """
    fund_amount = MoneyField(required=False, allow_null=True,)
    price_per_share = MoneyField(required=False, allow_null=True,)

    class Meta:
        model = ProjectLaunch
        fields  = ('id','launch','fund_amount','percentage','due_date','price_per_share')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('fund_amount'):
            raise serializers.ValidationError('Please set Fund amount')
        if not attrs.get('percentage'):
            raise serializers.ValidationError('Please set Percentage')
        if not attrs.get('due_date'):
            raise serializers.ValidationError('Please set due date')
        if not attrs.get('price_per_share'):
            raise serializers.ValidationError('Please set price per share')
        return attrs

class ProjectLaunchScopeSerializer(serializers.ModelSerializer):
    """
    Searlizer for listing launch data
    """

    launch = serializers.SerializerMethodField()
    manage_fund = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'is_registered', 'launch','manage_fund')


    def get_launch(self, obj):
        """
        Get current project launch
        """
        return ProjectLaunchSerializer(
            ProjectLaunch.objects.filter(project=obj.id),many=True
        ).data

    def get_manage_fund(self, obj):
        """
        Get Already entry against this launch or not
        """
        fund_obj = ProjectFund.objects.filter(project=obj.id)
        if fund_obj.exists():
            return True
        else:
            return False

class ProjectBackerLaunchSerializer(serializers.ModelSerializer):
    """
    Serializer for Project Backer launch
    """
    class Meta:
        model = ProjectBackerLaunch
        fields = ('id','project_launch','backer','quantity')

    def create(self, validated_data):
        wallet_amount = Transactions.get_wallet_amount(self,user=self.context['request'].user)

        amount = validated_data.get("quantity") * validated_data.get("project_launch").price_per_share.amount
        if wallet_amount < amount:
            raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')

        instance = super().create(validated_data)

        data = [{
                    "reference_no": "",
                    "remark": "Project launch",
                    "mode": "withdrawal",
                    "status": "success",
                    "amount":{"amount":amount,"currency":"USD"},
                    "user": self.context['request'].user.id
                },
                {
                    "reference_no": "",
                    "remark": "Project launch",
                    "mode": "deposite",
                    "status": "success",
                    "amount":{"amount":amount,"currency":"USD"},
                    "user": validated_data.get('project_launch').project.owner.id
                }
            ]
        s = TransactionsSerializer(data=data,many=True)
        s.is_valid(raise_exception=True)
        s.save(project=validated_data.get('project_launch').project)

        return instance

class ProductCompareSerializer(serializers.ModelSerializer):
    """
    serializer for compare product
    """
    pimage = Base64ImageField(required=False, allow_null=True)
    largeimage = Base64ImageField(required=False, allow_null=True)


class FinalProductSerializer(serializers.ModelSerializer):
    """
    serializer for final product
    """
    productcompare_answer = serializers.JSONField(required=False, allow_null=True)
    class Meta:
        model = FinalProduct
        fields = ('id','productcompare_answer')

class TimeSerializer(serializers.ModelSerializer):
    """
    Serializer for Time
    """
    time = serializers.TimeField(format="%H:%M:%S")
    class Meta:
        model = Time
        fields = '__all__'

class ToDoListSerializer(serializers.ModelSerializer):
    """
    Serializer for To Do List of Creator
    """
    frequency_time = TimeSerializer(many=True,read_only=True,required=False)
    repeat_days = fields.MultipleChoiceField(choices=DAYS_OF_WEEK)
    repeat_months = fields.MultipleChoiceField(choices=MONTHS_IN_YEAR)

    class Meta:
        model = ToDoList
        fields = '__all__'

    def get_serializer(self, args, *kwargs):
            if 'data' in kwargs:
                data = kwargs['data']

                if isinstance(data, list):
                    kwargs['many'] = True

            return super().get_serializer(*args, **kwargs)

class NotificationSerializer(serializers.ModelSerializer):
    """
    serializer for notification
    """
    project = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'
        
    def get_project(self, obj):
        return obj.to_do_list.project.id

    def update(self, instance, validated_data):
        read = validated_data.get('read', instance.read)
        id = validated_data.get('id', instance.id)
        if read == True:
            read_date =  timezone.now()
            Notification.objects.filter(id=id).update(read_date=read_date,read=read)
        return instance

class CompletedTasksSerializer(serializers.ModelSerializer):
    """
    Serializer for projects and subtasks.
    """
    subtasks = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'subtasks')

    def get_subtasks(self, obj):
        """
        Get current project's subtasks
        """
        tasks = Task.objects.filter(participants__in=obj.participants.all(),milestone__project=obj,parent_task__isnull=False).order_by('-id').distinct()
        data = []
        for i in tasks:
            rating_details = EmployeeRatingDetails.objects.filter(task=i,creator=self.context['request'].user).values_list('employee_ratings', flat=True)
            ratings = Ratings.objects.filter(id__in=rating_details)
            average_rating = 0
            if len(ratings) > 0:
                average_rating = sum([r.rating for r in ratings])/len(ratings)
            response = {'id': i.id,'title':i.title,'average_rating': round(average_rating), 'employee_ratings':RatingSerializer(ratings,many=True).data}
            data.append(response)
        return data


class NdaToDocusignSerializer(serializers.ModelSerializer):
    document = Base64FileField(
        required=False, allow_null=True
    )

    class Meta:
        model = NdaToDocusign
        fields = ('id','document_name','document','nda_details','enveloped')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('document_name'):
            file_extension = attrs.get('document_name').split('.')[1]
            if file_extension not in ['pdf']:
                raise serializers.ValidationError('This type of file is not valid.')
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    """
    serializer for material cost product
    """
    price = MoneyField(required=False, allow_null=True,)
    total = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = ProductExpenses
        fields = ('id','name', 'price','qty','shortdescription','total','image','product_id','project')

    def get_total(self, obj):
        """
        calculate total price
        """
        product_data = ProductExpenses.objects.get(id=obj.id)
        if product_data:
            price = product_data.price.amount
            total = price *  product_data.qty

        return '$'+ str(total)

class ProjectBudgetScopeSerializer(serializers.ModelSerializer):
    """
    Searlizer for listing product budget data
    """

    #project_product_budget = ProductSerializer(many=True,required=False)
    project_product_budget = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'project_product_budget','subtotal')


    def get_subtotal(self, obj):
        """
        calculate sub total
        """
        product_data= ProductExpenses.objects.filter(project=obj).order_by('id')
        subtotal = 0.0
        for i in product_data:
            if i.price:
                totalprice = i.price.amount * i.qty
                subtotal += float(totalprice)

        return round(subtotal, 2)

    def get_project_product_budget(self, obj):
        queryset = ProductExpenses.objects.filter(project=obj).order_by('-id')
        page = self.context.get('view').paginate_queryset(queryset)
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            #return serializer.data
            return self.context.get('view').get_paginated_response(serializer.data).data
        serializer = ProductSerializer(queryset, many=True)
        return self.context.get('view').get_paginated_response(serializer.data).data


class CurrentUserTransactonSerializer(serializers.ModelSerializer):
    """
    Serializer for current user Transactions
    """
    wallet = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'wallet','transactions')
        depth = 1

    def get_wallet(self, obj):
        debit_transactions = Transactions.objects.filter(user=obj,status="success",mode="withdrawal").values_list("amount",flat=True)
        credit_transactions = Transactions.objects.filter(user=obj,status="success",mode="deposite").values_list("amount",flat=True)
        wallet = sum(credit_transactions)-sum(debit_transactions)
        return wallet

    def get_transactions(self, obj):
        queryset = Transactions.objects.filter(user=obj)
        queryset = self.context.get('view').filter_queryset(queryset)

        page = self.context.get('view').paginate_queryset(queryset)
        if page is not None:
            serializer = TransactionsSerializer(page, many=True)
            return self.context.get('view').get_paginated_response(serializer.data).data

        serializer = TransactionsSerializer(queryset, many=True)
        return self.context.get('view').get_paginated_response(serializer.data).data

class FundInterestPaySerializer(serializers.ModelSerializer):
    """
    Serializer for Fund Interest Pay
    """
    amount_to_pay = MoneyField(required=False, allow_null=True,)

    class Meta:
        model = FundInterestPay
        fields = ('id','backer_fund','from_date','to_date','amount_to_pay','interest_rate','is_closed')

