from django.apps import AppConfig


class ActivityStreamConfig(AppConfig):
    name = 'activity_stream'

    def ready(self):
        from actstream import registry

        from projects.models import Answer, Project, Task

        registry.register(Answer)
        registry.register(Project)
        registry.register(Task)
