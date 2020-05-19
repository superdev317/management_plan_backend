from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Question
from .serializers import (
    QuestionSerializer,
    QuestionListSerializer
)


class StartupQuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.filter(stage='startup', is_active=True)
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        self.serializer_class = QuestionListSerializer
        return super().list(request, *args, **kwargs)
