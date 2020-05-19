from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import filters
import django_filters.rest_framework
from django.core.paginator import Paginator
from rest_framework import pagination
from django.shortcuts import get_object_or_404
import json
from .models import Thread,Comment,ForumCategories,Topics,thread_view
from .serializers import(
ThreadSerializer,
CommentSerializer,
ForumCategoriesSerializer,
TopicsSerializer,
ThreadScopeSerializer,
CommentThreadScopeSerializer,
)
from django.db.models import Q,Count
from projects.permissions import IsProjectOwner
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import filters
import django_filters.rest_framework
from django.http import HttpResponseRedirect,HttpResponse

class ThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
    search_fields = ('title',)

    def get_queryset(self):
        return Thread.objects.filter(
            Q(owner=self.request.user) |
            Q(participants=self.request.user) |
            Q(public=True)
        ).order_by('-id').distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @detail_route(url_name='comment_list', methods=['get'])
    def comment_list(self, request, pk=None):
        """
        crud for comment/post based on thread
        """
        self.serializer_class = CommentThreadScopeSerializer
        obj = get_object_or_404(Thread, pk=pk)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
        
class ForumCategoriesViewSet(viewsets.ModelViewSet):
    serializer_class = ForumCategoriesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
    search_fields = ('title',)
    
    def get_queryset(self):
        return ForumCategories.objects.all()

    @detail_route(url_name='topics', methods=['get'])
    def topics(self, request, pk=None):
        """
        Endpoint for Category related topics
        """
        serializer = TopicsSerializer(
            Topics.objects.filter(category_id=pk).order_by('title'), many=True
        )
        return Response(serializer.data)

    @detail_route(url_name='thread_list', methods=['get'])
    def thread_list(self, request, pk=None):
        """
        Endpoint for Category related thread
        """
        self.serializer_class = ThreadSerializer
        queryset = Thread.objects.filter(Q(forumcategories_id=pk),
                Q(owner=self.request.user) |
                Q(participants=self.request.user) |
                Q(public=True)
            ).order_by('-id')

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_name='thread_mostviewlist', methods=['get'])
    def thread_mostviewlist(self, request,pk=None):
        """
        Endpoint for most view threads
        """
        self.serializer_class = ThreadSerializer
        a = thread_view.objects.all().values("thread").annotate(count=Count('thread')).order_by("-count")
        t = [i.get("thread") for i in a]
        thread = Thread.objects.filter(~Q(id__in=t)).values_list('id', flat=True)
        thread_list = [i for i in thread]
        t.extend(thread_list)
        t1 = []
        for i in t:
            thread_obj = Thread.objects.filter(Q(id=i),Q(forumcategories=pk) | Q(owner=self.request.user)| Q(participants=self.request.user)| Q(public=True)).first()
            if thread_obj:
                t1.append(thread_obj)
        # t1 = [Thread.objects.filter(id=i,forumcategories=pk).first() for i in t]
        queryset = self.filter_queryset(t1)
        page = self.paginate_queryset(t1)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(t1, many=True)
        return Response(serializer.data)

class ForumCommentsViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.all()

    def list(self, request, *args, **kwargs):
        self.queryset = Comment.objects.filter(
            Q(comment_by=self.request.user)
        ).filter(parent_comment__isnull=True).distinct()
        return super().list(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(comment_by=self.request.user)
    
class TopicsViewSet(viewsets.ModelViewSet):
    serializer_class = TopicsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Topics.objects.all()

    @detail_route(url_name='thread_list', methods=['get'])
    def thread_list(self, request, pk=None):
        """
        Endpoint for Topic related thread
        """
        self.serializer_class = ThreadScopeSerializer
        obj = get_object_or_404(Topics, pk=pk)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
          
class ThreadMostViewListSet(viewsets.ModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
    search_fields = ('title',)

    def get_queryset(self):
        a = thread_view.objects.all().values("thread").annotate(count=Count('thread')).order_by("-count")
        t = [i.get("thread") for i in a]
        thread = Thread.objects.filter(~Q(id__in=t)).values_list('id', flat=True)
        thread_list = [i for i in thread]
        t.extend(thread_list)
        t1 = []
        for i in t:
            thread_obj = Thread.objects.filter(Q(id=i), Q(owner=self.request.user)| Q(participants=self.request.user)| Q(public=True)).first()
            if thread_obj:
                t1.append(thread_obj)
        
        #t1 = [Thread.objects.filter(Q(id=i)) for i in t]
        #print("tttttttttttttttttttttttttttttt",t1)
        return t1