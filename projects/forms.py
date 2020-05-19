from django import forms
from django.apps import apps

from .constants import (
    QUESTION_IDEA_GROUPS, QUESTION_IDEA_TYPES, QUESTION_STARTUP_GROUPS,
    QUESTION_STARTUP_TYPES, QUESTION_REGISTRATION_GROUPS, QUESTION_REGISTRATION_TYPES,
)

class QuestionIdeaAdminForm(forms.ModelForm):
    """
    Form for QuestionIdeaAdmin
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].choices = QUESTION_IDEA_GROUPS
        self.fields['question_type'].choices = QUESTION_IDEA_TYPES


class QuestionStartupAdminForm(forms.ModelForm):
    """
    Form for QuestionStartupAdmin
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].choices = QUESTION_STARTUP_GROUPS
        self.fields['question_type'].choices = QUESTION_STARTUP_TYPES

class QuestionRegistrationAdminForm(forms.ModelForm):
    """
    Form for QuestionRegistrationAdmin
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].choices = QUESTION_REGISTRATION_GROUPS
        self.fields['question_type'].choices = QUESTION_REGISTRATION_TYPES

    

