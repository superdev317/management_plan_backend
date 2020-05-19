from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

from .constants import (
    STATUS
)

class Department(models.Model):
	"""
    Model for Department 
    """
	title = models.CharField(max_length=300)
	description = models.CharField(max_length=500, default='')
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class Role(models.Model):
	"""
    Model for Role 
    """
	title = models.CharField(max_length=300)
	description = models.CharField(max_length=500, default='')
	department = models.ForeignKey(Department, related_name='role', blank=True, null=True)
	is_active = models.BooleanField(default=True)
	
	def __str__(self):
		return self.title

class Expertise(models.Model):
	"""
    Model for  Expertise 
    """
	title = models.CharField(max_length=300)
	description = models.CharField(max_length=500, default='')
	role = models.ForeignKey(Role, related_name='expertise', blank=True, null=True)
	department = models.ForeignKey(Department, related_name='expertise', blank=True, null=True)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		
		return self.title

	
class Experience(models.Model):
	"""
    Model for Experience
    """
	title = models.CharField(max_length=300)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class HourlyBudget(models.Model):
	"""
    Model for Hourly Budget 
    """
	title = models.CharField(max_length=300)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class Availability(models.Model):
	"""
    Model for Availability 
    """
	title = models.CharField(max_length=300)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class HighestQualification(models.Model):
	"""
    Model for Highest Qualification 
    """
	title = models.CharField(max_length=300)
	# programs = models.ManyToManyField(Programs, blank=True, related_name='programs')
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class Programs(models.Model):
	"""
    Model for Programs related to Highest Qualification 
    """
	title = models.CharField(max_length=300)
	highest_qualification = models.ForeignKey(HighestQualification, blank=True,null=True, related_name='highest_qualification')
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class University(models.Model):
	"""
    Model for University
    """
	title = models.CharField(max_length=300)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class Campus(models.Model):
	"""
    Model for Campus
    """
	title = models.CharField(max_length=300)
	university = models.ForeignKey(University, blank=True,null=True, related_name='university')
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class TeamSize(models.Model):
	"""
    Model for Team Size
    """
	title = models.IntegerField()
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return str(self.title)

class Country(models.Model):
	"""
    Model for Country
    """
	title = models.CharField(max_length=150)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class State(models.Model):
	"""
    Model for State
    """
	title = models.CharField(max_length=150)
	country = models.ForeignKey(Country, blank=True,null=True, related_name='states')
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class AvailabilityDaysPerYear(models.Model):
	"""
    Model for Availability Days Per Year
    """

	title = models.CharField(max_length=300)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class Hobbies(models.Model):
	"""
    Model for Hobbies
    """

	title = models.CharField(max_length=300)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.title

class Parameter(models.Model):
    """
    Model with Rating Parameters
    """
    title = models.CharField(max_length=100,null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Bank(models.Model):
    """
    Model for Bank
    """
    title = models.CharField(max_length=100,null=True)
    country = models.ForeignKey(Country, blank=True, null=True, related_name='banks')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

