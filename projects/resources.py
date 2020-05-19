from import_export import resources

from .models import Question


class QuestionIdeaResource(resources.ModelResource):

    class Meta:
        model = Question
        exclude = ()

    def get_queryset(self):
        return super().get_queryset().filter(stage='idea')


class QuestionStartupResource(resources.ModelResource):

    class Meta:
        model = Question
        exclude = ()

    def get_queryset(self):
        return super().get_queryset().filter(stage='startup')

class QuestionRegistrationResource(resources.ModelResource):

    class Meta:
        model = Question
        exclude = ()

    def get_queryset(self):
        return super().get_queryset().filter(stage='registration')
