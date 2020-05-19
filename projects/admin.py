from django.contrib import admin

from .models import (
    Project, Answer, TaskStatus, TaskTag, Task, QuestionIdea, QuestionStartup,
    TaskRule, Milestone, AnswerImage, AnswerSpreadsheet, AnswerDiagram, KeyVal,
    TaskDocument, QuestionRegistration ,Question, ProjectRegistrationType, AnswerDate ,AnswerMultiList
    ,AnswerRadio, AnswerList, ProjectRegistrationFeature, ProjectRegistrationPackage, PackageFeaturevalues
    ,ProjectFundType, PackageList , AnswerPowerPoint, DependencyTask, AnswerSwot, PredefinedMilestone,ToDoList,Time,Notification
    
)
from .forms import QuestionIdeaAdminForm, QuestionStartupAdminForm, QuestionRegistrationAdminForm
from .resources import QuestionIdeaResource, QuestionStartupResource, QuestionRegistrationResource

from import_export.admin import ImportExportModelAdmin
from django.db.models import Q

@admin.register(DependencyTask)
class DependencyTaskAdmin(admin.ModelAdmin):
    pass

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass

@admin.register(ToDoList)
class ProjectToDoListAdmin(admin.ModelAdmin):
    list_display = ('project', 'task', 'task_description', 'remind', 'remind_me',
                    'start_on','let_system_do_it',)
@admin.register(Time)
class ProjectToDoListTimeAdmin(admin.ModelAdmin):
    pass

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_visible', 'owner', 'status', 'date_start',
                    'date_end')
    list_filter = ('is_visible', 'status', 'owner')
    filter_horizontal = ('participants',)

@admin.register(ProjectRegistrationFeature)
class ProjectRegistrationFeatureAdmin(admin.ModelAdmin):
    list_display = ('title','order','is_active')
    list_filter = ('title','order','is_active')

@admin.register(ProjectRegistrationType)
class ProjectRegistrationTypeAdmin(admin.ModelAdmin):
    list_display = ('title','amount' ,'description','is_active')
    list_filter = ('title','amount','description','is_active')
    # filter_horizontal = ('features',)

class PackageFeaturevaluesAdminInline(admin.TabularInline):
    model = PackageFeaturevalues
    extra = 0

@admin.register(ProjectRegistrationPackage)
class ProjectRegistrationPackageAdmin(admin.ModelAdmin):
    list_display = ('title','description','amount','currency','get_registration_type_name','is_active')
    list_filter = ('title','amount','description','registration_type','is_active')
    inlines = (PackageFeaturevaluesAdminInline,)

    def get_registration_type_name(self, obj):
        return obj.registration_type.title

@admin.register(QuestionIdea)
class QuestionAdmin(ImportExportModelAdmin):
    resource_class = QuestionIdeaResource
    form = QuestionIdeaAdminForm
    list_display = ('title', 'order', 'question_type', 'group','parent_question', 'is_active')
    list_filter = ('is_active',)
    filter_horizontal = ('vals',)
    exclude = ('stage',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(stage='idea')
        return qs

    def save_model(self, request, obj, form, change):
        obj.stage = 'idea'
        obj.save()


@admin.register(QuestionStartup)
class QuestionStartupAdmin(ImportExportModelAdmin):
    resource_class = QuestionStartupResource
    form = QuestionStartupAdminForm
    list_display = ('title', 'order', 'question_type', 'group', 'parent_question', 'is_active')
    list_filter = ('is_active',)
    filter_horizontal = ('vals',)
    exclude = ('stage',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(stage='startup')
        return qs

    def save_model(self, request, obj, form, change):
        obj.stage = 'startup'
        obj.save()

@admin.register(QuestionRegistration)
class QuestionRegistrationAdmin(ImportExportModelAdmin):
    resource_class = QuestionRegistrationResource
    form = QuestionRegistrationAdminForm
    list_display = ('title', 'order', 'question_type', 'group', 'model', 'parent_question', 'is_active')
    list_filter = ('is_active',)
    filter_horizontal = ('vals',)
    exclude = ('stage',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(stage='registration')
        return qs

    def save_model(self, request, obj, form, change):
        obj.stage = 'registration'
        obj.save()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent_question":
            kwargs["queryset"] = Question.objects.filter(stage='registration')
        return super(QuestionRegistrationAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(KeyVal)
class KeyValAdmin(admin.ModelAdmin):
    list_display = ('id','value')
    pass

class AnswerImageAdminInline(admin.TabularInline):
    model = AnswerImage

class AnswerSwotAdminInline(admin.TabularInline):
    model = AnswerSwot


class AnswerSpreadsheetAdminInline(admin.TabularInline):
    model = AnswerSpreadsheet


class AnswerDiagramAdminInline(admin.TabularInline):
    model = AnswerDiagram

class AnswerListAdminInline(admin.TabularInline):
    model = AnswerList

class AnswerDateAdminInline(admin.TabularInline):
    model = AnswerDate

class AnswerMultiListAdminInline(admin.TabularInline):
    model = AnswerMultiList

class AnswerRadiAdminInline(admin.TabularInline):
    model = AnswerRadio

class AnswerPowerPointAdminInline(admin.TabularInline):
    model = AnswerPowerPoint



@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    inlines = (AnswerImageAdminInline, AnswerSpreadsheetAdminInline,
               AnswerDiagramAdminInline,  AnswerDateAdminInline
               ,AnswerMultiListAdminInline , AnswerRadiAdminInline, AnswerListAdminInline , AnswerPowerPointAdminInline,AnswerSwotAdminInline
               )


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')


@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    pass


class TaskRuleAdminInline(admin.TabularInline):
    model = TaskRule
    extra = 0


class TaskDocumentAdminInline(admin.StackedInline):
    model = TaskDocument
    extra = 0




@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'assignee', 'complete_percent')
    list_filter = ('status',)
    filter_horizontal = ('participants', 'tags')
    inlines = (TaskRuleAdminInline, TaskDocumentAdminInline)

#predefined milestone (templates)
@admin.register(PredefinedMilestone)
class PredefinedMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'description',)
    list_filter = ('title',)

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'description', 'date_start',
                    'date_end')
    list_filter = ('project', 'title')

@admin.register(ProjectFundType)
class ProjectFundTypeAdmin(admin.ModelAdmin):
    list_display = ('title','description','is_active')
    list_filter = ('title','description','is_active')

@admin.register(PackageList)
class PackageListAdmin(admin.ModelAdmin):
    list_display = ('title','amount','position_name','position_number','is_active')
    list_filter = ('title','amount','is_active')
