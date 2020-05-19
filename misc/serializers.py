from rest_framework import serializers

from .models import Page, Message


class PageSerializer(serializers.ModelSerializer):
    """
    Serializer for pages
    """
    class Meta:
        model = Page
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for messages
    """
    class Meta:
        model = Message
        fields = '__all__'
