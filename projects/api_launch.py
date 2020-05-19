from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import ( 
    ProjectLaunchType,
    ProjectFundType , 
    ProjectFund , 
    PackageList,
    ProjectPackageDetails,
    ProjectCompanyRole,
    ProjectBackerFund,
    ProjectBackerLaunch,
    Transactions
)

from .serializers import (
    LaunchListSerializer,
    ProjectFundTypeSerializer,
    ProjectFundSerializer,
    PackageListSerializer,
    ProjectPackageDetailsSerializer,
    ProjectCompanyRoleSerializer,
    ProjectBackerFundSerializer,
    ProjectBackerLaunchSerializer,
    ProjectBackerFundListSerializer,
    CurrentUserTransactonSerializer
)
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import filters
from accounts.models import User
from rest_framework import serializers

class LaunchTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD for Launch Type
    """
    serializer_class = LaunchListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectLaunchType.objects.filter(is_active=True).order_by('id')

class ComapanyRoleViewSet(viewsets.ModelViewSet):
    """
    CRUD for Company Role
    """
    serializer_class = ProjectCompanyRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectCompanyRole.objects.filter(is_active=True)

class FundTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD for Fund Type
    """
    serializer_class = ProjectFundTypeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectFundType.objects.filter(is_active=True).order_by('id')

class ProjectFundViewSet(viewsets.ModelViewSet):
    """
    CRUD for Fund Form
    """
    serializer_class = ProjectFundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectFund.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

class PackageListViewSet(viewsets.ModelViewSet):
    """
    CRUD for Package List
    """
    serializer_class = PackageListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PackageList.objects.filter(is_active=True).order_by('id')

class ProjectPackageDetailsViewSet(viewsets.ModelViewSet):
    """
    CRUD for Fund Form
    """
    serializer_class = ProjectPackageDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectPackageDetails.objects.filter(is_active=True).order_by('id')

class ProjectBackerFundViewSet(viewsets.ModelViewSet):
    """
    CRUD for Fund Form Backer
    """
    serializer_class = ProjectBackerFundSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('fund__fund__title','fund__project__title')

    def get_queryset(self):
        return ProjectBackerFund.objects.filter(backer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(backer=self.request.user)

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

            total_amount = 0
            wallet_amount = Transactions.get_wallet_amount(self,user=self.request.user)
            for d in data:
                fund = ProjectFund.objects.filter(id=d.get("fund")).first()

                if fund:
                    if fund.fund.id in [1,4]:
                        amount = d["quantity"] * fund.price_security.amount
                    elif fund.fund.id in [3,5]:
                        amount = d["sanction_amount"]["amount"]
                    elif fund.fund.id in [7,8]:
                        amount = sum([i["amount"]["amount"] for i in d["company_shares_backer"]])
                    elif fund.fund.id in [6]:
                        amount =fund.current_valuation.amount

                    total_amount += int(amount)
            if wallet_amount < total_amount:
                raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')

        return super().get_serializer(*args, **kwargs)

    @list_route(url_name='details', url_path='details')
    def details(self, request):
        """
        Endpoint for funding details
        """
        self.serializer_class = ProjectBackerFundListSerializer
        queryset = ProjectBackerFund.objects.filter(backer=self.request.user)

        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ProjectBackerLaunchViewSet(viewsets.ModelViewSet):
    """
    CRUD for Launch Form Backer
    """
    serializer_class = ProjectBackerLaunchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectBackerLaunch.objects.filter(backer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(backer=self.request.user)

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

class CurrentUserTransactonView(generics.RetrieveAPIView):
    """
    Endpoint for current user transactions list
    """
    serializer_class = CurrentUserTransactonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('mode','remark','amount',)

    def get_object(self):
        return User.objects.get(id=self.request.user.id)
