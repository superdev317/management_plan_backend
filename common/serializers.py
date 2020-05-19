from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import (
    Expertise , Experience , 
    HourlyBudget , Availability, 
    HighestQualification,Role, Department,
    TeamSize, State, Country, AvailabilityDaysPerYear,
    Programs, University, Campus, Hobbies, Parameter, Bank

)
from core.serializers import Base64ImageField, Base64FileField


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Department
    """
    class Meta:
        model = Department
        fields = ('id','title','description', 'is_active')

class ExpertiseSerializer(serializers.ModelSerializer):
    """
    Serializer for  Expertise
    """
    class Meta:
        model = Expertise
        fields = ('id','title','description','is_active')

class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for  Role
    """
    expertise = ExpertiseSerializer(required=False, many=True)
    class Meta:
        model = Role
        fields = ('id','title','description','department','is_active','expertise')
 
class FilterDepartmentListSerializer(serializers.ModelSerializer):
    """
    Serializer for Department and its dependent list viewset
    """
    role = RoleSerializer(required=False, many=True)

    class Meta:
        
        model = Department
        fields = ('id', 'title', 'description', 'is_active',
                  'role')
        depth = 1
       
class ExperienceListSerializer(serializers.ModelSerializer):
    """
    Serializer for experience Filter
    """
    class Meta:
        model = Experience
        fields = ('id', 'title','is_active')
        depth = 1
       
class AvailabilityListSerializer(serializers.ModelSerializer):
    """
    Serializer for availability Filter
    """
    class Meta:
        model = Availability
        fields = ('id', 'title','is_active')
        depth = 1
       
class HourlyBudgetListSerializer(serializers.ModelSerializer):
    """
    Serializer for hourlybudget Filter
    """
    class Meta:
        model = HourlyBudget
        fields = ('id', 'title','is_active')
        depth = 1

class ProgramsSerializer(serializers.ModelSerializer):
    """
    Serializer for Programs
    """
    class Meta:
        model = Programs
        fields = ('id','title','highest_qualification','is_active')

class HighestQualificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Highest Qualification
    """
    class Meta:
        model = HighestQualification
        fields = ('id','title','is_active')

class UniversitySerializer(serializers.ModelSerializer):
    """
    Serializer for University
    """
    class Meta:
        model = University
        fields = ('id','title','is_active')

class CampusSerializer(serializers.ModelSerializer):
    """
    Serializer for Campus
    """
    class Meta:
        model = Campus
        fields = ('id','title', 'university', 'is_active')


class TeamSizeSerializer(serializers.ModelSerializer):
    """
    Serializer for Team Size
    """
    class Meta:
        model = TeamSize
        fields = ('id','title','is_active')

class CountrySerializer(serializers.ModelSerializer):
    """
    Serializer for Country
    """
    class Meta:
        model = Country
        fields = ('id','title','is_active')

class StateSerializer(serializers.ModelSerializer):
    """
    Serializer for State
    """
    class Meta:
        model = State
        fields = ('id','title','country','is_active')

class AvailabilityDaysPerYearSerializer(serializers.ModelSerializer):
    """
    Serializer for Availability Days Per Year
    """
    class Meta:
        model = AvailabilityDaysPerYear
        fields = ('id','title','is_active')

class HobbiesSerializer(serializers.ModelSerializer):
    """
    Serializer for Hobbies
    """
    class Meta:
        model = Hobbies
        fields = ('id','title','is_active')

class ParameterSerializer(serializers.ModelSerializer):
    """
    Serializer for Parameter
    """
    class Meta:
        model = Parameter
        fields = ('id','title','is_active')

class BankSerializer(serializers.ModelSerializer):
    """
    Serializer for Bank
    """
    class Meta:
        model = Bank
        fields = ('id','title','country','is_active')
