from import_export import resources

from .models import Page, Message


class PageResource(resources.ModelResource):

    class Meta:
        model = Page
        exclude = ()


class MessageResource(resources.ModelResource):

    class Meta:
        model = Message
        exclude = ()
