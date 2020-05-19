from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import generics
from django.shortcuts import get_object_or_404
from digital_sign.views import create_signature,signature_status
import mimetypes
from django.core.files.storage import default_storage
from core.utils import convert_file_to_base64



from .models import (
	 Job , 
	 InterviewSchedule ,
	 JobApply, 
	 InterviewReschedule, 
	 EmployeeHire, 
	 RecruitmentEmployeeStatus,
	 DocumentsToDocusign,
)


from .serializers import (
    JobSerializer,
    InterviewSerializer,
    JobApplySerializer,
    JobApplyDetailsSerializer,
    EmployeeJobResponseSerializer,
    InterviewRescheduleSerializer,
    EmployeeDirectHireResponseSerializer,
    EmployeeHireSerializer,
    EmployeeListForJobSerializer,
    CurrentEmployerSerializer,
    JobDetailsSerializer,
    DirectInterviewRequestSerializer,
    DirectHireSerializer,
    AverageRatingSerializer,
	DocumentsToDocusignSerializer,
	MetricesSerializer
)
from rest_framework import filters 
import django_filters.rest_framework
from accounts.models import (
	User, UserProfile,EmployeeProfessionalDetails, EmployeeEmploymentDetails, EmployeeBasicDetails
)
from common.models import Department, Role, Expertise, Experience, HourlyBudget, Availability
from django.db.models import Q
import json
from django.http import HttpResponse
from datetime import datetime, date, timedelta
from projects.models import Project, Task, TaskAssignDetails, WorkSession, Transactions
from projects.serializers import CompletedTasksSerializer, TransactionsSerializer, WorkSessionSerializer
from rest_framework import status, generics
from rest_framework import serializers
from expenses.serializers import SalaryPaymentSerializer
from expenses.models import SalaryPayment
import re
import pytz
import requests
from django.utils.timezone import utc


class JobPostViewSet(viewsets.ModelViewSet):

	"""
	Crud Operation for job post
	"""
	serializer_class = JobSerializer
	permission_classes = [IsAuthenticated]
	#http_method_names = ['get', 'post', 'head','put']

	def get_queryset(self):
		return Job.objects.filter(~Q(date_end__lte = date.today()) & Q(owner=self.request.user))
		
	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)

	def perform_update(self, serializer):
		serializer.save(owner=self.request.user)

	@detail_route(url_name='project_jobs', methods=['get','post'])
	def project_jobs(self, request, pk=None):
		"""
		Endpoint for project jobs
		"""
		if request.method == 'POST':
			s = JobSerializer(data=request.data)
			s.is_valid(raise_exception=True)
			self.perform_create(s)
			project = Project.objects.get(id=pk)
			s.instance.project = project
			s.instance.owner = self.request.user
			s.instance.save()

		serializer = JobSerializer(
			Job.objects.filter(~Q(date_end__lte = date.today()) & Q(owner=self.request.user) & Q(project_id=pk)), many=True
		)
		return Response(serializer.data)


class JobListView(viewsets.ModelViewSet):

	serializer_class = JobDetailsSerializer
	permission_classes = [IsAuthenticated,]
	http_method_names = ['get', 'head']

	# Show all of the Jobs in particular experties, department and role
	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
	filter_fields = ('department', 'expertise', 'experience', 'role', 'hourlybudget', 'availability',)

	def get_queryset(self):
		return Job.objects.filter(date_start__lte = date.today(),date_end__gte = date.today(),status='publish').order_by('-id')


class InterviewScheduleViewSet(viewsets.ModelViewSet):
	"""
	Interview Schedule post
	"""
	serializer_class = InterviewSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return InterviewSchedule.objects.filter(owner=self.request.user)

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)

	def perform_update(self, serializer):
		serializer.save(owner=self.request.user)

class DirectInterviewScheduleViewSet(viewsets.ModelViewSet):
	"""
	Crud Operation for Direct Interview Schedule post
	"""
	serializer_class = DirectInterviewRequestSerializer
	permission_classes = [IsAuthenticated]
	http_method_names = ['get', 'put', 'head']
	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)

	def get_queryset(self):
		queryset = InterviewSchedule.objects.filter(is_direct_hire=True)
		queryset = queryset.filter(employee=self.request.user.userprofile).order_by('-id')
		return queryset

	@detail_route(url_name='join', methods=['get','put'])
	def join(self, request, pk=None):
		"""
		Endpoint for join company
		"""
		self.serializer_class = EmployeeHireSerializer
		obj = InterviewSchedule.objects.get(id=pk)
		if obj.job:
			employee_hire = EmployeeHire.objects.get(emp_id=obj.employee,job=obj.job,letter_through='direct_interview')
		else:
			employee_hire = EmployeeHire.objects.get(emp_id=obj.employee,job=None,letter_through='direct_interview')

		serializer = EmployeeHireSerializer(
            EmployeeHire.objects.filter(emp_id=obj.employee,job=obj.job).first()
        )
		if request.method == 'PUT':
			# if request.data.get('digital_sign_employee'):
			# 	employee_hire.digital_sign_employee = request.data.get('digital_sign_employee')
			employee_hire.status = 'accept'
			employee_hire.accept_nda = request.data.get('accept_nda')
			employee_hire.save()
			# obj.status = 'offer_accept'
			# obj.save()
			emp_status = RecruitmentEmployeeStatus.objects.get(employee=self.request.user.userprofile,owner=obj.owner, project=employee_hire.project)
			emp_status.status = 'join'
			emp_status.save()
			obj.owner.userprofile.employees.add(obj.employee.id)
			obj.owner.userprofile.save()
		return Response(serializer.data)

	@detail_route(url_name='reject_interview',methods=['put'])
	def reject_interview(self, request, pk=None):
	    """
	    Endpoint for Direct interview request rejection
	    """
	    
	    interview_obj = InterviewSchedule.objects.get(id=pk)
	    interview_obj.status = 'decline'
	    interview_obj.save()
	    return Response(InterviewSerializer(interview_obj).data)

	@detail_route(url_name='reject_offer',methods=['put'])
	def reject_offer(self, request, pk=None):
		"""
		Endpoint for Direct interview request offer rejection
		"""
		obj = InterviewSchedule.objects.get(id=pk)
		if obj.job:
			hire_obj = EmployeeHire.objects.get(emp_id=obj.employee,job=obj.job,letter_through='direct_interview')
		else:
			hire_obj = EmployeeHire.objects.get(emp_id=obj.employee,job=None,letter_through='direct_interview')
		hire_obj.status = 'reject'
		hire_obj.save()
		# obj.status = 'offer_reject'
		# obj.save()
		return Response(EmployeeHireSerializer(hire_obj).data)


class JobApplyViewSet(viewsets.ModelViewSet):

	"""
	Crud Operation for job application
	"""
	serializer_class = JobApplySerializer
	permission_classes = [IsAuthenticated]
	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)

	def get_queryset(self):
		return JobApply.objects.filter(employee=self.request.user.userprofile).order_by('-id')   	

	def retrieve(self, request, *args, **kwargs):
	    self.serializer_class = JobApplyDetailsSerializer
	    return super().retrieve(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			jobapply_obj = JobApply.objects.get(employee=self.request.user.userprofile,job=request.data.get('job'))

		except JobApply.DoesNotExist:
			serializer.save(employee=self.request.user.userprofile,status='applied')
			
		return Response(
			serializer.data, status=status.HTTP_201_CREATED
		)

	# def perform_create(self, serializer):
	# 	serializer.save(employee=self.request.user.userprofile,status='applied')

	@detail_route(url_name='interview', methods=['get','put'])
	def interview(self, request, pk=None):
	    """
	    Endpoint for job_apply interview
	    """
	    self.serializer_class = InterviewSerializer
	    
	    if request.method == 'PUT':
	    	interview = InterviewSchedule.objects.filter(job_application=pk).first()
	    	interview.status = request.data.get('status')
	    	interview.save()
	    	reschedule_obj = InterviewReschedule.objects.filter(interview_id=interview).order_by('-id').first()
	    	if reschedule_obj:
	    		if reschedule_obj.is_creator:
	    			interview.interview_date_time = reschedule_obj.reschedule_interview_date_time_creator
	    			interview.save()
	    			reschedule_obj.status = 'accept'
	    			reschedule_obj.save()
	    		if not reschedule_obj.reschedule_interview_date_time_creator:
	    			reschedule_obj.delete()

	    serializer = InterviewSerializer(
	        InterviewSchedule.objects.filter(job_application=pk).first()
	    )

	    return Response(serializer.data)

	@detail_route(url_name='join', methods=['get','put'])
	def join(self, request, pk=None):
		"""
		Endpoint for join company
		"""
		self.serializer_class = EmployeeHireSerializer
		obj = JobApply.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.get(emp_id=obj.employee,job=obj.job,letter_through='job_application')
		serializer = EmployeeHireSerializer(
            EmployeeHire.objects.filter(emp_id=obj.employee,job=obj.job).first()
        )
		if request.method == 'PUT':
			# if request.data.get('digital_sign_employee'):
			# 	employee_hire.digital_sign_employee = request.data.get('digital_sign_employee')
			employee_hire.status = 'accept'
			employee_hire.accept_nda = request.data.get('accept_nda')
			employee_hire.save()
			# obj.status = 'offer_accept'
			# obj.save()
			emp_status = RecruitmentEmployeeStatus.objects.get(employee=self.request.user.userprofile,owner=obj.job.owner, project=employee_hire.project)
			emp_status.status = 'join'
			emp_status.save()

			obj.job.owner.userprofile.employees.add(obj.employee.id)
			obj.job.owner.userprofile.save()
		return Response(serializer.data)

	@detail_route(url_name='reject_interview',methods=['put'])
	def reject_interview(self, request, pk=None):
	    """
	    Endpoint for job_apply interview rejection
	    """
	    
	    interview_obj = InterviewSchedule.objects.filter(job_application=pk).first()
	    interview_obj.status = 'decline'
	    interview_obj.save()
	    # obj = JobApply.objects.get(id=pk)
	    # obj.status = 'int_reject'
	    # obj.save()

	    return Response(InterviewSerializer(interview_obj).data)

	@detail_route(url_name='reject_offer',methods=['put'])
	def reject_offer(self, request, pk=None):
	    """
	    Endpoint for job_apply offer rejection
	    """
	    obj = JobApply.objects.get(id=pk)
	    hire_obj = EmployeeHire.objects.get(emp_id=obj.employee,job=obj.job,letter_through='job_application')
	    hire_obj.status = 'reject'
	    hire_obj.save()
	    # obj.status = 'offer_reject'
	    # obj.save()

	    return Response(EmployeeHireSerializer(hire_obj).data)


class EmployeeJobResponseViewSet(viewsets.ModelViewSet):
	"""
	Endpoint for employee job response
	"""
	serializer_class = EmployeeJobResponseSerializer
	permission_classes = [IsAuthenticated,]

	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
	search_fields = ('employee__first_name','employee__last_name','job__title')
	queryset = JobApply.objects.filter(status="applied").order_by('-id')  

	@detail_route(url_name='project_job_response', methods=['get','option','head'])
	def project_job_response(self, request, pk=None):
		"""
		Endpoint for project job responses
		"""
		queryset = JobApply.objects.filter(job__project__id=pk).order_by('-id') #status__in=("applied","schedule","offered"),
		queryset = self.filter_queryset(queryset)

		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)


	@detail_route(url_name='send_appointment', methods=['post'])
	def send_appointment(self, request, pk=None):
		"""
		Endpoint for job applied hire employee
		"""
		self.serializer_class = EmployeeHireSerializer
		obj = JobApply.objects.get(id=request.data.get('emp_id'))
		employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=obj.job, project=request.data.get('project'), letter_through='job_application').first()
		create_date = datetime.strptime(request.data.get('onDate'),'%m-%d-%Y').strftime('%Y-%m-%d')
		project = Project.objects.get(id=request.data.get('project'))
		data = {
			'emp_id' : obj.employee,
			'name' : request.data.get('name'),
			'create_date' : create_date,
			'address' : request.data.get('address'),
			'state' : request.data.get('state'),
			'city' : request.data.get('city'),
			'zip' : request.data.get('zip'),
			'working_title' : request.data.get('workingTitle'),
			'department' : request.data.get('department'),
			'duration' : request.data.get('duration'),
			'joining_date' : request.data.get('beginningDate'),
			'salary_parameters' : request.data.get('salaryParameters'),
			'responsibilities1' : request.data.get('responsibilities1'), 
			'responsibilities2' : request.data.get('responsibilities2'), 
			'responsibilities3' : request.data.get('responsibilities3'), 
			'department_contribution' : request.data.get('departmentContribution'),
			'availability' : request.data.get('availability'),
			'project' : project,
			'job' : obj.job,
			'letter_through' : 'job_application',
			'creator_email':request.data.get('creator_email')
		}
		docusign_data = {
			'emp_id' : obj.employee.user_id,
			'creator_email':request.data.get('creator_email'),
			'document' :request.data.get('document').split(',')[1],
			'document_name' :request.data.get('document_name'),
			'creatorXposition':request.data.get('creatorXposition'),
			'creatorYposition':request.data.get('creatorYposition'),
			'employeeXposition':request.data.get('employeeXposition'),
			'employeeYposition':request.data.get('employeeYposition'),
			'nda':False
		}

		if not employee_hire:
			employee_hire = EmployeeHireSerializer.create(EmployeeHireSerializer(), validated_data=data)
			docusign_url = create_signature(docusign_data)
			docusign_doc = {'document':request.data.get('document'),'document_name':request.data.get('document_name')}
			s = DocumentsToDocusignSerializer(data=docusign_doc)
			s.is_valid(raise_exception=True)     
			s.save(employeehire_details=employee_hire,enveloped=docusign_url['envelopeId'])
			
			EmployeeHire.objects.filter(id=employee_hire.id).update(envelop=docusign_url['envelopeId'])
	
			obj.status = 'offered'
			obj.save()
			

		# obj.interview_schedule.status = 'hire'
		emp_status, created = RecruitmentEmployeeStatus.objects.get_or_create(owner=self.request.user,employee=obj.employee, project=employee_hire.project)
		emp_status.status = 'hire'
		emp_status.save()
		# obj.save()
		response_data = {
			'id' : pk,
			'emp_id' : obj.employee.id,
			'status' : emp_status.status
		
		}
		return Response(response_data)

	@detail_route(url_name='hire', methods=['get'])
	def hire(self, request, pk=None):
		"""
		Endpoint for hire employee
		"""
		obj = JobApply.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=obj.job)
		data = {
					'name': obj.employee.first_name + ' ' + obj.employee.last_name,
					'address': obj.employee.basic_details.address_line1,
					'city': obj.employee.basic_details.city,
					'state': obj.employee.basic_details.state.title if obj.employee.basic_details.state else '',
					'zip': obj.employee.basic_details.pin_code,

				}
		return Response(data)

	@detail_route(url_name='docusign_status', url_path='docusign-status/(?P<envelop_id>[a-zA-Z0-9-]+)')
	def docusign_status(self, request,pk=None,envelop_id=None):
		"""
		Endpoint for  docusign status
		"""
		obj = JobApply.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.get(envelop=envelop_id)
		data={
			'emp_id':obj.employee.user_id,
			'creator_email':employee_hire.creator_email,
			'envelop_id':envelop_id
		}
		final_url = signature_status(data)

		return Response(final_url)

	@detail_route(url_name='reject',methods=['put'])
	def reject(self, request, pk=None):
	    """
	    Endpoint for Direct interview request rejection
	    """
	    
	    obj = JobApply.objects.get(id=pk)
	    obj.status = 'reject'
	    obj.save()
	    return Response(EmployeeJobResponseSerializer(obj).data)
	
class InterviewRescheduleViewSet(viewsets.ModelViewSet):
	"""
	Interview Schedule post
	"""
	serializer_class = InterviewRescheduleSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return InterviewReschedule.objects.all() #filter(interview_id__owner=self.request.user).order_by('-id')

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		created = False

		try:
			reschedule_obj = InterviewReschedule.objects.get(
			interview_id=request.data.get('interview_id'),status='draft'
			)
			created = True
		except InterviewReschedule.DoesNotExist:
			self.perform_create(serializer)
			interview_id = InterviewSchedule.objects.get(id=request.data.get('interview_id')) 
			interview_id.status = 'schedule'
			interview_id.save()

		if created:
			if reschedule_obj.status == "draft":
				reschedule_obj.reschedule_interview_date_time = request.data.get('reschedule_interview_date_time')
				reschedule_obj.is_employee = request.data.get('is_employee')
				reschedule_obj.is_creator = request.data.get('is_creator')
				reschedule_obj.save()
				serializer = InterviewRescheduleSerializer(reschedule_obj)
			elif reschedule_obj.status == "accept":
				self.perform_create(serializer)
				reschedule_obj.interview_id.status = 'schedule'
				reschedule_obj.interview_id.save()
		return Response(
			serializer.data, status=status.HTTP_201_CREATED
		)

    
class EmployeeDirectHireResponseViewSet(viewsets.ModelViewSet):
	"""
	Employee direct hire response
	"""
	serializer_class = EmployeeDirectHireResponseSerializer
	permission_classes = [IsAuthenticated]

	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
	search_fields = ('employee__first_name','employee__last_name','job__title')
	queryset = InterviewSchedule.objects.filter(is_direct_hire=True).order_by('-id')

	@detail_route(url_name='project_interview_response', methods=['get'])
	def project_interview_response(self, request, pk=None):
		"""
		Endpoint for project interview responses
		"""
		queryset = InterviewSchedule.objects.filter(is_direct_hire=True,project=pk).order_by('-id')
		queryset = self.filter_queryset(queryset)

		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)

	@detail_route(url_name='send_appointment', methods=['post'])
	def send_appointment(self, request, pk=None):
		"""
		Endpoint for direct hire employee
		"""
		self.serializer_class = EmployeeHireSerializer
		obj = InterviewSchedule.objects.get(id=request.data.get('emp_id'))
		employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, project=request.data.get('project'),letter_through= 'direct_interview').first()
		create_date = datetime.strptime(request.data.get('onDate'),'%m-%d-%Y').strftime('%Y-%m-%d')
		project = Project.objects.get(id=request.data.get('project'))
		data = {
			'emp_id' : obj.employee,
			'name' : request.data.get('name'),
			'create_date' : create_date,
			'address' : request.data.get('address'),
			'state' : request.data.get('state'),
			'city' : request.data.get('city'),
			'zip' : request.data.get('zip'),
			'working_title' : request.data.get('workingTitle'),
			'department' : request.data.get('department'),
			'duration' : request.data.get('duration'),
			'joining_date' : request.data.get('beginningDate'),
			'salary_parameters' : request.data.get('salaryParameters'),
			'responsibilities1' : request.data.get('responsibilities1'), 
			'responsibilities2' : request.data.get('responsibilities2'), 
			'responsibilities3' : request.data.get('responsibilities3'), 
			'department_contribution' : request.data.get('departmentContribution'),
			'project' : project,
			'letter_through' : 'direct_interview',
			'creator_email':request.data.get('creator_email'),
			'job' : obj.job,
		}
		docusign_data = {
			'emp_id' : obj.employee.user_id,
			'creator_email':request.data.get('creator_email'),
			'document' :request.data.get('document').split(',')[1],
			'document_name' :request.data.get('document_name'),
			'creatorXposition':request.data.get('creatorXposition'),
			'creatorYposition':request.data.get('creatorYposition'),
			'employeeXposition':request.data.get('employeeXposition'),
			'employeeYposition':request.data.get('employeeYposition'),
			'nda':False
		}
		if not employee_hire:
			employee_hire = EmployeeHireSerializer.create(EmployeeHireSerializer(), validated_data=data)
			docusign_url = create_signature(docusign_data)
			docusign_doc = {'document':request.data.get('document'),'document_name':request.data.get('document_name')}
			s = DocumentsToDocusignSerializer(data=docusign_doc)
			s.is_valid(raise_exception=True)     
			s.save(employeehire_details=employee_hire,enveloped=docusign_url['envelopeId'])
			
			EmployeeHire.objects.filter(id=employee_hire.id).update(envelop=docusign_url['envelopeId'])
			

		# obj.status = 'hire'
		emp_status, created = RecruitmentEmployeeStatus.objects.get_or_create(owner=self.request.user,employee=obj.employee, project=employee_hire.project)
		emp_status.status = 'hire'
		emp_status.save()
		# obj.save()
		response_data = {
			'id' : pk,
			'emp_id' : obj.employee.id,
			'status' : emp_status.status
		
		}
		return Response(response_data)

	@detail_route(url_name='hire', methods=['get'])
	def hire(self, request, pk=None):
		"""
		Endpoint for hire employee
		"""
		obj = InterviewSchedule.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=obj.job)
		data = {
					'name': obj.employee.first_name + ' ' + obj.employee.last_name,
					'address': obj.employee.basic_details.address_line1,
					'city': obj.employee.basic_details.city,
					'state': obj.employee.basic_details.state.title if obj.employee.basic_details.state else '',
					'zip': obj.employee.basic_details.pin_code,

				}
		return Response(data)

	@detail_route(url_name='docusign_status', url_path='docusign-status/(?P<envelop_id>[a-zA-Z0-9-]+)')
	def docusign_status(self, request,pk=None,envelop_id=None):
		"""
		Endpoint for  docusign status
		"""
		obj = InterviewSchedule.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.get(envelop=envelop_id)
		data={
			'emp_id':obj.employee.user_id,
			'creator_email':employee_hire.creator_email,
			'envelop_id':envelop_id
		}
		final_url = signature_status(data)

		return Response(final_url)


class EmployeeListForJobView(viewsets.ModelViewSet):

	serializer_class = EmployeeListForJobSerializer
	permission_classes = [IsAuthenticated,]

	# Show all of the Jobs in particular experties, department , role , hourlybudget, availability

	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
	filter_fields = ('employment_details__departments', 'employment_details__functional_areas',
					'employment_details__role','basic_details__total_experience',
					'availability_details__hourly_charges','availability_details__days_per_year', 'availability_details__hours_per_day')
	search_fields = ('first_name','last_name','employment_details__current_designation','availability_details__hours_per_day__title',)
	# queryset = UserProfile.objects.filter(~Q(first_name = ""),role="employee").order_by('-id')

	def get_queryset(self):
		employees = RecruitmentEmployeeStatus.objects.filter(status='join',owner=self.request.user).values_list('employee', flat=True)
		queryset = UserProfile.objects.filter(~Q(id__in=employees),~Q(first_name = ""),role="employee").order_by('-id')
		return queryset

	@detail_route(url_name='send_appointment', methods=['post'])
	def send_appointment(self, request, pk=None):
		
		"""
		Endpoint for send appointment letter
		"""		
		self.serializer_class = EmployeeHireSerializer
		employee_hire = EmployeeHire.objects.filter(~Q(status="reject"),emp_id=request.data.get('emp_id'),project=request.data.get('project'),letter_through= 'direct_hire').first()
		employee = UserProfile.objects.get(id=request.data.get('emp_id'))
		create_date = datetime.strptime(request.data.get('onDate'),'%m-%d-%Y').strftime('%Y-%m-%d')	
		project = Project.objects.get(id=request.data.get('project'))	
		data = {
			'emp_id' : employee,
			'name' : request.data.get('name'),
			'create_date' : create_date,
			'address' : request.data.get('address'),
			'state' : request.data.get('state'),
			'city' : request.data.get('city'),
			'zip' : request.data.get('zip'),
			'working_title' : request.data.get('workingTitle'),
			'department' : request.data.get('department'),
			'duration' : request.data.get('duration'),
			'joining_date' : request.data.get('beginningDate'),
			'salary_parameters' : request.data.get('salaryParameters'),
			'responsibilities1' : request.data.get('responsibilities1'), 
			'responsibilities2' : request.data.get('responsibilities2'), 
			'responsibilities3' : request.data.get('responsibilities3'), 
			'department_contribution' : request.data.get('departmentContribution'),
			'availability' : request.data.get('availability'),
			'project' : project,
			'letter_through' : 'direct_hire',
			'creator_email':request.data.get('creator_email')
		
		}
		
		docusign_data = {
			'emp_id' : employee.user_id,
			'creator_email':request.data.get('creator_email'),
			'document' :request.data.get('document').split(',')[1],
			'document_name' :request.data.get('document_name'),
			'creatorXposition':request.data.get('creatorXposition'),
			'creatorYposition':request.data.get('creatorYposition'),
			'employeeXposition':request.data.get('employeeXposition'),
			'employeeYposition':request.data.get('employeeYposition'),
			'nda':False
		}
		
		if not employee_hire:
			employee_hire = EmployeeHireSerializer.create(EmployeeHireSerializer(), validated_data=data)
			docusign_url = create_signature(docusign_data)
			docusign_doc = {'document':request.data.get('document'),'document_name':request.data.get('document_name')}
			s = DocumentsToDocusignSerializer(data=docusign_doc)
			s.is_valid(raise_exception=True)     
			s.save(employeehire_details=employee_hire,enveloped=docusign_url['envelopeId'])
			
			EmployeeHire.objects.filter(id=employee_hire.id).update(envelop=docusign_url['envelopeId'])
			

			
		emp_status, created = RecruitmentEmployeeStatus.objects.get_or_create(owner=self.request.user,employee=employee, project=employee_hire.project)
		emp_status.status = 'hire'
		emp_status.save()

		response_data = {
			'id' : pk,
			'emp_id' : employee.id,
			'status' : emp_status.status
	
		}
		return Response(response_data)

	@detail_route(url_name='hire', methods=['get'])
	def hire(self, request, pk=None):
		"""
		Endpoint for hire employee
		"""
		employee = UserProfile.objects.get(id=pk)
		data = {
					'name': employee.first_name + ' ' + employee.last_name,
					'address': employee.basic_details.address_line1,
					'city': employee.basic_details.city,
					'state': employee.basic_details.state.title if employee.basic_details.state else '',
					'zip': employee.basic_details.pin_code,

				}
		return Response(data)

	@detail_route(url_name='docusign_status', url_path='docusign-status/(?P<envelop_id>[a-zA-Z0-9-]+)')
	def docusign_status(self, request,pk=None,envelop_id=None):
		"""
		Endpoint for  docusign status
		"""
		employee_hire = EmployeeHire.objects.get(envelop=envelop_id)
		employee = UserProfile.objects.get(id=pk)
		data={
			'emp_id':employee.user_id,
			'creator_email':employee_hire.creator_email,
			'envelop_id':envelop_id
		}
		final_url = signature_status(data)

		return Response(final_url)

class CurrentEmployeeViewSet(viewsets.ModelViewSet):
	"""
	Current Employee list
	"""
	serializer_class = CurrentEmployerSerializer
	permission_classes = [IsAuthenticated]

	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
	search_fields = ('userprofile__first_name','userprofile__last_name','userprofile__employment_details__current_designation')

	def get_queryset(self):
		#employees = RecruitmentEmployeeStatus.objects.filter(owner=self.request.user,docusign_status='sent').values_list('employee', flat=True)
		employees = RecruitmentEmployeeStatus.objects.filter(status='join',owner=self.request.user).values_list('employee', flat=True)
		queryset = EmployeeBasicDetails.objects.filter(userprofile__in=employees,userprofile__role='employee').order_by('-id')
		return queryset

		
	@detail_route(url_name='fire', methods=['get'])
	def fire(self, request, pk=None):
		"""
		Endpoint for fire employee
		"""
		obj = EmployeeBasicDetails.objects.get(id=pk)
		data =  {
					'name': obj.userprofile.first_name + ' ' + obj.userprofile.last_name,
					'address': obj.address_line1,
					'city': obj.city,
					'state': obj.state.title if obj.state else '',
					'zip': obj.pin_code,

				}
		return Response(data)
	
	@detail_route(url_name='docusign_status', url_path='docusign-status/(?P<envelop_id>[a-zA-Z0-9-]+)')
	def docusign_status(self, request,pk=None,envelop_id=None):
		"""
		Endpoint for  docusign status
		"""
		obj = EmployeeBasicDetails.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.get(envelop=envelop_id)
		data={
			'emp_id':'',
			'creator_email':employee_hire.creator_email,
			'envelop_id':envelop_id
		}
		final_url = signature_status(data)
		return Response(final_url)

	@detail_route(url_name='send_termination', methods=['post'])
	def send_termination(self, request, pk=None):
		"""
		Endpoint for send appointment letter
		"""
		self.serializer_class = EmployeeHireSerializer

		employee = EmployeeBasicDetails.objects.get(id=request.data.get('emp_id'))
		employee_hire = EmployeeHire.objects.filter(emp_id=employee.userprofile,emp_id__employee_status__status='join').first()
		create_date = datetime.strptime(request.data.get('create_date'),'%m-%d-%Y').strftime('%Y-%m-%d')		
		project = Project.objects.get(id=request.data.get('project'))
		data = {
			'emp_id' : employee.userprofile,
			'name' : request.data.get('name'),
			'create_date' : create_date,
			'address' : request.data.get('address'),
			'state' : request.data.get('state'),
			'city' : request.data.get('city'),
			'zip' : request.data.get('zip'),
			'working_title' : request.data.get('working_title'),
			'termination_reason1' : request.data.get('termination_reason1'), 
			'termination_reason2' : request.data.get('termination_reason2'), 
			'termination_reason3' : request.data.get('termination_reason3'),
			'termination_reason4' : request.data.get('termination_reason4'), 
			'termination_reason5' : request.data.get('termination_reason5'),
			'termination_date' : request.data.get('termination_date'),
			'project' : project,
			'creator_email':request.data.get('creator_email')
		}

		docusign_data = {
			'emp_id' : '',
			'creator_email':request.data.get('creator_email'),
			'document' :request.data.get('document').split(',')[1],
			'document_name' :request.data.get('document_name'),
			'creatorXposition':request.data.get('creatorXposition'),
			'creatorYposition':request.data.get('creatorYposition'),
			'nda':False
		}

		if employee_hire:
			employee_hire = EmployeeHireSerializer.create(EmployeeHireSerializer(), validated_data=data)
			docusign_url = create_signature(docusign_data)
			docusign_doc = {'document':request.data.get('document'),'document_name':request.data.get('document_name')}
			s = DocumentsToDocusignSerializer(data=docusign_doc)
			s.is_valid(raise_exception=True)     
			s.save(employeehire_details=employee_hire,enveloped=docusign_url['envelopeId'])
			
			EmployeeHire.objects.filter(id=employee_hire.id).update(envelop=docusign_url['envelopeId'])
			


		# emp_status, created = RecruitmentEmployeeStatus.objects.get_or_create(owner=self.request.user,employee=employee.userprofile, project=employee_hire.project)
		emp_status_details = RecruitmentEmployeeStatus.objects.filter(owner=self.request.user,employee=employee.userprofile, status='join')
		for emp_status in emp_status_details:
			emp_status.status = 'left'
			emp_status.save()
		self.request.user.userprofile.employees.remove(employee.userprofile.user.id)
		self.request.user.userprofile.save()
		response_data = {
			'id': pk,
			'emp_id' : employee.id,
			'status' : 'left'
		
		}
		return Response(response_data)


	@detail_route(url_name='completed_tasks',url_path='completed-tasks', methods=['get'])
	def completed_tasks(self, request, pk=None):
		"""
		Endpoint employee completed task CRUD
		"""
		self.serializer_class = CompletedTasksSerializer
		obj = EmployeeBasicDetails.objects.get(id=pk)

		tasks = Task.objects.filter(participants=obj.userprofile.user).distinct() #.values_list('id', flat=True)
		task_assign_details = TaskAssignDetails.objects.filter(task__in=tasks,is_complete=True).distinct()
		milestones = [i.task.milestone for i in task_assign_details]
		projects = Project.objects.filter(milestones__in=milestones).values_list('id', flat=True)
		queryset = Project.objects.filter(Q(id__in=projects)).distinct()
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)

	@detail_route(url_name='ratings',url_path='ratings', methods=['get'])
	def ratings(self, request, pk=None):
		"""
		Endpoint employee average ratings
		"""
		self.serializer_class = AverageRatingSerializer
		obj = EmployeeBasicDetails.objects.get(id=pk)
		serializer = self.get_serializer(obj)
		return Response(serializer.data)

	@detail_route(url_name='pay',url_path='pay', methods=['get','post'])
	def pay(self, request, pk=None):
		"""
		Endpoint employee salary payments CRUD
		"""
		queryset=[]
		rate = 0
		self.serializer_class = SalaryPaymentSerializer
		obj = EmployeeBasicDetails.objects.get(id=pk)
		
		if request.method == 'POST':
			wallet_amount = Transactions.get_wallet_amount(self,user=self.request.user)
			if wallet_amount < request.data.get("amount").get("amount"):
				raise serializers.ValidationError('No sufficient balance in your wallet for processing the transaction.')

			s = SalaryPaymentSerializer(data=request.data, many=False, partial=True)
			s.is_valid(raise_exception=True)
			s.save(user=obj.userprofile.user)

			data = [{
				"reference_no": "",
				"remark": "Salary Payment",
				"mode": "withdrawal",
				"status": "success",
				"amount":{"amount":request.data.get("amount").get("amount"),"currency":"USD"},
				"user": self.request.user.id
				},
				{
				"reference_no": "",
				"remark": "Salary Payment",
				"mode": "deposite",
				"status": "success",
				"amount":{"amount":request.data.get("amount").get("amount"),"currency":"USD"},
				"user": obj.userprofile.user.id
				}
			]
			transaction = TransactionsSerializer(data=data,many=True)
			transaction.is_valid(raise_exception=True)
			transaction.save(project_id=request.data.get("project"))
			queryset = SalaryPayment.objects.filter(project__owner=self.request.user,project__id=request.data.get("project"),user=obj.userprofile.user).distinct()

		if request.method == 'GET':
			queryset = SalaryPayment.objects.filter(project__owner=self.request.user,project__id=request.META['HTTP_PROJECT'],user=obj.userprofile.user).distinct()

		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			serializer = self.get_paginated_response(serializer.data)
		else:
			serializer = self.get_serializer(queryset, many=True)
		if obj.userprofile.availability_details:	
			rate =  re.findall('\\d+',obj.userprofile.availability_details.hourly_charges.title)
			rate = int(rate[0])

		data = {
					"employee": obj.userprofile.first_name +' '+ obj.userprofile.last_name,
					"photo": convert_file_to_base64(obj.userprofile.photo) if obj.userprofile.photo else None,
					"rating": obj.userprofile.rating,
					"current_designation": obj.userprofile.employment_details.all().first().current_designation if obj.userprofile.employment_details else "",
					"hourly_rate": rate,
					"payment_history": serializer.data
				}
		return Response(data)

	@detail_route(url_name='hours_calculation',url_path='hours-calculation', methods=['post','get'])
	def hours_calculation(self, request, pk=None):
		"""
		Endpoint employee logged in hours calculation CRUD
		"""
		employee = EmployeeBasicDetails.objects.get(id=pk)

		if request.data.get("end_date") and not request.data.get("start_date"):
			raise serializers.ValidationError('Please set start date.')
		elif not request.data.get("end_date") and request.data.get("start_date"):
			raise serializers.ValidationError('Please set end date.')
		elif not request.data.get("end_date") and not request.data.get("start_date"):
			raise serializers.ValidationError('Please set start and end date.')
		elif request.data.get("end_date") < request.data.get("start_date"):
			raise serializers.ValidationError('End date must be greater than or equal to start date.')
		elif request.data.get("end_date") and request.data.get("start_date"):

			salary_payments = SalaryPayment.objects.filter(project__owner=self.request.user,user=employee.userprofile.user,project=request.data.get("project")).distinct()
			dates = []
			for i in salary_payments:
				if str(i.from_date)  <= request.data.get("start_date") <= str(i.to_date) or str(i.from_date) <= request.data.get("end_date") <= str(i.to_date):
					dates.append(str(i.from_date) + " to " + str(i.to_date))
			if dates:
				raise serializers.ValidationError('You already paied for following dates: %s' % dates)

		
		hourly_rate = request.data.get("hourly_rate")
		work_session_details = WorkSession.objects.filter(~Q(end_datetime=None),task__milestone__project__id=request.data.get("project"),employee=employee.userprofile.user)
		minutes = 0

		for i in work_session_details:
			start_date = str(i.start_datetime.date())
			end_date = str(i.end_datetime.date())
			loggedin_hours = i.loggedin_hours.split(':')

			if start_date != end_date:
				delta = i.end_datetime.date()-i.start_datetime.date()
				flag = 1
				response = requests.get('https://timezoneapi.io/api/ip')
				data = response.json()
				user_time_zone = data['data']['timezone']['id']
				tz = pytz.timezone(user_time_zone)
				et = start = diff = None
				l = timedelta(hours=int(loggedin_hours[0]),minutes=int(loggedin_hours[1]))

				for d in range(delta.days + 1):
					if flag==1:
						st= i.start_datetime.astimezone(tz).replace(tzinfo=None)
						et= datetime(st.year, st.month, st.day,23,59,59,999)
						
						if request.data.get("start_date") <= str(st.date()) <= request.data.get("end_date") and request.data.get("start_date") <= str(et.date()) <= request.data.get("end_date"):
							diff = et-st
							minutes += (60 * (diff.seconds // 3600)) + (diff.seconds % 3600 / 60.0)
							
					else:
						st= datetime.combine(start, datetime.min.time())
						if et == None:
							et= datetime(start.year, start.month, start.day,23,59,59,999)

						if request.data.get("start_date") <= str(st.date()) <= request.data.get("end_date") and request.data.get("start_date") <= str(et.date()) <= request.data.get("end_date"):
							diff = et-st
							minutes += (60 * (diff.seconds // 3600)) + (diff.seconds % 3600 / 60.0)
					flag += 1
					et = None if l.days > 0 else i.end_datetime.astimezone(tz).replace(tzinfo=None)
					start = i.start_datetime.date() + timedelta(d+1)
					if diff:
						l = l-diff
			else:
				if request.data.get("start_date") <= start_date <= request.data.get("end_date") and request.data.get("start_date") <= end_date <= request.data.get("end_date"):
					minutes += (60 * (int(loggedin_hours[0]))) + (int(loggedin_hours[1]))
		amount = (hourly_rate/60)*minutes
		t = str(timedelta(minutes=minutes))
		data = {"hours": t,"amount":amount}

		return Response(data)

	@detail_route(url_name='processes',url_path='processes', methods=['get'])
	def processes(self, request, pk=None):
		"""
		Endpoint employee's processes CRUD
		"""
	
		# self.serializer_class = WorkSessionSerializer
		obj = EmployeeBasicDetails.objects.get(id=pk)

		work_session_details = WorkSession.objects.filter(task__milestone__project__id=request.META['HTTP_PROJECT'],employee=obj.userprofile.user)
		tasks = [{"process_id":i.task.id,"title":i.task.title}for i in work_session_details]

		data = {
					"employee": obj.userprofile.first_name +' '+ obj.userprofile.last_name,
					"photo": convert_file_to_base64(obj.userprofile.photo) if obj.userprofile.photo else None,
					"rating": obj.userprofile.rating,
					"current_designation": obj.userprofile.employment_details.all().first().current_designation if obj.userprofile.employment_details else "",
					"processes": [dict(t) for t in set(frozenset(t.items()) for t in tasks)]
				}
		
		return Response(data)

	@detail_route(url_name='metrices',url_path='processes/(?P<process_id>[0-9]+)/metrices', methods=['get'])
	def metrices(self, request, pk=None, process_id=None):
		"""
		Endpoint employee metrices CRUD
		"""
	
		self.serializer_class = MetricesSerializer
		obj = EmployeeBasicDetails.objects.get(id=pk)

		queryset = WorkSession.objects.filter(~Q(end_datetime=None),task__id=process_id,employee=obj.userprofile.user)

		page = self.paginate_queryset(queryset)

		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(queryset, many=True)

		return Response(serializer.data)

class PreviousEmployeeViewSet(viewsets.ModelViewSet):
	"""
	Current Employee list
	"""
	serializer_class = CurrentEmployerSerializer
	permission_classes = [IsAuthenticated]

	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)
	search_fields = ('userprofile__first_name','userprofile__last_name','userprofile__employment_details__current_designation')

	def get_queryset(self):
		join_emp = RecruitmentEmployeeStatus.objects.filter(Q(status='join'),owner=self.request.user).values_list('id', flat=True)
		employees = RecruitmentEmployeeStatus.objects.filter(Q(status='left')|Q(status='rehire'),~Q(employee__employee_status__id__in=join_emp) ,owner=self.request.user).values_list('employee', flat=True)
		queryset = EmployeeBasicDetails.objects.filter(userprofile__in = employees ,userprofile__role='employee').order_by('-id')
		return queryset

	@detail_route(url_name='re_hire', methods=['get'])
	def re_hire(self, request, pk=None):
		"""
		Endpoint for hire employee
		"""
		obj = EmployeeBasicDetails.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.filter(emp_id=obj.userprofile)
		data = {
					'name': obj.userprofile.first_name + ' ' + obj.userprofile.last_name,
					'address': obj.address_line1,
					'city': obj.city,
					'state': obj.state.title if obj.state else '',
					'zip': obj.pin_code,

				}
		return Response(data)
	
	@detail_route(url_name='docusign_status', url_path='docusign-status/(?P<envelop_id>[a-zA-Z0-9-]+)')
	def docusign_status(self, request,pk=None,envelop_id=None):
		"""
		Endpoint for  docusign status
		"""
		employee = UserProfile.objects.get(id=pk)
		employee_hire = EmployeeHire.objects.get(envelop=envelop_id)
		data={
			'emp_id':employee.user_id,
			'creator_email':employee_hire.creator_email,
			'envelop_id':envelop_id
		}
		final_url = signature_status(data)

		return Response(final_url)

	@detail_route(url_name='send_appointment', methods=['post'])
	def send_appointment(self, request, pk=None):
		"""
		Endpoint for send appointment letter
		"""		
		self.serializer_class = EmployeeHireSerializer
		
		employee = EmployeeBasicDetails.objects.get(id=request.data.get('emp_id'))
		employee_hire = EmployeeHire.objects.filter(emp_id=employee.userprofile,emp_id__employee_status__status='rehire',letter_through= 're_hire').first()
		create_date = datetime.strptime(request.data.get('onDate'),'%m-%d-%Y').strftime('%Y-%m-%d')	
		project = Project.objects.get(id=request.data.get('project'))
		data = {
			'emp_id' : employee.userprofile,
			'name' : request.data.get('name'),
			'create_date' : create_date,
			'address' : request.data.get('address'),
			'state' : request.data.get('state'),
			'city' : request.data.get('city'),
			'zip' : request.data.get('zip'),
			'working_title' : request.data.get('workingTitle'),
			'department' : request.data.get('department'),
			# 'tenure_status' : request.data.get('tenureStatus'),
			'duration' : request.data.get('duration'),
			'joining_date' : request.data.get('beginningDate'),
			'salary_parameters' : request.data.get('salaryParameters'),
			'responsibilities1' : request.data.get('responsibilities1'), 
			'responsibilities2' : request.data.get('responsibilities2'), 
			'responsibilities3' : request.data.get('responsibilities3'), 
			'department_contribution' : request.data.get('departmentContribution'),
			'availability' : request.data.get('availability'),
			'project' : project,
			'letter_through' : 're_hire',
			'creator_email':request.data.get('creator_email')
			
		}
		docusign_data = {
			'emp_id' : employee.userprofile.user_id,
			'creator_email':request.data.get('creator_email'),
			'document' :request.data.get('document').split(',')[1],
			'document_name' :request.data.get('document_name'),
			'creatorXposition':request.data.get('creatorXposition'),
			'creatorYposition':request.data.get('creatorYposition'),
			'employeeXposition':request.data.get('employeeXposition'),
			'employeeYposition':request.data.get('employeeYposition'),
			'nda':False
		}
		if not employee_hire:
			employee_hire = EmployeeHireSerializer.create(EmployeeHireSerializer(), validated_data=data)
			docusign_url = create_signature(docusign_data)
			docusign_doc = {'document':request.data.get('document'),'document_name':request.data.get('document_name')}
			s = DocumentsToDocusignSerializer(data=docusign_doc)
			s.is_valid(raise_exception=True)     
			s.save(employeehire_details=employee_hire,enveloped=docusign_url['envelopeId'])
			
			EmployeeHire.objects.filter(id=employee_hire.id).update(envelop=docusign_url['envelopeId'])
			


		emp_status, created = RecruitmentEmployeeStatus.objects.get_or_create(owner=self.request.user,employee=employee.userprofile, project=employee_hire.project)
		emp_status.status = 'rehire'
		emp_status.save()

		response_data = {
			'id': pk,
			'emp_id' : employee.id,
			'status' : emp_status.status
			
		}
		return Response(response_data)

	@detail_route(url_name='ratings',url_path='ratings', methods=['get'])
	def ratings(self, request, pk=None):
		"""
		Endpoint employee average ratings
		"""
		self.serializer_class = AverageRatingSerializer
		obj = EmployeeBasicDetails.objects.get(id=pk)
		serializer = self.get_serializer(obj)
		return Response(serializer.data)
		

class DirectHireViewSet(viewsets.ModelViewSet):
	"""
	Crud Operation for Direct Hire post
	"""
	serializer_class = DirectHireSerializer
	permission_classes = [IsAuthenticated]
	http_method_names = ['get', 'put', 'head']
	filter_backends = (django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter)

	def get_queryset(self):
		queryset = EmployeeHire.objects.filter(Q(letter_through='direct_hire')|Q(letter_through= 're_hire'))
		queryset = queryset.filter(emp_id=self.request.user.userprofile).order_by('-id')
		return queryset

	@detail_route(url_name='join', methods=['get','put'])
	def join(self, request, pk=None):
		"""
		Endpoint for join company
		"""
		self.serializer_class = EmployeeHireSerializer
		employee_hire = EmployeeHire.objects.get(id=pk)
		serializer = EmployeeHireSerializer(employee_hire)
		if request.method == 'PUT':
			# if request.data.get('digital_sign_employee'):
			# 	employee_hire.digital_sign_employee = request.data.get('digital_sign_employee')
			employee_hire.status = 'accept'
			employee_hire.accept_nda = request.data.get('accept_nda')
			employee_hire.save()
			emp_status = RecruitmentEmployeeStatus.objects.get(employee=self.request.user.userprofile,owner=employee_hire.project.owner, project=employee_hire.project)
			emp_status.status = 'join'
			emp_status.save()
			employee_hire.project.owner.userprofile.employees.add(employee_hire.emp_id.user.id)
			employee_hire.project.owner.userprofile.save()
		return Response(serializer.data)


	@detail_route(url_name='reject_offer',methods=['put'])
	def reject_offer(self, request, pk=None):
		"""
		Endpoint for Direct offer request rejection
		"""
		hire_obj = EmployeeHire.objects.get(id=pk)
		hire_obj.status = 'reject'
		hire_obj.save()
		return Response(EmployeeHireSerializer(hire_obj).data)