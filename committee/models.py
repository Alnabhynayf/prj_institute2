from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
from students.models import ApplicationStatus   
from dean.models import Employee # بدلاً من from dean.models import *

# Create your models here.

# class User(AbstractUser):
#     is_student = models.BooleanField(default=False)
#     is_employee = models.BooleanField(default=False)
#     is_superuser = models.BooleanField(default=False)


class CommitteeOpinion(models.Model):
    OPINION_CHOICES = [
        ('accept', 'قبول'),
        ('reject', 'رفض'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    application_status = models.ForeignKey(ApplicationStatus, on_delete=models.CASCADE)
    description = models.TextField()
    opinion = models.CharField(max_length=10, choices=OPINION_CHOICES)
    # opinion = models.CharField(max_length=10, choices=[('accept', 'قبول'), ('reject', 'رفض')])
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        unique_together = ('employee', 'application_status')  # منع تكرار الرأي

class StageResult(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    document = models.FileField(upload_to='stage_results/', null=True, blank=True)
    application_status = models.ForeignKey(ApplicationStatus, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    score = JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employee} - {self.application_status}"

