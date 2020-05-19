from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import generics
from django.utils import timezone
from rest_framework import filters
import django_filters.rest_framework
from django.core.paginator import Paginator
from rest_framework import pagination
from rest_framework.viewsets import ReadOnlyModelViewSet
from actstream.models import Action
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from collections import Counter
from rest_framework import status
from .task import get_notifications
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import datetime, date,timedelta
from digital_sign.views import create_signature,signature_status
import mimetypes
from django.core.files.storage import default_storage
from core.utils import convert_file_to_base64
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from .models import (
    Project, Answer, Milestone, Task, TaskAssignDetails, ToDoList,NdaDetails,
    NdaHistoryDetails,PredefinedMilestone, Question,ProjectLaunch,ProjectLaunchType,
    FinalProduct, ProjectPackageDetails,ProjectFundType , ProjectFund,
    ProjectBuyCompanyShare, NotarizationDetails,Time,Notification,NdaToDocusign,ProductExpenses,Transactions,
    ProjectRegistrationPackage,ProjectBackerFund,ProjectBackerLaunch,PackageList, FundInterestPay
)
from .permissions import IsMilestoneOwner
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectActivitySerializer,
    AnswerSerializer,
    MilestoneSerializer,
    ProjectMilestonesScopeSerializer,
    ProjectPublishedSerializer,
    EmployeeProjectSerializer,
    ToDoListSerializer,
    NdaSerializer,
    NdaHistorySerializer,
    FeedSerializer,
    AllProjectActivitySerializer,
    ProcessesSerializer,
    PredefinedMilestoneSerializer,
    QuestionSerializer,
    ProjectLaunchSerializer,
    #ProductCompareSerializer,
    ProjectLaunchScopeSerializer,
    FinalProductSerializer,
    ProjectPackageDetailsSerializer,
    TimeSerializer,
    NotificationSerializer,
    FundListSerializer,
    # EmployeeExtendHoursSerializer,
    TaskSerializer,
    ProjectFundTypeSerializer,
    ProjectFundSerializer,
    ProjectBuyCompanyShareSerializer,
    FundListSerializer,
    NotarizationDetailsSerializer,
    ProjectFundScopeSerializer,
    NdaToDocusignSerializer,
    ProductSerializer,
    ProjectBudgetScopeSerializer,
    TransactionsSerializer,
    ProjectBackerFundListSerializer,
    ProjectBackerLaunchListSerializer,
    ProjectBackerFundSerializer,
    FundInterestPaySerializer
)
class NotificationViewSet(viewsets.ModelViewSet):
    """
    Notification
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    # queryset =ToDoList.objects.filter(project_id=pk, project__owner=request.user).order_by('end_on')
    def get_queryset(self):
        return Notification.objects.filter(
            Q(to_do_list__project__owner=self.request.user)
        )


class ProjectViewSet(viewsets.ModelViewSet):

    """
    CRUD for projects
    """
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
    filter_fields = ('stage',)
    search_fields = ('title',)
    #ordering = ('-id',)#filters.OrderingFilter,

    def get_serializer(self, *args, **kwargs):

        kwargs['partial'] = True
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        # Q(owner__userprofile__employees=self.request.user)
        return Project.objects.filter(
            Q(owner=self.request.user) |
            Q(participants=self.request.user)
        ).order_by('-id').distinct()

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = ProjectDetailSerializer
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @list_route(url_name='projects_count', url_path='projects-count')
    def projects_count(self, request):
        """
        Endpoint for projects count
        """
        queryset =Project.objects.filter(
            Q(owner=self.request.user) |
            Q(participants=self.request.user)
        ).distinct().values_list('id',flat=True)
        data = {'count': len(queryset)}
        return Response(data)

    @list_route(url_name='published_list', url_path='published')
    def published_list(self, request):
        """
        Endpoint for published projects list
        """
        queryset = Project.objects.filter(
            is_visible=True, status='published'
        ).prefetch_related('milestones')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='published_detail', url_path='published')
    def published_detail(self, request, pk=None):
        """
        Endpoint for published project detail
        """
        obj = get_object_or_404(
            Project, pk=pk, is_visible=True, status='published'
        )
        return Response(ProjectPublishedSerializer(obj).data)

    @detail_route(url_name='activity')
    def activity(self, request, pk=None):
        """
        Endpoint for project activity
        """
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)
        return Response(ProjectActivitySerializer(obj).data)


    @detail_route(url_name='feed')
    def feed(self, request, *args, **kwargs):
        """
        Endpoint for project activity
        """
        self.serializer_class = FeedSerializer
        object = self.get_object()

        self.answer_ct = ContentType.objects.get_for_model(Answer)
        queryset = object.target_actions.filter(
        action_object_content_type=self.answer_ct
        ).order_by('-pk')

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='processes')
    def processes(self, request, *args, **kwargs):
        """
        Endpoint for project processes
        """
        self.serializer_class = ProcessesSerializer
        object = self.get_object()
        queryset =  Task.objects.filter(
            milestone__project=object,
            due_date__gte=timezone.now(),
            parent_task__isnull=False
        ).order_by('due_date')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='answers',url_path='answers/(?P<stage>[a-z]+)', methods=['get', 'post'])
    def answers(self, request, pk=None, stage=None):
        """
        Endpoint for project answers
        """
        if request.method == 'POST':
            s = AnswerSerializer(data=request.data, many=True, partial=True)
            s.is_valid(raise_exception=True)
            s.save(project_id=self.kwargs.get('pk'))

        serializer = AnswerSerializer(
                Answer.objects.filter(project_id=pk), many=True
            )
        if stage in ["idea","startup","registration"]:
            serializer = AnswerSerializer(
                Answer.objects.filter(project_id=pk,question__stage=stage), many=True
            )
        # project__owner__id=request.user.id
        return Response(serializer.data)

    # @detail_route(url_name='answers', methods=['get', 'post'])
    # def answers(self, request, pk=None, stage=None):
    #     """
    #     Endpoint for project answers
    #     """
    #     if request.method == 'POST':
    #         s = AnswerSerializer(data=request.data, many=True, partial=True)
    #         s.is_valid(raise_exception=True)
    #         s.save(project_id=self.kwargs.get('pk'))

    #     serializer = AnswerSerializer(
    #             Answer.objects.filter(project_id=pk), many=True
    #         )

    #     # project__owner__id=request.user.id
    #     return Response(serializer.data)

    @detail_route(url_name='answers_published', url_path='answers/published')
    def answers_published(self, request, pk=None):
        """
        Endpoint for published project answers
        """
        obj = get_object_or_404(
            Project, pk=pk, is_visible=True, status='published'
        )
        serializer = AnswerSerializer(
            Answer.objects.filter(project=obj, is_private=False), many=True
        )
        return Response(serializer.data)

    @detail_route(url_name='project_launch', methods=['post','get'])
    def project_launch(self, request, pk=None):
        """
        Endpoint for project fund plateform
        """
        self.serializer_class = ProjectLaunchSerializer
        obj = get_object_or_404(
            Project, pk=pk, is_visible=True, owner=request.user.id
        )

        serializer = ProjectLaunchSerializer(
            ProjectLaunch.objects.filter(project=obj.id),many=True
        )

        if request.data.get('launch'):
            launchtype_obj = ProjectLaunchType.objects.get(id = request.data.get('launch'))

            launch_data  = ProjectLaunch.objects.filter(project_id=obj.id)
            if launch_data:
                for i in launch_data:

                    if i.launch.id == 2 and launchtype_obj.id == 2:
                        raise serializers.ValidationError('You already launched with ISX ')

                    elif i.launch.id == 3 and launchtype_obj.id == 3:
                        raise serializers.ValidationError('You already launched with LSX ')

                    elif i.launch.id == 2 and launchtype_obj.id == 3:
                        raise serializers.ValidationError('You cannot launch on LSX with ISX')

                    elif i.launch.id == 3 and launchtype_obj.id == 2:
                        raise serializers.ValidationError('You cannot launch on LSX with ISX')

                    else:
                        data = {
                                'launch' : launchtype_obj,
                                'fund_amount':request.data.get('fund_amount'),
                                'percentage':request.data.get('percentage'),
                                'due_date':request.data.get('due_date'),
                                'price_per_share':request.data.get('price_per_share'),
                                'project': obj
                                }

                        project_launch = ProjectLaunchSerializer.create(ProjectLaunchSerializer(), validated_data=data)
                        obj.status = 'published'
                        obj.save()

            else:
                if launchtype_obj.id == 2 and obj.is_registered==False:
                    raise serializers.ValidationError('Sorry! You cannot launch the project on ISX unless have registered the start-up idea.')
                elif launchtype_obj.id ==3 and obj.get_answers_progress() != 100:
                    raise serializers.ValidationError('This funding requires your idea to complete the company registration phase')
                else:
                    data = {
                        'launch' : launchtype_obj,
                        'fund_amount':request.data.get('fund_amount'),
                        'percentage':request.data.get('percentage'),
                        'due_date':request.data.get('due_date'),
                        'price_per_share':request.data.get('price_per_share'),
                        'project': obj
                        }

                    project_launch = ProjectLaunchSerializer.create(ProjectLaunchSerializer(), validated_data=data)
                    obj.status = 'published'
                    obj.save()

        return Response(serializer.data)

    @detail_route(url_name='launch')
    def launch(self, request, pk=None):
        """
        Endpoint for project launch
        """
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)
        return Response(ProjectLaunchScopeSerializer(obj).data)

    @detail_route(url_name='fund_list',url_path='fund-list', methods=['get'])
    def fund_list(self, request, pk=None):
        """
        Endpoint for project fund list
        """
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)
        return Response(FundListSerializer(obj).data)

    ############################################# Backer Fund and Launch Services Start#######################################################
    @detail_route(url_name='selected_fund_list',url_path='selected/fund-list', methods=['get'])
    def selected_fund_list(self, request, pk=None):
        """
        Endpoint for project selected fund list
        """
        self.serializer_class = ProjectFundScopeSerializer
        obj = get_object_or_404(
            Project, pk=pk, is_visible=True, status='published'
        )
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @detail_route(url_name='fund_details', url_path='selected/fund-list/(?P<fund_type_id>[0-9]+)')
    def fund_details(self, request,pk=None, fund_type_id=None):
        self.serializer_class = ProjectFundSerializer
        obj = get_object_or_404(
            Project, pk=pk, is_visible=True, status='published'
        )
        fund_obj = ProjectFund.objects.filter(project=obj,fund=fund_type_id).first()
        serializer = self.get_serializer(fund_obj)
        return Response(serializer.data)

    @detail_route(url_name='launch_details', url_path='launch-details', methods=['get'])
    def launch_details(self, request, pk=None):
        """
        Endpoint of project launch details for backer
        """
        obj = get_object_or_404(Project, pk=pk, is_visible=True, status='published')
        return Response(ProjectLaunchScopeSerializer(obj).data)

    ############################################# Backer Fund and Launch Services End #######################################################

    ############################################# Project Wise creator saw the funds provided by backer and purchase share in ISX/LSX Start ##############################
    @detail_route(url_name='funds',url_path='funds', methods=['get'])
    def funds(self, request, pk=None):
        """
        Endpoint for project fund list by backer
        """
        self.serializer_class = ProjectBackerFundListSerializer
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)
        queryset = ProjectBackerFund.objects.filter(fund__owner=request.user.id,fund__project=obj)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset,many=True)
        return Response(serializer.data)

    @detail_route(url_name='backer_launch_details',url_path='backer-launch-details', methods=['get'])
    def backer_launch_details(self, request, pk=None):
        """
        Endpoint for project launch list by backer
        """
        self.serializer_class = ProjectBackerLaunchListSerializer
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)
        queryset = ProjectBackerLaunch.objects.filter(project_launch__project__owner=request.user.id,project_launch__project=obj)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset,many=True)
        return Response(serializer.data)

    ############################################# Project Wise creator saw the funds provided by backer  purchase share in ISX/LSX End ##############################

    @detail_route(url_name='milestones')
    def milestones(self, request, pk=None):
        """
        Endpoint for milestones-tasks-subtasks
        """
        self.serializer_class = ProjectMilestonesScopeSerializer
        milestones = Task.objects.filter(milestone__project__id=pk ,participants=self.request.user).values_list('milestone', flat=True)

        queryset = Milestone.objects.filter(Q(id__in=milestones)|Q(project__owner=self.request.user,project_id=pk)).order_by('order')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='to_do_list', url_path='todo-list', methods=['get', 'post','put','delete'])
    def to_do_list(self, request, pk=None):
        """
        Endpoint for Projects to do list.
        """
        self.serializer_class = ToDoListSerializer

        def check_frequency(frequency_time):
            if len(frequency_time) > int(frequency):
                raise serializers.ValidationError({'error': 'you can only submit {} time(s) frequency'.format(frequency)})

            start_d = '09:00:00'
            start_time = datetime.strptime(start_d, "%H:%M:%S").time()

            end_d = '17:00:00'
            end_time = datetime.strptime(end_d, "%H:%M:%S").time()

            for time in frequency_time:
                t = datetime.strptime(time.get('time'), "%H:%M:%S").time()
                if t < start_time or t > end_time:
                    raise serializers.ValidationError({'error': 'Time is out of range '})
            return frequency_time

        def add_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months):
            #add data
            end_on = timezone.now()+timedelta(days=3650)
            time_list = []
            for time in frequency_time:
                addons = Time.objects.create(time=time['time'])
                time_list.append(addons)

            request_data_list = []
            request_data_list.append(request.data)
            s = self.serializer_class(data=request_data_list,many=True)
            s.is_valid(raise_exception=True)
            obj = get_object_or_404(
            Project, pk=pk, owner=request.user
            )
            s.save(project=obj,frequency_time=time_list)

        # POST METHOD FOR TO DO LIST
        def update_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months,task):
            time_list = []
            new_time_list = []

            for time in frequency_time:
                get_time = time.get('id', None)
                if get_time is None or get_time is 0:
                    create_obj = Time.objects.create(time=time['time'])
                    new_time_list.append(create_obj)
                else:
                    filt_obj = Time.objects.get(id=get_time)
                    filt_obj.time = time['time']
                    filt_obj.save()
                    new_time_list.append(filt_obj)
            to_do_list = ToDoList.objects.get(id=id)
            time_delete = [i.delete() for i in to_do_list.frequency_time.all() if i not in new_time_list]
            serializer = ToDoListSerializer(to_do_list, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(frequency_time=new_time_list)


        if request.method == 'POST':
            remind = request.data.get('remind')
            task = request.data.get('task')
            start_on = request.data.get('start_on')
            remind_me = request.data.get('remind_me')
            frequency_time = request.data.get('frequency_time')
            repeat_days = request.data.get('repeat_days')
            repeat_months = request.data.get('repeat_months')
            frequency  = request.data.get('frequency')
            let_system_do_it  = request.data.get('let_system_do_it')
            # to check whether time is between 9 to 17
            end_on = timezone.now()+timedelta(days=3650)
            if let_system_do_it:
                frequency = 3
                end_on = timezone.now()+timedelta(days=3650)
                frequency_time = [{'time': '09:00:00'}, {'time': '12:00:00'},{'time': '15:00:00'}]
                add_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months)

            if remind == 'daily' and not let_system_do_it:
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                repeat_months = ''
                repeat_days = ''
                add_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months)

            elif remind == 'weekly' and not let_system_do_it:
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                repeat_months = ''
                add_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_days)

            elif remind == 'monthly' and not let_system_do_it:
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                add_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_days)

            elif remind == 'yearly' and not let_system_do_it:
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                repeat_months = ''
                add_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_days)

        # END OF POST METHOD FOR TO DO LIST

        # PUT METHOD FOR TO DO LIST
        if request.method == 'PUT':
            id = request.data.get('id')
            remind = request.data.get('remind')
            task = request.data.get('task')
            start_on = request.data.get('start_on')
            remind_me = request.data.get('remind_me')
            frequency_time = request.data.get('frequency_time')
            repeat_days = request.data.get('repeat_days')
            repeat_months = request.data.get('repeat_months')
            end_on  = request.data.get('end_on')
            frequency  = request.data.get('frequency')
            let_system_do_it  = request.data.get('let_system_do_it')

            if let_system_do_it:
                frequency = 3
                end_on = timezone.now()+timedelta(days=3650)
                frequency_time = [{'time': '09:00:00'}, {'time': '12:00:00'},{'time': '15:00:00'}]
                update_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months,task)

            if remind == 'daily':
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                end_on = 'null'
                repeat_months = ''
                repeat_days = ''
                update_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months,task)

            if remind == 'weekly':
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                repeat_months = ''
                update_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months,task)

            if remind == 'monthly':
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                update_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months,task)

            if remind == 'yearly':
                if remind_me == 'between_9_to_17':
                    check_frequency(frequency_time)
                repeat_months = ''
                repeat_days = ''
                update_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months,task)

            if remind_me == '24_hours':
                check_frequency(frequency_time)
                update_data(frequency_time,remind,remind_me,start_on,end_on,repeat_days,repeat_months,task)

        if request.method == 'DELETE':
            id = request.data.get('id')
            m = ToDoList(id=id)
            m.delete()

        queryset =ToDoList.objects.filter(project_id=pk, project__owner=request.user, is_complete=False).order_by('end_on')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='completed_todo_list',url_path='todo-list/completed', methods=['get'])
    def completed_todo_list(self, request, pk=None):
        """
        Endpoint for completed todo list
        """
        self.serializer_class = ToDoListSerializer
        obj = get_object_or_404(
            Project, pk=pk, owner=request.user
        )
        queryset =ToDoList.objects.filter(project=obj, project__owner=request.user, is_complete=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='nda_list', url_path='nda-list', methods=['get', 'post', 'put'])
    def nda_list(self, request, pk=None):
        """
        Endpoint for Projects nda list.
        """
        self.serializer_class = NdaSerializer
        if request.method == 'POST':
            s = NdaSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            obj = get_object_or_404(
                Project, pk=pk)

            instance = s.save(project=obj)
            obj.add_nda = True
            obj.save()

            docusign_data = {
                'emp_id' : '',
                'creator_email':request.data.get('creator_email'),
                'document' :request.data.get('document').split(',')[1],
                'document_name' :request.data.get('document_name'),
                'creatorXposition':request.data.get('creatorXposition'),
			    'creatorYposition':request.data.get('creatorYposition'),
                'nda':True
		    }

            docusign_url = create_signature(docusign_data)
            docusign_doc = {'document':request.data.get('document'),'document_name':request.data.get('document_name')}
            s = NdaToDocusignSerializer(data=docusign_doc)
            s.is_valid(raise_exception=True)
            s.save(nda_details=instance,enveloped=docusign_url['envelopeId'])

            NdaDetails.objects.filter(project=pk).update(docusign_envelop=docusign_url['envelopeId'],creator_email=request.data.get('creator_email'))

            nda_data = NdaDetails.objects.filter(project=pk).order_by('-id').first()
            return Response(NdaSerializer(nda_data).data)

        if request.method == 'PUT':

            obj = get_object_or_404(
                Project, pk=pk
            )

            data = {
                'description' : request.data.get('description'),
                'project':obj
            }
            history = NdaHistorySerializer.create(NdaHistorySerializer(), validated_data=data)
            nda_obj = NdaDetails.objects.get(id = request.data.get('id'))
            nda_obj.description = request.data.get('description')
            nda_obj.save()
            nda_data = NdaDetails.objects.filter(project=pk).order_by('-id').first()
            return Response(NdaSerializer(nda_data).data)

        if request.method == 'GET':
            obj = get_object_or_404(
                Project, pk=pk
            )
            nda_obj = NdaDetails.objects.filter(project=pk).order_by('-id').first()
            if nda_obj is not None:
                data={
                    'emp_id':'',
                    'creator_email':nda_obj.creator_email,
                    'envelop_id':nda_obj.docusign_envelop
                }
                final_url = signature_status(data)
                nda_details = NdaSerializer(nda_obj).data
                nda_details.update({'docusign_status':final_url})
                return Response(nda_details)

            else:
                data={
                    "docusign_status":"No Nda"
                }
                return Response(data)


    @detail_route(url_name='project_package_details', url_path='package-details', methods=['get', 'post', 'put'])
    def project_package_details(self, request, pk=None):
        """
        Endpoint for project upgrade package list
        """
        self.serializer_class = ProjectPackageDetailsSerializer
        wallet_amount = Transactions.get_wallet_amount(self,user=request.user)

        if request.method == 'POST':
            package = PackageList.objects.get(id=request.data.get('package'))
            if wallet_amount < package.amount.amount:
                raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')
            s = ProjectPackageDetailsSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            obj = get_object_or_404(
                Project, pk=pk, owner=request.user
            )
            s.save(project=obj)

            data = [{
                        "reference_no": "",
                        "remark": "Upgrade Listing",
                        "mode": "withdrawal",
                        "status": "success",
                        "amount":{"amount":package.amount.amount,"currency":"USD"},
                        "user": request.user.id
                    },
                    {
                        "reference_no": "",
                        "remark": "Upgrade Listing",
                        "mode": "deposite",
                        "status": "success",
                        "amount":{"amount":package.amount.amount,"currency":"USD"},
                        "user": 1
                    }
                ]

            transaction = TransactionsSerializer(data=data,many=True)
            transaction.is_valid(raise_exception=True)
            transaction.save(project=obj)

        if request.method == 'PUT':
            package = PackageList.objects.get(id=request.data.get('selected_package'))
            if wallet_amount < package.amount.amount:
                raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')
            obj = get_object_or_404(
                Project, pk=pk
            )
            package_details_obj = ProjectPackageDetails.objects.get(id = request.data.get('id'))
            package_details_obj.is_active = False
            package_details_obj.save()

        queryset =ProjectPackageDetails.objects.filter(project_id=pk, project__owner=request.user, is_active=True,expiry_date__gt=datetime.now().date()).order_by('-id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @detail_route(url_name='notarization_details',url_path='notarization-details', methods=['get'])
    def notarization_details(self, request, pk=None):
        """
        Endpoint for project notarization details
        """
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)
        notarization_obj = get_object_or_404(NotarizationDetails, project=pk)
        return Response(NotarizationDetailsSerializer(notarization_obj).data)

    @detail_route(url_name='product_budget', url_path='product-budget', methods=['get', 'post','put','delete'])
    def product_budget(self, request, pk=None):
        self.serializer_class = ProductSerializer
        if request.method == 'POST':
            s = ProductSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            obj = get_object_or_404(
                Project, pk=pk, owner=request.user
            )
            s.save(project=obj)

        queryset =ProductExpenses.objects.filter(project_id=pk,).order_by('-id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='product_budget_details', url_path='product-budget/(?P<id>[0-9]+)', methods=['get','put','delete'])
    def product_budget_details(self, request,pk=None, id=None):
        if request.method == 'DELETE':
            m = ProductExpenses(id=id)
            m.delete()

        self.serializer_class = ProductSerializer
        obj = get_object_or_404(
                Project, pk=pk, owner=request.user
        )
        queryset = ProductExpenses.objects.filter(project=obj,id=id).first()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    @detail_route(url_name='budget_list',url_path='budget-list', methods=['get'])
    def budget_list(self, request, pk=None):
        """
        Endpoint for product budget list
        """
        self.serializer_class = ProjectBudgetScopeSerializer
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @detail_route(url_name='project_registration',url_path='transaction', methods=['post','get'])
    def project_registration(self, request, pk=None):
        """
        Endpoint for product budget list
        """
        self.serializer_class = TransactionsSerializer
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)

        if request.method == 'POST':
            wallet_amount = Transactions.get_wallet_amount(self,user=request.user)
            registration_package = request.data.pop('package')
            registration_package_obj = ProjectRegistrationPackage.objects.filter(id=registration_package).first()

            if wallet_amount < registration_package_obj.amount:
                raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')
            else:
                data = [{
                        "reference_no": "",
                        "remark": "project registration",
                        "mode": "withdrawal",
                        "status": "success",
                        "amount":{"amount":registration_package_obj.amount,"currency":"USD"},
                        "user": request.user.id
                    },
                    {
                        "reference_no": "",
                        "remark": "project registration",
                        "mode": "deposite",
                        "status": "success",
                        "amount":{"amount":registration_package_obj.amount,"currency":"USD"},
                        "user": 1
                    }
                ]

                s = self.get_serializer(data=data,many=True)
                s.is_valid(raise_exception=True)
                s.save(project=obj)
                obj.package = registration_package_obj
                obj.is_registered = True
                obj.save()

        queryset = Transactions.objects.filter(project=obj)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='loan_services_list',url_path='loan-list', methods=['get','put'])
    def loan_services_list(self, request, pk=None):
        """
        Endpoint for loan services list
        """
        self.serializer_class = ProjectBackerFundSerializer
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)

        if request.method == 'PUT':
            backer_fund = get_object_or_404(ProjectBackerFund, pk=request.data.get('id'), fund__project__owner=request.user.id)
            if not backer_fund.is_closed:
                wallet_amount = Transactions.get_wallet_amount(self,user=request.user)
                if wallet_amount < backer_fund.sanction_amount.amount:
                    raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')
                data = [{
                    "reference_no": "",
                    "remark": "Loan Closing",
                    "mode": "withdrawal",
                    "status": "success",
                    "amount":{"amount":backer_fund.sanction_amount.amount,"currency":"USD"},
                    "user": request.user.id
                    },
                    {
                    "reference_no": "",
                    "remark": "Loan Closing",
                    "mode": "deposite",
                    "status": "success",
                    "amount":{"amount":backer_fund.sanction_amount.amount,"currency":"USD"},
                    "user": backer_fund.backer.id
                    }
                ]

                transaction = TransactionsSerializer(data=data,many=True)
                transaction.is_valid(raise_exception=True)
                transaction.save(project=obj)
                backer_fund.is_closed = True
                backer_fund.save()

        queryset = ProjectBackerFund.objects.filter(fund__fund__id__in=[3,5], fund__project=obj)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='interest_pay',url_path='fund/interest-pay', methods=['get','put'])
    def interest_pay(self, request, pk=None):
        """
        Endpoint for loan services list
        """
        self.serializer_class = FundInterestPaySerializer
        obj = get_object_or_404(Project, pk=pk, owner=request.user.id)

        if request.method == 'PUT':
            amount = sum([i.get('amount_to_pay').get('amount') for i in request.data])
            
            wallet_amount = Transactions.get_wallet_amount(self,user=request.user)
            if wallet_amount < amount:
                raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')

            for i in request.data:
                fund_interest_obj = FundInterestPay.objects.get(id=i.get("id"))
                if not fund_interest_obj.is_closed:
                    data = [{
                        "remark": "Loan Interest Pay- " + str(fund_interest_obj.from_date) + " to " + str(fund_interest_obj.to_date),
                        "mode": "withdrawal",
                        "status": "success",
                        "amount":i.get('amount_to_pay'),
                        "user": request.user.id
                        },
                        {
                        "remark": "Loan Interest Pay- " + str(fund_interest_obj.from_date) + " to " + str(fund_interest_obj.to_date),
                        "mode": "deposite",
                        "status": "success",
                        "amount":i.get('amount_to_pay'),
                        "user": fund_interest_obj.backer_fund.backer.id
                        }
                    ]

                    transaction = TransactionsSerializer(data=data,many=True)
                    transaction.is_valid(raise_exception=True)
                    transaction.save(project=obj)
                    fund_interest_obj.is_closed = i.get('is_closed')
                    fund_interest_obj.save()

        queryset = FundInterestPay.objects.filter(backer_fund__fund__owner=request.user, backer_fund__fund__project=obj,is_closed=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

#to get notification count
class NotificationCountView(APIView):
    """
    A view that can accept POST requests with JSON content.
    """
    parser_classes = (JSONParser,)

    def get(self, request, format=None):
        serializer = Notification.objects.filter(to_do_list__project__owner=self.request.user,read=False )
        serializer = len(serializer)
        return Response({'notification_count':serializer})


class PredefinedMilestoneViewset(viewsets.ModelViewSet):
    """
    CRUD for predefined milestone
    """
    serializer_class = PredefinedMilestoneSerializer
    permission_classes = [IsAuthenticated, IsMilestoneOwner]
    queryset = PredefinedMilestone.objects.all()

class MilestoneViewSet(viewsets.ModelViewSet):
    """
    CRUD for milestones
    """
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated, IsMilestoneOwner]

    def get_serializer(self, *args, **kwargs):
        kwargs['partial'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return Milestone.objects.filter(project__owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        milestone_obj = Milestone.objects.get(id=instance.id)
        order_data = Milestone.objects.filter(order__gte = milestone_obj.order,project=instance.project)
        for mile in order_data:
            mile_obj = Milestone.objects.get(id=mile.id)
            mile_obj.order = mile_obj.order -1 
            mile_obj.save()
        self.perform_destroy(instance)

        return Response("deleted",status=status.HTTP_200_OK)

class EmployeeOngoingProjectViewSet(viewsets.ModelViewSet):
    """
    Endpoint employee project CRUD
    """
    serializer_class = EmployeeProjectSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head']
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)

    def get_queryset(self):
        # FIXME: check perms
        # t = Task.objects.filter(participants=self.request.user, complete_percent__lt = 100).distinct().values_list('milestone', flat=True)
        tasks = Task.objects.filter(participants=self.request.user).distinct().values_list('id', flat=True)
        ongoing_task = TaskAssignDetails.objects.filter(task__in=tasks,completed_date__isnull=True).distinct()
        milestones = [task.task.milestone for task in ongoing_task]
        projects = Project.objects.filter(milestones__in=milestones).values_list('id', flat=True)
        return Project.objects.filter(Q(id__in=projects)).distinct()


class EmployeePastProjectViewSet(viewsets.ModelViewSet):
    """
    Endpoint employee project CRUD
    """
    serializer_class = EmployeeProjectSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head']
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
    filter_fields = ('stage',)
    search_fields = ('title','owner__userprofile__first_name','owner__userprofile__last_name')

    def get_queryset(self):
        # FIXME: check perms
        # t = Task.objects.filter(Q(complete_percent__gt = 100),participants=self.request.user).distinct().values_list('milestone', flat=True)
        tasks = Task.objects.filter(participants=self.request.user).distinct().values_list('id', flat=True)
        ongoing_task = TaskAssignDetails.objects.filter(task__in=tasks,completed_date__isnull=True).distinct()
        ongoging_milestones = [task.task.milestone for task in ongoing_task]
        ongoing_projects = Project.objects.filter(milestones__in=ongoging_milestones).values_list('id', flat=True)
        completed_task = TaskAssignDetails.objects.filter(~Q(task__milestone__project__in=ongoing_projects),task__in=tasks,completed_date__isnull=False).distinct()
        milestones = [task.task.milestone for task in completed_task]
        projects = Project.objects.filter(milestones__in=milestones).values_list('id', flat=True)
        return Project.objects.filter(Q(id__in=projects)).distinct()

class ToDoListViewSet(viewsets.ModelViewSet):
    """
    CRUD for To Do List for Creator
    """
    serializer_class = ToDoListSerializer
    permission_classes = [IsAuthenticated, IsMilestoneOwner]

    def get_serializer(self, *args, **kwargs):
        kwargs['partial'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return ToDoList.objects.filter(project__owner=self.request.user,is_complete=False)


# class ProductCompareViewSet(viewsets.ModelViewSet):
#     """
#     CRUD for  product compare for creator
#     """
#     serializer_class = ProductCompareSerializer
#     permission_classes = [IsAuthenticated]
#     queryset = ProductDetails.objects.all()

class FinalProductViewSet(viewsets.ModelViewSet):
    """
    CRUD for  final product
    """
    serializer_class = FinalProductSerializer
    permission_classes = [IsAuthenticated]
    queryset = FinalProduct.objects.all()

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)
