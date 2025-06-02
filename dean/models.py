from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
from students.models import *   
# from committee.models import *   

class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

class Department(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class AcademicYear(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.department} - {self.year}"

class Subject(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    MATERIAL_TYPE_CHOICES = [
        ('oral', 'شفوي'),
        ('written', 'تحريري'),
    ]
    material_type = models.CharField(
        max_length=10, 
        choices=MATERIAL_TYPE_CHOICES, 
        null=True, 
        blank=True
    )
    
    def __str__(self):
        return f"{self.department} - {self.name}"
    

class Stage(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(unique=True)  # لترتيب المراحل
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name




class Employee(models.Model):
    ROLE_CHOICES = [
        ('dean', 'عميد'),
        ('data_entry', 'مدخل بيانات'),
        ('committee_member', 'عضو لجنة'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"



class Group(models.Model):
    # statuses = models.ManyToManyField(ApplicationStatus, verbose_name="حالات الطلب")
    statuses = models.ManyToManyField('students.ApplicationStatus', verbose_name="حالات الطلب")
    # بقية الحقول...
    capacity = models.PositiveIntegerField("القدرة الاستيعابية")
    group_number = models.PositiveIntegerField("رقم المجموعة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مجموعة'
        verbose_name_plural = 'المجموعات'
        unique_together = ('group_number', 'created_at')

    def __str__(self):
        return f"المجموعة {self.group_number} - {self.created_at.strftime('%Y-%m-%d')}"

class Announcement(models.Model):
    ANNOUNCEMENT_TYPE_CHOICES = [
        ('general', 'عام'),
        ('private', 'خاص'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=10, choices=ANNOUNCEMENT_TYPE_CHOICES,default='general')
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)  # أضف هذا الحقل
    read_at = models.DateTimeField(null=True, blank=True)  # اختياري: لإضافة وقت القراءة
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name='الطالب المستهدف'
    )
    


    def __str__(self):
        return self.title

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def get_announcement_type_display(self):
        return "عام" if self.is_public else "خاص"





