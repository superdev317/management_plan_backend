from rest_framework import generics
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Page, Message
from .serializers import PageSerializer, MessageSerializer


class PageListView(viewsets.ModelViewSet):
    """
    Endpoint for list pages
    """
    serializer_class = PageSerializer
    permission_classes = [AllowAny]
    queryset = Page.objects.all()


class MessageListView(generics.ListAPIView):
    """
    Endpoint for list messages
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
