from django.contrib import admin

from .models import (
    Expertise, Experience, HourlyBudget, Availability, HighestQualification, Role, Department, TeamSize, State, Country, AvailabilityDaysPerYear, Programs, University, Campus, Hobbies,
    Parameter, Bank
)
from import_export.admin import ImportExportModelAdmin


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
	list_display = ('title', 'description', 'is_active')
	list_filter = ('title', 'is_active')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = ('title', 'description','department','is_active')
	list_filter = ('title','department','is_active')

@admin.register(Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
	list_display = ('title', 'description','role','is_active')
	list_filter = ('title','role','is_active')

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title','is_active')

@admin.register(HourlyBudget)
class HourlyBudgetAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title','is_active')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title','is_active')

@admin.register(Programs)
class ProgramsAdmin(admin.ModelAdmin):
	list_display = ('title','highest_qualification', 'is_active')
	list_filter = ('title','highest_qualification', 'is_active')

class ProgramsAdminInline(admin.TabularInline):
	model = Programs
	extra = 0

@admin.register(HighestQualification)
class HighestQualificationAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title','is_active')
	inlines = (ProgramsAdminInline,)

class CampusAdminInline(admin.TabularInline):
	model = Campus
	extra = 0

@admin.register(University)
class UniversityAdmin(ImportExportModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title','is_active')
	inlines = (CampusAdminInline,)

@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title', 'is_active')


@admin.register(TeamSize)
class TeamSizeAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title','is_active')

class StateAdminInline(admin.TabularInline):
	model = State
	extra = 0

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title', 'is_active')
	# filter_horizontal = ('states')
	inlines = (StateAdminInline,)

@admin.register(State)
class StateAdmin(ImportExportModelAdmin):
	list_display = ('title', 'country', 'is_active')
	list_filter = ('title', 'country', 'is_active')

@admin.register(AvailabilityDaysPerYear)
class AvailabilityDaysPerYearAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title', 'is_active')

@admin.register(Hobbies)
class HobbiesAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title', 'is_active')

@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active')
	list_filter = ('title', 'is_active')

@admin.register(Bank)
class BankAdmin(ImportExportModelAdmin):
	list_display = ('title', 'country', 'is_active')
	list_filter = ('country', 'is_active')



