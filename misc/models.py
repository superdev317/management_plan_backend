from django.db import models

from ckeditor.fields import RichTextField


class Page(models.Model):
    """
    Model for pages
    """
    VARIOUS = (
        #('tos', 'Privacy policy Terms of use'),
        ('tos', 'tos'),
        ('privacy', 'Privacy policy'),
        ('terms', 'Terms of use'),
    )
    various = models.CharField(max_length=30, choices=VARIOUS, unique=True)
    title = models.CharField(max_length=20)
    description = RichTextField()

    def __str__(self):
        return self.title


class Message(models.Model):
    """
    Model for some strings or simple messages.
    For example bubbles ot titles
    """
    VARIOUS = (
        ('new_idea_start_screen', 'New Idea start screen'),
        ('new_idea_flow_bubble_express', 'New Idea flow bubble Express'),
        ('new_idea_flow_bubble_develop', 'New Idea flow bubble Develop'),
        ('new_idea_flow_bubble_visual', 'New Idea flow bubble Visual'),
        ('new_idea_flow_bubble_target', 'New Idea flow bubble Target'),
        ('new_idea_flow_bubble_plan', 'New Idea flow bubble Plan'),
        ('creator_start', 'Home screen Creator'),
        ('backer_start', 'Home screen Backer'),
        ('employee_start', 'Home screen Employee'),
        ('start_screen', 'Start screen'),
        ('role_selection', 'Role selection screen'),
        ('notify_new_idea_bubbles_not_completed', 'Notification: New idea bubbles not completed'),
        ('notify_lazy_user_update_profile', 'Notification: temporary account - to update the profile'),
        ('notify_not_implemented_message', 'Notification: Not implemented message'),
        ('photo_upload_field_empty', 'Photo upload field - empty'),
        ('photo_upload_field_filled', 'Photo upload field - filled'),
        ('edit_profile_photo', 'Edit profile photo'),
    )
    various = models.CharField(max_length=30, choices=VARIOUS, unique=True)
    message = models.CharField(max_length=50)

    def __str__(self):
        return self.message
