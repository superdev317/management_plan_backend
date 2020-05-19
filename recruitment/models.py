from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .constants import (
    JOB_STATUS, INTERVIEW_STATUS, JOB_APPLICATION_STATUS, RESCHEDULE_INTERVIEW_STATUS, APPOINTMET_LETTER_STATUS, EMPLOYEE_STATUS, APPOINTMET_LETTER_THROUGH
)
from accounts.models import User,UserProfile
from projects.models import Project
from common.models import Department,Role,Expertise,Experience,HourlyBudget,Availability



class Job(models.Model):
	"""
    Model for job post in recruitment
    """
	title = models.CharField(max_length=300)
	description = models.CharField(max_length=500, default='')
	owner = models.ForeignKey(User, related_name='recruitments', blank=True, null=True)
	date_start = models.DateField(blank=True, null=True)
	date_end = models.DateField(blank=True, null=True)
	status = models.CharField(
        choices=JOB_STATUS,
        default=JOB_STATUS[0][0],
        max_length=10
    )
	department = models.ManyToManyField(
		Department,
		blank=True,
		related_name='Department'
    )
	role = models.ManyToManyField(
        Role,
        blank=True,
        related_name='Role'
    )
	availability = models.ManyToManyField(
        Availability,
        blank=True,
        related_name='Availability'
    )
	expertise = models.ManyToManyField(
		Expertise,
		blank=True,
		related_name='Expertise'
    )
	experience = models.ManyToManyField(
		Experience,
		blank=True,
		related_name='Experience'
    )
	hourlybudget = models.ManyToManyField(
		HourlyBudget,
		blank=True,
		related_name='HourlyBudget'
    )
	project = models.ForeignKey(Project, related_name='jobs',blank=True, null=True)

	def __str__(self):
		return self.title



class JobApply(models.Model):
	"""
    Model for job application for particular user
    """
	cover_letter = models.TextField(blank=True, null=True)
	job = models.ForeignKey(Job, related_name='job_apply', blank=True, null=True)
	employee = models.ForeignKey(UserProfile, related_name='job_apply', blank=True, null=True)
	status = models.CharField(
        choices=JOB_APPLICATION_STATUS,
        blank=True, null=True,
        max_length=20
    )
	create_date = models.DateField(blank=True, null=True, auto_now_add=True)

	def __str__(self):
		return self.job.title

class InterviewSchedule(models.Model):
	"""
    Model for Interview Schedule
    """
	interview_date_time = models.DateTimeField(blank=True, null=True)
	project = models.ForeignKey(Project, related_name='interview_schedule',blank=True, null=True)
	job = models.ForeignKey(Job, related_name='interview_schedule', blank=True, null=True)
	employee = models.ForeignKey(UserProfile, related_name='interview_schedule', blank=True, null=True)
	job_application = models.ForeignKey(JobApply, related_name='interview_schedule', blank=True, null=True)
	owner = models.ForeignKey(User, related_name='interviewschedule',blank=True, null=True)
	status = models.CharField(
        choices=INTERVIEW_STATUS,
        default=INTERVIEW_STATUS[0][0],
        max_length=20
    )

	job_title = models.CharField(max_length=300, blank=True, null=True)
	job_description = models.TextField(max_length=300,blank=True, null=True)
	is_direct_hire = models.BooleanField(default=False)
	job_description = models.TextField(max_length=300,blank=True, null=True)

	def __str__(self):
		return str(self.id)

class InterviewReschedule(models.Model):
	"""
    Model for Interview Reschedule
    """
	reschedule_interview_date_time = models.DateTimeField(blank=True, null=True)
	reschedule_interview_date_time_creator = models.DateTimeField(blank=True, null=True)
	interview_id = models.ForeignKey(InterviewSchedule, related_name='interview_reschedule', blank=True, null=True)
	status = models.CharField(
        choices=RESCHEDULE_INTERVIEW_STATUS,
        default=RESCHEDULE_INTERVIEW_STATUS[0][0],
        max_length=10
    )
	is_employee = models.BooleanField(default=False)
	is_creator = models.BooleanField(default=False)

class EmployeeHire(models.Model):
	"""
    Model for Hire employee
    """
	job = models.ForeignKey(Job, related_name='employee_hire', blank=True, null=True)
	create_date = models.DateField(blank=True, null=True)
	emp_id = models.ForeignKey(UserProfile, related_name='employee_hire', blank=True, null=True)
	name = models.CharField(max_length=300, blank=True, null=True)
	address = models.CharField(max_length=300, blank=True, null=True)
	state = models.CharField(max_length=300, blank=True, null=True)
	city = models.CharField(max_length=300, blank=True, null=True)
	zip = models.CharField(max_length=300, blank=True, null=True)
	working_title = models.CharField(max_length=300, blank=True, null=True)
	department = models.CharField(max_length=300, blank=True, null=True)
	tenure_status = models.CharField(max_length=300, blank=True, null=True)
	duration = models.CharField(max_length=300, blank=True, null=True)
	joining_date = models.DateField(max_length=300, blank=True, null=True)
	salary_parameters = models.CharField(max_length=300, blank=True, null=True)
	responsibilities1 = models.CharField(max_length=300, blank=True, null=True)
	responsibilities2 = models.CharField(max_length=300, blank=True, null=True)
	responsibilities3 = models.CharField(max_length=300, blank=True, null=True)
	department_contribution = models.CharField(max_length=300, blank=True, null=True)
	digital_sign_creator = models.TextField(max_length=200,blank=True, null=True)
	termination_reason1 = models.CharField(max_length=300, blank=True, null=True)
	termination_reason2 = models.CharField(max_length=300, blank=True, null=True)
	termination_reason3 = models.CharField(max_length=300, blank=True, null=True)
	termination_reason4 = models.CharField(max_length=300, blank=True, null=True)
	termination_reason5 = models.CharField(max_length=300, blank=True, null=True)
	termination_date    = models.DateField(max_length=300, blank=True, null=True)
	# is_direct_hire = models.BooleanField(default=False)
	digital_sign_employee = models.TextField(max_length=200,blank=True, null=True)
	project = models.ForeignKey(Project, related_name='employee_hire',blank=True, null=True)
	availability = models.CharField(max_length=50, blank=True, null=True)
	status = models.CharField(
		choices=APPOINTMET_LETTER_STATUS,
		default=APPOINTMET_LETTER_STATUS[0][0],
		max_length=10
	)
	letter_through = models.CharField(
        choices=APPOINTMET_LETTER_THROUGH,
        blank=True, null=True,
        max_length=25
    )
	accept_nda = models.BooleanField(default=False)
	envelop = models.CharField(max_length=500, blank=True, null=True)
	creator_email = models.EmailField(blank=True, null=True) 


class RecruitmentEmployeeStatus(models.Model):
	"""
    Model for Employee Status for creator and project
    """
	owner = models.ForeignKey(User, related_name='employee_status', blank=True, null=True)
	project = models.ForeignKey(Project, related_name='employee_status',blank=True, null=True)
	employee = models.ForeignKey(UserProfile, related_name='employee_status', blank=True, null=True)
	status = models.CharField(
        choices=EMPLOYEE_STATUS,
        blank=True, null=True,
        max_length=10
    )
	
	
class DocumentsToDocusign(models.Model):

	employeehire_details = models.ForeignKey(EmployeeHire, related_name='uploaded_documents',null=True, blank=True)
	document = models.FileField(upload_to='docusign/documents', blank=True, null=True)
	document_name = models.CharField(max_length=100, blank=True, null=True)
	enveloped = models.CharField(max_length=500, blank=True, null=True)
   