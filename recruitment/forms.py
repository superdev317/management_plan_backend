from django import forms

# Appointment Letter Form
class AppointmentLetterForm(forms.Form):
    job_title = forms.CharField()


