from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Bid, Ask
from .serializers import BidSerializer, AskSerializer, LaunchProjectListSerializer
from django.db.models import Q
from projects.models import Project
from rest_framework.decorators import list_route, detail_route


class BidViewSet(viewsets.ModelViewSet):
	serializer_class = BidSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return Bid.objects.filter(bid_by=self.request.user).order_by('-id').distinct()

	def perform_create(self, serializer):
		serializer.save(bid_by=self.request.user)

class AskViewSet(viewsets.ModelViewSet):
	serializer_class = AskSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return Ask.objects.filter(ask_by=self.request.user).order_by('-id').distinct()

	def perform_create(self, serializer):
		serializer.save(ask_by=self.request.user)

class LaunchProjectListView(viewsets.ModelViewSet):
	"""
	Endpoint for Launch Projects List
	"""
	serializer_class = LaunchProjectListSerializer
	permission_classes = [IsAuthenticated]
	http_method_names = ['get','head']

	def get_queryset(self):
		return Project.objects.filter(~Q(project_launch=None))

	@list_route(url_name='launch_type', url_path='(?P<launch_type>[a-z]+)')
	def launch_type(self, request, launch_type=None):
		"""
		Endpoint for lauch projects list
		"""
		queryset = []
		if launch_type == "isx":
			queryset = Project.objects.filter(project_launch__launch__id=2).order_by("id")
		elif launch_type == "lsx":
			queryset = Project.objects.filter(project_launch__launch__id=3).order_by("id")

		page = self.paginate_queryset(queryset)

		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)


