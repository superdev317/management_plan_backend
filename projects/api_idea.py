from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from rest_framework.parsers import JSONParser, MultiPartParser

from django.db.models import Q
from django.core.files.storage import default_storage
from django.http import HttpResponse

from .models import Question, Project, Task, TaskStatus, TaskDocument,DependencyTask, Milestone, EmployeeRatingDetails, WorkSession, Transactions
from .serializers import (
    QuestionSerializer,
    QuestionListSerializer,
    GanttProjectsSerializer,
    TaskSerializer,
    TaskStatusSerializer,
    TaskDocumentSerializer,
    DependentTaskSerializer,
    ProjectMilestonesScopeSerializer,
    EmployeeRatingDetailsSerializer,
    WorkSessionSerializer,
    TransactionsSerializer,
)
from .serializers import DependencyTaskSerializer
from django.shortcuts import get_object_or_404

class IdeaQuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.filter(stage='idea', is_active=True)
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        self.serializer_class = QuestionListSerializer
        return super().list(request, *args, **kwargs)


class GanttProjectsListView(generics.ListAPIView):
    """
    Endpoint for gantt projects list
    """
    serializer_class = GanttProjectsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(
            owner=self.request.user,
            stage='idea',
            date_start__isnull=False,
            date_end__isnull=False
        )
        
class TaskViewSet(viewsets.ModelViewSet):
    """
    Endpoint tasks CRUD
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # FIXME: check perms
        return Task.objects.all()

    def list(self, request, *args, **kwargs):
        self.queryset = Task.objects.filter(
            Q(owner=self.request.user) | Q(participants=self.request.user)
        ).filter(parent_task__isnull=True).distinct()
        return super().list(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @list_route(url_name='statuses')
    def statuses(self, request):
        """
        Endpoint for tasks statuses
        """
        qs = TaskStatus.objects.all()
        return Response(TaskStatusSerializer(qs, many=True).data)


    ####### Avoid Reverse Conflict in milestone dependency #######  
    def dependent_task(self, task, dependent_tasks=None):
        if dependent_tasks is None:  # create a new result if no intermediate was given
            dependent_tasks = []

        task_obj = Task.objects.filter(dependency_task__task = task)#.values_list('id', flat=True)

        for t in task_obj:
            dependent_tasks.append(t)
        if not task_obj:
            return dependent_tasks
        else:
            for t in task_obj: 
                return self.dependent_task(t,dependent_tasks)

    @detail_route(url_name='milestone_list', url_path='milestone-list')
    def milestone_list(self, request, pk=None):
        """
        Endpoint for milestone list
        """
        task_obj =  get_object_or_404(
            Task, pk=pk, owner=request.user
        )
        milestone = []
        tasks = []
        dependent_tasks = self.dependent_task(task_obj)

        for t in dependent_tasks:
            tasks.append(t.id)
        milestone = Task.objects.filter(id__in = tasks).values_list('milestone', flat=True)
        
        serializer = ProjectMilestonesScopeSerializer(
            Milestone.objects.filter(~Q(id__in=milestone),project=task_obj.milestone.project), many=True
        )
        return Response(serializer.data)



class DependentTaskView(viewsets.ReadOnlyModelViewSet):
    # queryset = Task.objects.all()
    serializer_class = DependentTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # FIXME: check perms
        parent_task = Task.objects.filter(participants=self.request.user)\
                           .values_list('parent_task', flat=True).order_by('-id').distinct()
        return Task.objects.filter(Q(participants=self.request.user)| Q(owner=self.request.user) | Q(id__in=parent_task))\
                           .order_by('-id').distinct()


#For Deleting Dependency
class DependencyTaskViewSet(viewsets.ModelViewSet):
    """
    Endpoint tasks for delete
    """
    queryset = DependencyTask.objects.all()
    serializer_class = DependencyTaskSerializer
    permission_classes = [IsAuthenticated]



class TaskDocumentViewSet(viewsets.ModelViewSet):
    """
    Endpoint tasks documents CRUD
    """
    serializer_class = TaskDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return TaskDocument.objects.filter(
            Q(task__owner=self.request.user)|Q(task__participants=self.request.user), task__parent_task__isnull=False
        ).distinct()


class TaskDocumentProxyView(generics.GenericAPIView):
    """
    Endpoint for files proxy from Amazon S3 to frontend
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.GET.get('f'):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        f = default_storage.open(request.GET.get('f')).read()
        response = HttpResponse(f)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            request.GET.get('f')
        )
        return response

class EmployeeRatingDetailsViewSet(viewsets.ModelViewSet):
    """
    Endpoint foe Employee Ratings Crud
    """
    serializer_class = EmployeeRatingDetailsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
        
    def get_queryset(self):
        return EmployeeRatingDetails.objects.all().order_by('-id').distinct()

class WorkSessionViewSet(viewsets.ModelViewSet):
    serializer_class = WorkSessionSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ('task__title')

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    def get_queryset(self):
        return WorkSession.objects.filter(Q(employee__in=self.request.user.userprofile.employees.all(),task__owner=self.request.user)|Q(employee=self.request.user)).order_by('-id').distinct()


class TransactionsViewSet(viewsets.ModelViewSet):
    """
    Endpoint for Transaction Details of Bank Accounts
    """
    serializer_class = TransactionsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transactions.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)





