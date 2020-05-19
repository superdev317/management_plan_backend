from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import generics

from django.shortcuts import get_object_or_404

from .models import (
    Department, Role, Expertise , 
    Experience , HourlyBudget , 
    Availability, HighestQualification,
    TeamSize, State, Country,
    AvailabilityDaysPerYear, Programs, University, Campus, Hobbies, Parameter, Bank
)

from .serializers import (
    FilterDepartmentListSerializer,
    ExperienceListSerializer,
    AvailabilityListSerializer,
    HourlyBudgetListSerializer,
    HighestQualificationSerializer,
    DepartmentSerializer,
    HighestQualificationSerializer,
    ExpertiseSerializer,
    RoleSerializer,
    TeamSizeSerializer,
    StateSerializer,
    CountrySerializer,
    AvailabilityDaysPerYearSerializer,
    ProgramsSerializer,
    UniversitySerializer,
    CampusSerializer,
    HobbiesSerializer,
    ParameterSerializer,
    BankSerializer
)

from django.db.models import Q
from rest_framework import filters
import django_filters.rest_framework

class FilterDepartmentViewSet(viewsets.ModelViewSet):

    """
    Filter List
    """
    serializer_class = FilterDepartmentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
    	
        return Department.objects.all()

class ExperienceViewSet(viewsets.ModelViewSet):
    """
    Experience List
    """
    serializer_class = ExperienceListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Experience.objects.all()       

class AvailabilityViewSet(viewsets.ModelViewSet):
    """
    Availability List
    """
    serializer_class = AvailabilityListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Availability.objects.all()       

class HourlyBudgetViewSet(viewsets.ModelViewSet):
    """
    HourlyBudget List
    """
    serializer_class = HourlyBudgetListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HourlyBudget.objects.all()

class HighestQualificationViewSet(viewsets.ModelViewSet):
    """
    HighestQualification List
    """
    serializer_class = HighestQualificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HighestQualification.objects.filter(is_active=True)

    @detail_route(url_name='programs', methods=['get'])
    def programs(self, request, pk=None):
        """
        Endpoint for Country related states
        """
        serializer = ProgramsSerializer(
            Programs.objects.filter(highest_qualification_id=pk), many=True
        )
        return Response(serializer.data)

class ProgramsViewSet(viewsets.ModelViewSet):
    """
    Programs List
    """
    serializer_class = ProgramsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Programs.objects.filter(is_active=True)

class ExpertiseViewSet(viewsets.ModelViewSet):
    """
    Expertise List
    """
    serializer_class = ExpertiseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expertise.objects.filter(is_active=True)

class RoleViewSet(viewsets.ModelViewSet):
    """
    Role List
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Role.objects.filter(is_active=True)

class UniversityViewSet(viewsets.ModelViewSet):
    """
    HighSchool List
    """
    serializer_class = UniversitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return University.objects.filter(is_active=True).order_by("title")

    @detail_route(url_name='campuses', methods=['get'])
    def campuses(self, request, pk=None):
        """
        Endpoint for University related campuses
        """
        serializer = CampusSerializer(
            Campus.objects.filter(Q(university_id=pk)| Q(title__icontains='other')), many=True
        )
        return Response(serializer.data)

class CampusViewSet(viewsets.ModelViewSet):
    """
    Campus List
    """
    serializer_class = CampusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Campus.objects.filter(is_active=True)

class TeamSizeViewSet(viewsets.ModelViewSet):
    """
    TeamSize List
    """
    serializer_class = TeamSizeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TeamSize.objects.filter(is_active=True)

class CountrySet(viewsets.ModelViewSet):
    """
    Country List
    """
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Country.objects.filter(is_active=True).order_by('title')

    @detail_route(url_name='states', methods=['get'])
    def states(self, request, pk=None):
        """
        Endpoint for Country related states
        """
        serializer = StateSerializer(
            State.objects.filter(country_id=pk).order_by('title'), many=True
        )
        return Response(serializer.data)

class StateSet(viewsets.ModelViewSet):
    """
    State List
    """
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return State.objects.filter(is_active=True)


class AvailabilityDaysPerYearViewSet(viewsets.ModelViewSet):
    """
    Availability Days Per Year List
    """
    serializer_class = AvailabilityDaysPerYearSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AvailabilityDaysPerYear.objects.filter(is_active=True)

class HobbiesViewSet(viewsets.ModelViewSet):
    """
    Availability Hobbies
    """
    serializer_class = HobbiesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
    search_fields = ('title',)

    def get_queryset(self):
        return Hobbies.objects.filter(is_active=True)

class ParameterViewSet(viewsets.ModelViewSet):
    """
    Parameter End
    """
    serializer_class = ParameterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Parameter.objects.filter(is_active=True)

class BankViewSet(viewsets.ModelViewSet):
    """
    Bank End
    """
    serializer_class = BankSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bank.objects.filter(is_active=True)

   