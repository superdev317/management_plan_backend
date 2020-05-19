from rest_framework import serializers

from .models import UserChat, DecisionPollVote
from accounts.serializers import UserProfileShortDataSerializer


class UserChatSerializer(serializers.ModelSerializer):
    """
    Serializer for chat user profile
    """
    user = UserProfileShortDataSerializer(source='user.userprofile')

    class Meta:
        model = UserChat
        fields = ('id', 'username', 'chat_user_id', 'user')

class DecisionPollVoteSerializer(serializers.ModelSerializer):
    """
    Serializer for chat user profile
    """
    class Meta:
        model = DecisionPollVote
        fields = ('id', 'message_id', 'options', 'chat_user_id')
