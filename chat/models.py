from django.db import models
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.db.models.signals import post_delete, post_save, m2m_changed, pre_delete
from django.conf import settings

from accounts.models import User, UserProfile
from projects.models import Task

from .helpers import RocketChat
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.jsonb import KeyTextTransform
import sys
from rest_framework import serializers

MESSAGE_TYPE = [('opinion','opinion'),
                ('decisions','decisions'),
                ('argument','argument'),
                ('task','task'),
                ('gut_feeling','gut_feeling'),
                ('decision_poll','decision_poll'),
                ('assumption','assumption'),
                ('suggestion','suggestion'),
                ('thought_experiment','thought_experiment'),
                ('hypothesis','hypothesis')]


class UserChat(models.Model):
    """
    Model for chat user data
    """
    user = models.OneToOneField(User, related_name='chat')
    username = models.CharField(max_length=32)
    raw_password = models.CharField(max_length=16)
    auth_token = models.CharField(max_length=50, blank=True)
    chat_user_id = models.CharField(max_length=20, blank=True)


class TaskGroup(models.Model):
    """
    Model for chat groups data
    """
    task = models.OneToOneField(Task)
    group_id = models.CharField(max_length=20)
    title = models.CharField(max_length=100)


def get_chat_user(
        user: User, commit: bool = True, rocket_admin: RocketChat = None
) -> UserChat:
    """
    Function get or create chat user
    """
    if user.__str__():
        chat_user, created = UserChat.objects.get_or_create(
            user=user, defaults={
                'username': user.username,
                'raw_password': get_random_string(length=16)
            }
        )

        if rocket_admin is None:
            rocket_admin = RocketChat(
                settings.ROCKETCHAT_USER,
                settings.ROCKETCHAT_PASSWORD
            )

        if chat_user.chat_user_id:
            if not rocket_admin.users_info(chat_user.chat_user_id).json()['success']:
                created = True

        if created:
            rocket_user = rocket_admin.users_create(
                email= user.__str__(),
                name=user.first_name,
                password=chat_user.raw_password,
                username=chat_user.username
            )
            chat_user.chat_user_id = rocket_user.json()['user']['_id']
            if commit:
                chat_user.save(update_fields=['chat_user_id'])
        return chat_user
    else:
        raise serializers.ValidationError({"email":'Email is Required.'})




class MessageType(models.Model):
    """
    Model for different type of messages for particular chat groups
    """
    group_id = models.CharField(max_length=100, blank=True, null=True)
    message_id = models.CharField(max_length=50, blank=True, null=True)
    message_type = models.CharField(choices=MESSAGE_TYPE, max_length=30, blank=True, null=True)
    options = JSONField(blank=True, null=True)
    # options = models.CharField(blank=True, null=True)
    voting = JSONField(blank=True, null=True)
    chat_user_id = models.CharField(max_length=50, blank=True, null=True)
    parent_message_id = models.CharField(max_length=50, blank=True, null=True)


class DecisionPollVote(models.Model):
    """
    Model for Decision Poll Voting
    """
    message_id = models.CharField(max_length=50, blank=True, null=True)
    options = models.IntegerField(blank=True, null=True)
    chat_user_id = models.CharField(max_length=50, blank=True, null=True)

@receiver(post_save, sender=DecisionPollVote)
def calculate_vote(sender, instance, created, **kwargs):
    # if created:
    voters = 0
    message_type_id = MessageType.objects.filter(message_id=instance.message_id).first()
    if message_type_id:
        group_obj = TaskGroup.objects.filter(group_id=message_type_id.group_id).first()
        task_obj = Task.objects.filter(id=group_obj.task.id).first()
        participants = task_obj.participants.all()

        if not message_type_id.voting:
            voting = []
            for i in message_type_id.options:
                voting.append({"id":i["id"],"option":i["option"],"votes":0,"percentage":0.0})
            message_type_id.voting = voting
            message_type_id.save()
        for i in message_type_id.voting:
            if i["id"] == instance.options:
                i["votes"] += 1
                if len(participants) > 0:
                    i["percentage"] = (i["votes"]/len(participants))*100
        message_type_id.save()           

@receiver(post_save, sender=Task)
def calculate_vote_task(sender, instance, created, **kwargs):
    if not created:
        participants = instance.participants.all()
        group_obj = TaskGroup.objects.filter(task=instance).first()
        if group_obj:
            message_type_obj = MessageType.objects.filter(group_id=group_obj.group_id).first()
            if message_type_obj:
                if not message_type_obj.voting:
                    voting = []
                    if message_type_obj.options:
                        for i in message_type_obj.options:
                            voting.append({"id":i["id"],"option":i["option"],"votes":0,"percentage":0.0})
                        message_type_obj.voting = voting
                        message_type_obj.save()
                if message_type_obj.voting:
                    for i in message_type_obj.voting:
                        if len(participants) > 0:
                            i["percentage"] = (i["votes"]/len(participants))*100
                    message_type_obj.save()


# We need exclude chat signals from tests
if 'test' not in sys.argv:

    @receiver(post_delete, sender=User)
    def handler_delete_user(sender, instance, **kwargs):
        """
        Signal delete user from chat
        """
        rocket_admin = RocketChat(
            settings.ROCKETCHAT_USER,
            settings.ROCKETCHAT_PASSWORD
        )
        rocket_admin.users_delete(instance.chat.chat_user_id)


    @receiver(post_save, sender=User)
    @receiver(post_save, sender=UserProfile)
    def handler_user_update_data(sender, instance, **kwargs):
        """
        Signal update user data when user update his profile
        """
        if sender == User:
            user = instance
        else:
            user = instance.user

        try:
            chat_user = UserChat.objects.get(user=user)
            if chat_user.username != user.username:
                chat_user.username = user.username
                chat_user.save(update_fields=['username'])
        except UserChat.DoesNotExist:
            pass


    @receiver(pre_delete, sender=Task)
    def handler_task_delete_channel(sender, instance, **kwargs):
        """
        Signal delete chat group and task group data
        """
        rocket_admin = RocketChat(
            settings.ROCKETCHAT_USER,
            settings.ROCKETCHAT_PASSWORD
        )

        for participant in instance.participants.all():
            chat_user = get_chat_user(participant, rocket_admin=rocket_admin)
            rocket = RocketChat(
                headers={
                    'X-Auth-Token': chat_user.auth_token,
                    'X-User-Id': chat_user.chat_user_id
                }
            )
            try:
                task_group = TaskGroup.objects.get(task=instance)
                rocket.groups_close(task_group.group_id)
                message_type_ids = MessageType.objects.filter(group_id=task_group.group_id).values_list('message_id',flat=True)
                decision_poll_obj = DecisionPollVote.objects.filter(message_id__in=message_type_ids)
                decision_poll_obj.delete()
                message_type_obj = MessageType.objects.filter(group_id=task_group.group_id)
                message_type_obj.delete()
                task_group.delete()
            except TaskGroup.DoesNotExist:
                pass

class DirectGroup(models.Model):
    """
    Model for Direct Group data
    """
    group_id = models.CharField(max_length=100)
    participant1 = models.CharField(max_length=100)
    participant2 = models.CharField(max_length=100)


#     @receiver(m2m_changed, sender=Task.participants.through)
#     def handler_change_task_participants(sender, instance, action, **kwargs):
#         """
#         Signal update chat group participants
#         """
#         if action in ['post_add', 'post_remove']:
#             rocket_admin = RocketChat(
#                 settings.ROCKETCHAT_USER,
#                 settings.ROCKETCHAT_PASSWORD
#             )

#             for user in User.objects.filter(pk__in=list(kwargs['pk_set'])):
#                 chat_user = get_chat_user(user, rocket_admin=rocket_admin)

#                 try:
#                     group = TaskGroup.objects.get(task=instance)
#                 except TaskGroup.DoesNotExist:
#                     return

#                 if action == 'post_add':
#                     rocket_admin.groups_invite(
#                         group.group_id, chat_user.chat_user_id
#                     )

#                 if action == 'post_remove':
#                     rocket_admin.groups_kick(
#                         group.group_id, chat_user.chat_user_id
#                     )
