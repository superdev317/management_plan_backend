"""
Note: If you want add new model action, you need register model at apps.py
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from projects.models import Answer, Task

from actstream import action


@receiver(post_save, sender=Answer)
def handler_answer_activity_stream(sender, instance, created, **kwargs):
    """
    Handler save answers action
    """
    verb = 'updated'
    if created:
        verb = 'added'

    action.send(
        instance.project.owner,
        verb=verb,
        action_object=instance,
        target=instance.project
    )


@receiver(post_save, sender=Task)
def handler_task_activity_stream(sender, instance, created, **kwargs):
    """
    Handler save tasks action
    """
    verb = 'updated'
    if created:
        verb = 'added'

    action.send(
        instance.owner,
        verb=verb,
        action_object=instance,
        target=instance.milestone.project
    )
