from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Q
from django.conf import settings
from django.utils.text import slugify

from .models import TaskGroup, UserChat, get_chat_user, DecisionPollVote
from .helpers import RocketChat
from .serializers import UserChatSerializer, DecisionPollVoteSerializer
from projects.models import Task

from typing import Optional


class ChatUserTokenView(generics.GenericAPIView):
    """
    Endpoint for chat user id and token
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        chat_user = get_chat_user(self.request.user, commit=False)
        rocket = RocketChat(
            chat_user.username,
            chat_user.raw_password
        )
        chat_user.auth_token = rocket.headers['X-Auth-Token']
        chat_user.chat_user_id = rocket.headers['X-User-Id']
        chat_user.save()
        return Response(
            {'user_id': chat_user.chat_user_id, 'token': chat_user.auth_token}
        )


class ChatTaskView(generics.RetrieveAPIView):
    """
    Endpoint for room id and title
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # FIXME: check perms
        return Task.objects.filter(parent_task__isnull=False)

    def get(self, request, *args, **kwargs):
        task = self.get_object()
        rocket_admin = RocketChat(
            settings.ROCKETCHAT_USER,
            settings.ROCKETCHAT_PASSWORD
        )
        chat_user = get_chat_user(self.request.user)

        if task.parent_task:
            try:
                group = TaskGroup.objects.get(task=task)

                if not rocket_admin.groups_info(group.group_id).json().get('success'):
                    group = self.create_chat_group(rocket_admin, task, group)
                elif chat_user.username not in rocket_admin.groups_info(group.group_id).json().get('group').get('u'):
                    rocket_admin.groups_invite(
                        group.group_id, chat_user.chat_user_id
                    )

            except TaskGroup.DoesNotExist:
                group = self.create_chat_group(rocket_admin, task)

            if group is None:
                return Response(status=status.HTTP_403_FORBIDDEN)

            chat_user_ids = UserChat.objects.filter(
                user__in=[x for x in group.task.participants.all()] +
                         [group.task.owner]
            ).values_list('chat_user_id', flat=True)
            return Response(
                {
                    'room_id': group.group_id,
                    'title': group.title,
                    'chat_user_ids': chat_user_ids
                }
            )

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_chat_group(
            rocket_admin: RocketChat, task: Task, group: TaskGroup = None
    ) -> Optional[TaskGroup]:
        """
        Create chat group and add task participants to created group
        """
        chat_group_title = '{}-{}'.format(slugify(task.title), task.pk)
        chat_group = rocket_admin.groups_create(
            chat_group_title,
            members=[
                get_chat_user(x).username for x in
                task.participants.all()
            ] + [get_chat_user(task.owner).username]
        )
        if chat_group.json().get('success'):
            if group is not None:
                group.title = chat_group_title
                group.save(update_fields=['title'])
                return group
            else:
                return TaskGroup.objects.create(
                    title=chat_group_title,
                    task=task,
                    group_id=chat_group.json()['group']['_id']
                )
        return


class ChatUserProfileView(generics.RetrieveAPIView):
    """
    Endpoint for chat user profile
    """
    queryset = UserChat.objects.all()
    lookup_field = 'chat_user_id'
    serializer_class = UserChatSerializer
    permission_classes = [IsAuthenticated]

class DecisionPollVoteViewSet(viewsets.ModelViewSet):
    serializer_class = DecisionPollVoteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = UserChat.objects.filter(user=self.request.user).first()
        serializer.save(chat_user_id=user.chat_user_id)

    def get_queryset(self):
        user = UserChat.objects.filter(user=self.request.user).first()
        return DecisionPollVote.objects.filter(chat_user_id=user.chat_user_id).order_by('-id').distinct()

