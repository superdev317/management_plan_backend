from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import (
    User, UserProfile, Specialization, Education, WorkExperience, SecurityQuestion, KeyVal
)
from .forms import CustomUserCreationForm

from mptt.admin import DraggableMPTTAdmin


@admin.register(Specialization)
class SpecializationAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'title')
    list_display_links = ('title',)
    mptt_level_indent = 20


class EducationAdminInline(admin.TabularInline):
    model = Education
    extra = 0


class WorkExperienceAdminInline(admin.StackedInline):
    model = WorkExperience
    extra = 0


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    filter_horizontal = ('specializations', 'skills', 'employees')
    inlines = (EducationAdminInline, WorkExperienceAdminInline)

    def has_delete_permission(self, request, obj=None):
        return


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'is_staff', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)

@admin.register(SecurityQuestion)
class SecurityQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'question_type', 'is_active')
    list_filter = ('is_active',)
    filter_horizontal = ('vals',)

    def has_delete_permission(self, request, obj=None):
        return

@admin.register(KeyVal)
class KeyValAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    pass