from rest_framework import generics

from .serializers import ActionStreamAnySerializer

from actstream.models import Action


class ActionStreamAnyListView(generics.ListAPIView):
    """
    Endpoint for any active stream list
    """
    queryset = Action.objects.filter(public=True)
    serializer_class = ActionStreamAnySerializer
