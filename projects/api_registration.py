from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated

from .models import Question , ProjectRegistrationType, ProjectRegistrationPackage
from .serializers import (
    QuestionSerializer,
    QuestionListSerializer,
    RegistrationListSerializer,
    RegistrationPackageSerializer
    )
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response


class RegistrationQuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.filter(stage='registration', is_active=True)
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        self.serializer_class = QuestionListSerializer
        return super().list(request, *args, **kwargs)


class RegistrationTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD for Registration Type
    """
    serializer_class = RegistrationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectRegistrationType.objects.all().order_by('id')

    @detail_route(url_name='questions', methods=['get'])
    def questions(self, request, pk=None):
        """
        Endpoint for Registration Type Questions
        """
        serializer = QuestionSerializer(
            Question.objects.filter(registration_type_id=pk, parent_question__isnull=True, is_active=True), many=True
        )
        return Response(serializer.data)

    @detail_route(url_name='packages', methods=['get'])
    def packages(self, request, pk=None):
        """
        Endpoint for Registration Type Questions
        """
        serializer = RegistrationPackageSerializer(
            ProjectRegistrationPackage.objects.filter(registration_type_id=pk, is_active=True), many=True
        )
        return Response(serializer.data)

