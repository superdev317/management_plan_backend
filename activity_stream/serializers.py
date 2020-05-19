from rest_framework import serializers

from actstream.models import Action


class ActionStreamAnySerializer(serializers.ModelSerializer):
    """
    Serializer for any active actions
    """
    sentence = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = '__all__'

    @staticmethod
    def get_sentence(obj):
        return obj.__str__()
