from django.contrib import admin

from .models import Page, Message
from .resources import PageResource, MessageResource

from import_export.admin import ImportExportModelAdmin


@admin.register(Page)
class PageAdmin(ImportExportModelAdmin):
    resource_class = PageResource
    list_display = ('various', 'title')


@admin.register(Message)
class MessageAdmin(ImportExportModelAdmin):
    resource_class = MessageResource
    list_display = ('various', 'message')
