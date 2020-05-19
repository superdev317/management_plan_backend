from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from rest_framework import serializers
from rest_framework.reverse import reverse

from core.serializers import Base64ImageField, Base64FileField
from .models import Job , InterviewSchedule , JobApply, InterviewReschedule, EmployeeHire, RecruitmentEmployeeStatus, DocumentsToDocusign

from common.models import Department,Role,Expertise,Experience,HourlyBudget,Availability,Parameter
from accounts.serializers import (
    EmployeeDetailSerializer,UserProfileSerializer,EmployeeAvailabilitySerializer,EmployeeProfessionalDetailSerializer,
    EmployeeEmploymentDetailSerializer, EmployeeAvailabilityShortDataSerializer
)
from common.serializers import (
    DepartmentSerializer, RoleSerializer, ExpertiseSerializer, ExperienceListSerializer, AvailabilityListSerializer, HourlyBudgetListSerializer
)
from accounts.models import UserProfile, EmployeeAvailability, EmployeeProfessionalDetails ,EmployeeBasicDetails ,EmployeeEmploymentDetails
from rest_framework.response import Response
from datetime import datetime, date
from projects.models import EmployeeRatingDetails, Ratings, WorkSession
from django.db.models import Q
import requests
import pytz

class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for Category
    """
    department = Department()
    role = Role()
    expertise = Expertise()


    class Meta:
        model = Job
        fields = ('id','title','description','date_start','date_end','department','role','expertise','experience','availability','hourlybudget','owner','status','project')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('title'):
            raise serializers.ValidationError('Please set title')
        if not attrs.get('description'):
            raise serializers.ValidationError('Please set description')
        if not attrs.get('date_start'):
            raise serializers.ValidationError('Please set start date')
        if not attrs.get('date_end'):
            raise serializers.ValidationError('Please set end date')
        if not attrs.get('department'):
            raise serializers.ValidationError('Please set department')
        if not attrs.get('role'):
            raise serializers.ValidationError('Please set role')
        if attrs.get('date_start') and attrs.get('date_end'):
            if attrs.get('date_end') <= attrs.get('date_start'):
                raise serializers.ValidationError('Please select start date less than end date')
        return attrs

class JobDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for Job Details
    """
    department = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    hourlybudget = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ('id','title','description','date_start','date_end','department','role','expertise','experience','availability','hourlybudget','owner','status','is_applied')

    def get_department(self, obj):
        return DepartmentSerializer(obj.department, many=True).data

    def get_role(self, obj):
        return RoleSerializer(obj.role, many=True).data

    def get_expertise(self, obj):
        return ExpertiseSerializer(obj.expertise, many=True).data

    def get_experience(self, obj):
        return ExperienceListSerializer(obj.experience, many=True).data

    def get_availability(self, obj):
        return AvailabilityListSerializer(obj.availability, many=True).data

    def get_hourlybudget(self, obj):
        return HourlyBudgetListSerializer(obj.hourlybudget, many=True).data

    def get_is_applied(self, obj):
        try:
            JobApply.objects.get(employee=self.context['request'].user.userprofile,job=obj.id)
            return True
        except JobApply.DoesNotExist:
            return False

class JobApplySerializer(serializers.ModelSerializer):
    """
    Serializer for Job Application
    """
    job_title = serializers.SerializerMethodField()
    job_description = serializers.SerializerMethodField()
    job_availability = serializers.SerializerMethodField()
    job_hourlybudget = serializers.SerializerMethodField()
    job_application_status = serializers.SerializerMethodField()
    interview_details = serializers.SerializerMethodField()
    offer_details = serializers.SerializerMethodField()

    class Meta:
        model = JobApply
        fields = ('id','cover_letter','job','job_title','job_description','job_availability','job_hourlybudget','create_date','employee', 'status', 'job_application_status', 'interview_details', 'offer_details')

    def get_job_title(self, obj):
        if obj.job:
            return obj.job.title

    def get_job_description(self, obj):
        if obj.job:
            return obj.job.description

    def get_job_availability(self, obj):
        if obj.job.availability:
            return AvailabilityListSerializer(obj.job.availability, many=True).data

    def get_job_hourlybudget(self, obj):
        if obj.job.hourlybudget:
            return HourlyBudgetListSerializer(obj.job.hourlybudget, many=True).data

    def get_job_application_status(self, obj):
        owner = obj.job.owner.first_name if obj.job.owner else "Recruiter"
        if obj.status == 'offered':
            employee_hire = EmployeeHire.objects.get(emp_id=obj.employee,job=obj.job,letter_through='job_application')
            offered_date = employee_hire.create_date.strftime('%B %d, %Y')

            if employee_hire.status == 'draft':
                return owner + " offered on, " +str(offered_date)
            elif employee_hire.status == 'reject':
                return "You rejected the offer letter."
            elif employee_hire.status == 'accept':
                return "You accepted the offer letter."
        elif obj.status == 'schedule':
            interview_obj = InterviewSchedule.objects.get(employee=obj.employee,job=obj.job, job_application=obj.id)
            interview_date = interview_obj.interview_date_time.strftime('%B %d, %Y')
            if interview_obj.status == 'schedule':
                return owner + " wants to schedule an interview on " +str(interview_date)
            elif interview_obj.status == 'decline':
                return "You rejected the interview request."
            elif interview_obj.status == 'accept':
                return "Candidate is available on " + str(interview_date)
        elif obj.status == 'reject':
            return owner + " reject your job application."

    def get_interview_details(self, obj):
        data = {}
        interview_obj = InterviewSchedule.objects.filter(employee=obj.employee,job=obj.job, job_application=obj.id).order_by('-id').first()
        if interview_obj:
            data={'id': interview_obj.id, 'status': interview_obj.status}
        return data

    def get_offer_details(self, obj):
        data = {}
        employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee,job=obj.job,letter_through='job_application').order_by('-id').first()
        if employee_hire:
            data={'id': employee_hire.id, 'status': employee_hire.status,'envelop': employee_hire.envelop,'emp_id': employee_hire.emp_id.id}
        return data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('employee') and attrs.get('job'):
            try:
                JobApply.objects.get(employee=attrs.get('employee'),job=attrs.get('job'))
                raise serializers.ValidationError('You already applied for this job')
            except JobApply.DoesNotExist:
                pass
        return attrs


class JobApplyDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for Job Application detail viewset
    """

    job = serializers.SerializerMethodField()
    interview_details = serializers.SerializerMethodField()
    offer_details = serializers.SerializerMethodField()

    class Meta:
        model = JobApply
        fields = ('cover_letter','job','create_date','employee', 'status','interview_details', 'offer_details')

    def get_job(self, obj):
        return JobSerializer(obj.job).data

    def get_interview_details(self, obj):
        data = {}
        interview_obj = InterviewSchedule.objects.filter(employee=obj.employee,job=obj.job, job_application=obj.id).order_by('-id').first()
        if interview_obj:
            data={'id': interview_obj.id, 'status': interview_obj.status}
        return data

    def get_offer_details(self, obj):
        data = {}
        employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee,job=obj.job,letter_through='job_application').order_by('-id').first()
        if employee_hire:
            data={'id': employee_hire.id, 'status': employee_hire.status,'envelop':employee_hire.envelop,'emp_id':employee_hire.emp_id.id}
        return data

class InterviewRescheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for Interview Reschedule
    """

    class Meta:
        model = InterviewReschedule
        fields  = ('id','reschedule_interview_date_time','reschedule_interview_date_time_creator','interview_id', 'status', 'is_employee', 'is_creator')

    def update(self, instance, validated_data):
        if validated_data.get('status') == 'accept':
            interview = validated_data.get('interview_id')
            interview.interview_date_time = validated_data.get('reschedule_interview_date_time')
            interview.status = 'accept'
            interview.save()
        instance = super().update(instance, validated_data)
        return instance

class InterviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Interview Schedule
    """

    reschedule_interviews = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSchedule

        fields  = ('id','interview_date_time','project','owner','job','employee','job_application','status','is_direct_hire','job_title','job_description', 'reschedule_interviews')


    def get_reschedule_interviews(self, obj):
        serializer = InterviewRescheduleSerializer(
            InterviewReschedule.objects.filter(interview_id=obj).order_by('-id'), many=True
        )
        return serializer.data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('interview_date_time'):
            raise serializers.ValidationError('Please set interview date and time.')
        return attrs

    def create(self, validated_data):
        if validated_data['job_application']:
            filt_obj = InterviewSchedule.objects.filter(owner=validated_data['owner'],employee=validated_data['employee'],project=validated_data['project'])
            if filt_obj:
                #if interview already assigned
                raise serializers.ValidationError("error : Interview already scheduled for this candidate")
            validated_data['job_application'].status = 'schedule'
            validated_data['job_application'].save()
        return super(InterviewSerializer, self).create(validated_data)


class EmployeeJobResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for employee job response
    """
    userprofile_id = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    availability_details = serializers.SerializerMethodField()
    reschedule_details = serializers.SerializerMethodField()
    interview_details = serializers.SerializerMethodField()
    offer_details = serializers.SerializerMethodField()
    job_application_status = serializers.SerializerMethodField()


    class Meta:
        model = JobApply
        fields = ('id', 'first_name','last_name','userprofile_id','job_id','job_title','experience','status','create_date','employee','availability_details', 'reschedule_details', 'job_application_status', 'interview_details', 'offer_details')

    def get_userprofile_id(self, obj):
        return obj.employee.pk

    def get_first_name(self, obj):
         return obj.employee.first_name

    def get_last_name(self, obj):
        return obj.employee.last_name

    def get_job_title(self, obj):
        return obj.job.title

    def get_availability_details(self, obj):
        availability_details = EmployeeAvailability.objects.filter(userprofile=obj.employee)
        return EmployeeAvailabilityShortDataSerializer(availability_details, many=True).data

    def get_experience(self, obj):
        if obj.employee.basic_details.total_experience:
            return obj.employee.basic_details.total_experience.title

    def get_reschedule_details(self, obj):
        data = InterviewReschedule.objects.filter(interview_id__job_application=obj).order_by('-id').first()
        if data:
            return InterviewRescheduleSerializer(data).data

    def get_job_application_status(self, obj):
        if obj.status == 'applied':
            applied_date = obj.create_date.strftime('%B %d, %Y')
            return "Applied on " +str(applied_date)
        elif obj.status == 'offered':
            employee_hire = EmployeeHire.objects.get(emp_id=obj.employee,job=obj.job,letter_through='job_application')
            offered_date = employee_hire.create_date.strftime('%B %d, %Y')
            if employee_hire.status == 'draft':
                return "Offered on " +str(offered_date)
            elif employee_hire.status == 'reject':
                return "Candidate rejected the offer letter."
            elif employee_hire.status == 'accept':
                return "Candidate accepted the offer letter."
        elif obj.status == 'schedule':
            interview_obj = InterviewSchedule.objects.get(employee=obj.employee,job=obj.job, job_application=obj.id)
            interview_date = interview_obj.interview_date_time.strftime('%B %d, %Y')

            reschedule_obj = InterviewReschedule.objects.filter(interview_id__job_application=obj, interview_id=interview_obj).order_by('-id').first()
            if reschedule_obj:
                emp_reschedule_date = reschedule_obj.reschedule_interview_date_time.strftime('%B %d, %Y %X')
                if emp_reschedule_date and reschedule_obj.is_employee==True and reschedule_obj.status=='draft' and interview_obj.status!= 'decline':
                    return "Employee wants to reschedule interview on " +str(emp_reschedule_date)
                elif emp_reschedule_date and reschedule_obj.is_employee==True and reschedule_obj.status=='accept' and interview_obj.status != 'decline':
                    return "Interview schedule on " +str(emp_reschedule_date)

                if reschedule_obj.reschedule_interview_date_time_creator:
                    creator_reschedule_date = reschedule_obj.reschedule_interview_date_time_creator.strftime('%B %d, %Y %X')
                    if creator_reschedule_date and reschedule_obj.is_creator==True and reschedule_obj.status=='draft' and interview_obj.status!= 'decline':
                        return "You reschedule interview on " +str(creator_reschedule_date)
                    elif creator_reschedule_date and reschedule_obj.is_creator==True and reschedule_obj.status=='accept' and interview_obj.status!= 'decline':
                        return "Interview schedule on " +str(creator_reschedule_date)
                if interview_obj.status=='decline':
                    return  "Candidate decline the interview request."
            else:
                if interview_obj.status == 'schedule':
                    return "Interview schedule on " +str(interview_date)
                elif interview_obj.status == 'decline':
                    return "Candidate decline the interview request."
                elif interview_obj.status == 'accept':
                    return "Candidate is available on " + str(interview_date)
        elif obj.status == 'reject':
            return "You rejected this job application."

    def get_interview_details(self, obj):
        data = {}
        interview_obj = InterviewSchedule.objects.filter(employee=obj.employee,job=obj.job, job_application=obj.id).order_by('-id').first()
        if interview_obj:
            data={'id': interview_obj.id, 'status': interview_obj.status}
        return data

    def get_offer_details(self, obj):
        data = {}
        employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee,job=obj.job,letter_through='job_application').order_by('-id').first()
        if employee_hire:
            data={'id': employee_hire.id, 'status': employee_hire.status,'envelop': employee_hire.envelop}
        return data


class EmployeeDirectHireResponseSerializer(serializers.ModelSerializer):

    """
    Serializer for employee direct hire response
    """

    userprofile_id = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    availability_details = serializers.SerializerMethodField()
    reschedule_details = serializers.SerializerMethodField()
    final_status = serializers.SerializerMethodField()
    offer_details = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSchedule
        fields = ('id', 'first_name','last_name','userprofile_id','job','job_title','experience','status','availability_details','reschedule_details', 'final_status', 'offer_details')

    def get_userprofile_id(self, obj):
        return obj.employee.pk

    def get_first_name(self, obj):
        return obj.employee.first_name

    def get_last_name(self, obj):
        return obj.employee.last_name

    def get_availability_details(self, obj):
        availability_details = EmployeeAvailability.objects.filter(userprofile=obj.employee)
        return EmployeeAvailabilityShortDataSerializer(availability_details, many=True).data

    def get_experience(self, obj):
        if obj.employee.basic_details.total_experience:
            return obj.employee.basic_details.total_experience.title

    def get_reschedule_details(self, obj):
        data = InterviewReschedule.objects.filter(interview_id=obj).order_by('-id').first()
        if data:
            return InterviewRescheduleSerializer(data).data

    def get_final_status(self, obj):
        interview_date = obj.interview_date_time.strftime('%B %d, %Y')
        if obj.status == 'schedule':
            reschedule_obj = InterviewReschedule.objects.filter(interview_id=obj).order_by('-id').first()
            if reschedule_obj:
                emp_reschedule_date = reschedule_obj.reschedule_interview_date_time.strftime('%B %d, %Y %X')
                if emp_reschedule_date and reschedule_obj.is_employee==True and reschedule_obj.status=='draft':
                    return "Employee wants to reschedule interview on " +str(emp_reschedule_date)
                elif emp_reschedule_date and reschedule_obj.is_employee==True and reschedule_obj.status=='accept':
                    return "Interview schedule on " +str(emp_reschedule_date)
                if reschedule_obj.reschedule_interview_date_time_creator:
                    creator_reschedule_date = reschedule_obj.reschedule_interview_date_time_creator.strftime('%B %d, %Y %X')
                    if creator_reschedule_date and reschedule_obj.is_creator==True and reschedule_obj.status=='draft':
                        return "You reschedule interview on " +str(creator_reschedule_date)
                    elif creator_reschedule_date and reschedule_obj.is_creator==True and reschedule_obj.status=='accept':
                        return "Interview schedule on " +str(creator_reschedule_date)
            else:
                return "Interview schedule on " +str(interview_date)
        elif obj.status == 'decline':
            return "Candidate decline the interview request."
        elif obj.status == 'accept':
            if obj.job:
                employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=obj.job,letter_through='direct_interview', project=obj.project).order_by('-id').first()
            else:
                employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=None, letter_through='direct_interview', project=obj.project).order_by('-id').first()

            if employee_hire:
                offered_date = employee_hire.create_date.strftime('%B %d, %Y')
                if employee_hire.status == 'draft':
                    return "Offered on " +str(offered_date)
                elif employee_hire.status == 'reject':
                    return "Candidate rejected the offer letter."
                elif employee_hire.status == 'accept':
                    return "Candidate accepted the offer letter."
            else:
                return "Candidate is available on " + str(interview_date)


    def get_offer_details(self, obj):
        data = {}
        if obj.job:
            employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=obj.job,letter_through='direct_interview', project=obj.project).order_by('-id').first()
        else:
            employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=None, letter_through='direct_interview', project=obj.project).order_by('-id').first()

        if employee_hire:
            data={'id': employee_hire.id, 'status': employee_hire.status,'envelop':employee_hire.envelop}
        return data


class EmployeeListForJobSerializer(serializers.ModelSerializer):

    job_title = serializers.SerializerMethodField()
    availability_details = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    emp_status = serializers.SerializerMethodField()
    envelop = serializers.SerializerMethodField()
    interview_schedule = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('id', 'first_name', 'last_name', 'availability_details','job_title','experience','emp_status','envelop','interview_schedule')


    def get_job_title(self, obj):
        current_designation = EmployeeEmploymentDetails.objects.filter(userprofile=obj,present=True).values_list('current_designation', flat=True).first()
        return current_designation

    def get_availability_details(self, obj):
        availability_details = EmployeeAvailability.objects.filter(userprofile=obj)
        return EmployeeAvailabilityShortDataSerializer(availability_details, many=True).data

    def get_experience(self, obj):
        if obj.basic_details.total_experience:
            return obj.basic_details.total_experience.title

    def get_emp_status(self, obj):
        if obj.basic_details.employee_status:
            return obj.basic_details.employee_status

    def get_envelop(self, obj):
        envelop = EmployeeHire.objects.filter(emp_id=obj,project__owner=self.context['request'].user,letter_through='direct_hire',status='draft').order_by('-id').first()
        if envelop:
            return envelop.envelop

    def get_interview_schedule(self, obj):
        schedule_obj = InterviewSchedule.objects.filter(owner=self.context['request'].user,employee=obj).first()
        accept_obj = InterviewSchedule.objects.filter(owner=self.context['request'].user,employee=obj).first()
        if schedule_obj or accept_obj:
            return True
        else:
            return False



class EmployeeHireSerializer(serializers.ModelSerializer):
    """
    Serializer for Hire Employee
    """
    owner = serializers.SerializerMethodField(read_only=True)
    show_nda = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmployeeHire
        fields  = ('id','create_date','job','emp_id','name','address',
            'state','city','zip','working_title','department','availability',
            'owner','duration','joining_date','salary_parameters','responsibilities1',
            'responsibilities2','responsibilities3','department_contribution','digital_sign_creator','letter_through','digital_sign_employee','status','project', 'show_nda', 'accept_nda','envelop')

    def get_owner(self, obj):
        if obj.job:
            if obj.job.owner:
                return obj.job.owner.id

    def get_show_nda(self, obj):
        if obj.project:
            return obj.project.show_nda

class CurrentEmployerSerializer(serializers.ModelSerializer):
    """
    Serializer for Current Employee
    """

    userprofile_id = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    current_designation = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    availability_details= serializers.SerializerMethodField()
    termination_envelop = serializers.SerializerMethodField()
    rehire_envelop = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeBasicDetails
        fields = ('id', 'first_name','last_name','userprofile_id','current_designation','experience','availability_details','termination_envelop','rehire_envelop')#,'rehire_envelop'


    def get_userprofile_id(self, obj):
        return obj.userprofile.pk

    def get_first_name(self, obj):
        return obj.userprofile.first_name

    def get_last_name(self, obj):
        return obj.userprofile.last_name

    def get_current_designation(self, obj):
        current_designation = EmployeeEmploymentDetails.objects.filter(userprofile=obj.userprofile,present=True).values_list('current_designation', flat=True).first()
        return current_designation

    def get_experience(self, obj):
        if obj.total_experience:
            return obj.total_experience.title

    def get_availability_details(self, obj):
        availability_details = EmployeeAvailability.objects.filter(userprofile=obj.userprofile)
        return EmployeeAvailabilityShortDataSerializer(availability_details, many=True).data

    def get_status(self, obj):

        status_details = EmployeeHire.objects.filter(emp_id=obj.userprofile,project__owner=self.context['request'].user,letter_through='re_hire',status='draft').order_by('-id').first()
        if status_details:
            return "re_hire"

    def get_termination_envelop(self, obj):
        envelop = EmployeeHire.objects.filter(emp_id=obj.userprofile,project__owner=self.context['request'].user,letter_through=None,status='draft').order_by('-id').first()

        if envelop is not None:
            return envelop.envelop


    def get_rehire_envelop(self, obj):
        last_entry = EmployeeHire.objects.filter(emp_id=obj.userprofile,project__owner=self.context['request'].user,letter_through=None,status='draft').order_by('-id').first()
        if last_entry:
            return None

        envelop = EmployeeHire.objects.filter(emp_id=obj.userprofile,project__owner=self.context['request'].user,letter_through='re_hire',status='accept').order_by('-id').first()
        if envelop is not None:
            return envelop.envelop

        rehiredraft_obj = EmployeeHire.objects.filter(Q(emp_id=obj.userprofile),Q(project__owner=self.context['request'].user),(Q(letter_through='re_hire') & Q(status='draft'))).order_by('-id').first()
        if rehiredraft_obj is not None:
            return rehiredraft_obj.envelop






class DirectInterviewRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for Direct Interview requests for employee
    """
    project = serializers.SerializerMethodField()
    job_description = serializers.SerializerMethodField()
    job_availability = serializers.SerializerMethodField()
    job_hourlybudget = serializers.SerializerMethodField()
    job_application_status = serializers.SerializerMethodField()
    reschedule_interviews = serializers.SerializerMethodField()
    offer_details = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSchedule
        fields  = ('id','interview_date_time','project','owner','job','employee','job_application','status',
            'job_title','job_description', 'job_availability', 'job_hourlybudget','reschedule_interviews', 'job_application_status', 'offer_details')

    def get_project(self, obj):
        if obj.project:
            return {'id':obj.project.id,'title':obj.project.title}

    def get_job_description(self, obj):
        return obj.job_description

    def get_job_availability(self, obj):
        if obj.job:
            if obj.job.availability:
                return AvailabilityListSerializer(obj.job.availability, many=True).data

    def get_job_hourlybudget(self, obj):
        if obj.job:
            if obj.job.availability:
                return HourlyBudgetListSerializer(obj.job.hourlybudget, many=True).data

    def get_reschedule_interviews(self, obj):
        serializer = InterviewRescheduleSerializer(
            InterviewReschedule.objects.filter(interview_id=obj), many=True
        )
        return serializer.data

    def get_job_application_status(self, obj):
        owner = obj.owner.first_name if obj.owner else "Recruiter"
        if obj.status == 'hire':
            if obj.job:
                employee_hire = EmployeeHire.objects.get(emp_id=obj.employee, job=obj.job,letter_through='direct_interview', project=obj.project)
                offered_date = employee_hire.create_date.strftime('%B %d, %Y')

                if employee_hire.status == 'draft':
                    return owner + " offered on, " +str(offered_date)
                elif employee_hire.status == 'reject':
                    return "You rejected the offer letter."
                elif employee_hire.status == 'accept':
                    return "You accepted the offer letter."
            else:
                employee_hire = EmployeeHire.objects.get(emp_id=obj.employee, job=None, letter_through='direct_interview', project=obj.project)
                offered_date = employee_hire.create_date.strftime('%B %d, %Y')

                if employee_hire.status == 'draft':
                    return owner + " offered on, " +str(offered_date)
                elif employee_hire.status == 'reject':
                    return "You rejected the offer letter."
                elif employee_hire.status == 'accept':
                    return "You accepted the offer letter."
        elif obj.status == 'schedule' and obj.interview_date_time:
            interview_date = obj.interview_date_time.strftime('%B %d, %Y')
            return owner + " wants to schedule an interview on " +str(interview_date)
        elif obj.status == 'decline':
            return "You rejected this interview request."

    def get_offer_details(self, obj):
        data = {}
        if obj.job:
            employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=obj.job,letter_through='direct_interview', project=obj.project.id).order_by('-id').first()
        else:
            employee_hire = EmployeeHire.objects.filter(emp_id=obj.employee, job=None, letter_through='direct_interview', project=obj.project).order_by('-id').first()
        if employee_hire:
            data={'id': employee_hire.id,'status':employee_hire.status,'envelop':employee_hire.envelop,'emp_id':employee_hire.emp_id.id}
        return data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        reschedule_obj = InterviewReschedule.objects.filter(interview_id=instance).order_by('-id').first()
        if reschedule_obj:
            if reschedule_obj.is_creator:
                instance.interview_date_time = reschedule_obj.reschedule_interview_date_time_creator
                instance.save()
                reschedule_obj.status = 'accept'
                reschedule_obj.save()
            if not reschedule_obj.reschedule_interview_date_time_creator:
                reschedule_obj.delete()

        return instance


class DirectHireSerializer(serializers.ModelSerializer):
    """
    Serializer for Direct Hire Employee
    """
    project = serializers.SerializerMethodField()
    job_application_status = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeHire
        fields  = ('id','project','salary_parameters','availability','responsibilities1',
            'responsibilities2','responsibilities3', 'job_application_status', 'status','envelop','emp_id')

    def get_project(self, obj):
        if obj.project:
            return {'id':obj.project.id,'title':obj.project.title}

    def get_job_application_status(self, obj):
        owner = obj.project.owner.first_name if obj.project.owner else "Recruiter"
        if obj.status == 'hire':
            if obj.job:
                employee_hire = EmployeeHire.objects.get(emp_id=obj.employee, job=obj.job, letter_through='direct_hire')
                offered_date = employee_hire.create_date.strftime('%B %d, %Y')
                return owner + " offered on, " +str(offered_date)
            else:
                employee_hire = EmployeeHire.objects.get(emp_id=obj.employee, job=None, letter_through='direct_hire')
                offered_date = employee_hire.create_date.strftime('%B %d, %Y')
                return owner + " offered on, " +str(offered_date)
        elif obj.status == 'schedule' and obj.interview_date_time:
            interview_date = obj.interview_date_time.strftime('%B %d, %Y')
            return owner + " wants to schedule an interview on " +str(interview_date)
        elif obj.status == 'reject':
            return "You rejected this offer letter."
        elif obj.status == 'accept':
            return "You accepted this offer letter."

class AverageRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for Current Employee Average Ratings
    """
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    rating_details = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeBasicDetails
        fields = ('id', 'first_name', 'last_name', 'user', 'average_rating', 'rating_details')

    def get_user(self, obj):
        return obj.userprofile.user.id

    def get_first_name(self, obj):
        return obj.userprofile.first_name

    def get_last_name(self, obj):
        return obj.userprofile.last_name

    def get_average_rating(self, obj):
        return obj.userprofile.rating

    def get_rating_details(self, obj):
        parameter_rating = []
        parameters = Parameter.objects.all()
        for p in parameters:
            emp_rating_details = EmployeeRatingDetails.objects.filter(employee=obj.userprofile.user,employee_ratings__parameter=p).values_list('employee_ratings', flat=True)
            rating_details = Ratings.objects.filter(id__in=list(emp_rating_details)).values_list('rating', flat=True)
            rating = 0
            if rating_details.exists():
                rating = float(sum(list(rating_details))) / float(len(rating_details))
            parameter_rating.append({"parameter": p.title, "rating": round(rating), "employer_count": len(rating_details)})
        return parameter_rating

class DocumentsToDocusignSerializer(serializers.ModelSerializer):
    document = Base64FileField(
        required=False, allow_null=True
    )

    class Meta:
        model = DocumentsToDocusign
        fields = ('id','document_name','document','employeehire_details',)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('document_name'):
            file_extension = attrs.get('document_name').split('.')[1]
            if file_extension not in ['pdf']:
                raise serializers.ValidationError('This type of file is not valid.')
        return attrs

def user_timezone(datetime_field):
    response = requests.get('https://timezoneapi.io/api/ip')
    data = response.json()
    user_time_zone = data['data']['timezone']['id']
    tz = pytz.timezone(user_time_zone)
    date= datetime_field.astimezone(tz).replace(tzinfo=None)
    return date

class MetricesSerializer(serializers.ModelSerializer):
    """
    Serializer for Metrices Work Session
    """
    start_datetime = serializers.SerializerMethodField()
    end_datetime = serializers.SerializerMethodField()

    class Meta:
        model = WorkSession
        fields = ('start_datetime', 'end_datetime', 'loggedin_hours')

    def get_start_datetime(self, obj):
        if obj.start_datetime:
            start_datetime = user_timezone(obj.start_datetime)
            start = start_datetime.strftime('%B %d, %Y %I:%M %p')
            return start

    def get_end_datetime(self, obj):
        if obj.end_datetime:
            end_datetime = user_timezone(obj.end_datetime)
            end = end_datetime.strftime('%B %d, %Y %I:%M %p')
            return end