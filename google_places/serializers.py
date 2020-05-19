from rest_framework import serializers


class PlaceAddressSerializer(serializers.Serializer):
    """
    Serializer for list addresses from google place
    """
    address = serializers.CharField()
