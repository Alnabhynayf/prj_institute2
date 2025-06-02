from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
# from dean.models import User
from django.db import models
# from dean.models import *   



# Create your models here.

# class User(AbstractUser):
#     is_student = models.BooleanField(default=False)
#     is_employee = models.BooleanField(default=False)
#     is_superuser = models.BooleanField(default=False)


class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    ]
    user = models.OneToOneField('dean.User', on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=200)
    nickname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)  # إضافة حقل الجنس

    def __str__(self):
        return self.full_name
    
class BirthInfo(models.Model):
    birth_date = models.DateField()
    birth_place = models.CharField(max_length=100)
    governorate = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    directorate = models.CharField(max_length=100, null=True, blank=True)  # إضافة حقل المديرية

    def __str__(self):
        return f"{self.birth_date} - {self.birth_place}"


class FatherInfo(models.Model):
    father_name = models.CharField(max_length=100, null=True, blank=True)
    father_phone = models.CharField(max_length=20, null=True, blank=True)
    father_job = models.CharField(max_length=100, null=True, blank=True)  # تعديل الحقل
    father_job_type = models.CharField(max_length=100, null=True, blank=True)  # إضافة نوع عمل الأب
    father_work_place = models.CharField(max_length=200, null=True, blank=True)  # إضافة مكان عمل الأب
    father_address = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.father_name if self.father_name else "No father name"


class PersonalInfo(models.Model):
    MARITAL_STATUS_CHOICES = [
        ('single', 'أعزب'),
        ('married', 'متزوج'),
        ('divorced', 'مطلق'),
        ('widowed', 'أرمل'),
    ]

    ID_TYPE_CHOICES = [
        ('personal', 'بطاقة شخصية'),
        ('election', 'بطاقة انتخابية'),
        ('passport', 'جواز سفر'),
    ]

    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    current_address = models.CharField(max_length=200, null=True, blank=True)
    permanent_address = models.CharField(max_length=200)
    id_number = models.CharField(max_length=50)
    id_type = models.CharField(max_length=10, choices=ID_TYPE_CHOICES)
    id_issue_date = models.DateField(null=True, blank=True)  # إضافة تاريخ إصدار البطاقة
    id_issue_place = models.CharField(max_length=100, null=True, blank=True)  # إضافة مكان إصدار البطاقة
    current_job = models.CharField(max_length=100, null=True, blank=True)  # إضافة العمل الحالي
    work_place = models.CharField(max_length=100, null=True, blank=True)  # إضافة مكان العمل
    employment_date = models.DateField(null=True, blank=True)  # إضافة تاريخ التوظيف
    secondary_phone = models.CharField(max_length=20, null=True, blank=True)  # إضافة هاتف آخر

    def __str__(self):
        return f"{self.id_type} - {self.id_number}"


class StudentDocuments(models.Model):
    id_image = models.FileField(upload_to='documents/')
    high_school_certificate = models.FileField(upload_to='documents/')
    grade_data = models.FileField(upload_to='documents/', null=True, blank=True)  # تعديل حقل عقد الإيجار
    criminal_record = models.FileField(upload_to='documents/')  # تعديل حقل السجل القانوني
    birth_certificate = models.FileField(upload_to='documents/')  # إضافة شهادة الميلاد

    def __str__(self):
        return f"Documents {self.id}"


class Qualification(models.Model):
    QUALIFICATION_TYPE_CHOICES = [
        ('diploma', 'دبلوم'),
        ('bachelor', 'بكلريوس'),
        ('master', 'ماجستير'),
    ]

    qualification_type = models.CharField(max_length=10, choices=QUALIFICATION_TYPE_CHOICES)
    university = models.CharField(max_length=200)
    gpa = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(4.0)])
    certificate_image = models.FileField(upload_to='qualifications/')
    qualification_date = models.DateField(null=True, blank=True)  # إضافة حقل تاريخ المؤهل
    grade = models.CharField(max_length=50, null=True, blank=True)  # إضافة حقل التقدير

    def __str__(self):
        return f"{self.get_qualification_type_display()} - {self.university}"

class Application(models.Model):
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('submitted', 'تم التقديم'),
        ('documents_reviewed', 'تم مراجعة المستندات'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.ForeignKey('dean.AcademicYear', on_delete=models.CASCADE)
    birth_info = models.ForeignKey(BirthInfo, on_delete=models.CASCADE)
    father_info = models.ForeignKey(FatherInfo, on_delete=models.CASCADE)
    personal_info = models.ForeignKey(PersonalInfo, on_delete=models.CASCADE)
    documents = models.ForeignKey(StudentDocuments, on_delete=models.CASCADE)
    qualifications = models.ManyToManyField(Qualification)
    application_date = models.DateTimeField(auto_now_add=True)
    department = models.ForeignKey('dean.Department', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    last_updated = models.DateTimeField(auto_now=True)
    
    def get_progress_percentage(self):
        if self.status == 'draft':
            return 0
        elif self.status == 'submitted':
            return 33
        elif self.status == 'documents_reviewed':
            return 66
        elif self.status in ['approved', 'rejected']:
            return 100
        return 0

    def get_current_stage(self):
        stages = {
            'draft': 'تقديم الطلب',
            'submitted': 'مراجعة المستندات',
            'documents_reviewed': 'القبول النهائي',
            'approved': 'مقبول',
            'rejected': 'مرفوض'
        }
        return stages.get(self.status, 'غير معروف')
        

    
class ApplicationStatus(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    stage = models.ForeignKey('dean.Stage', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_rejected = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('application', 'stage')
    
        get_latest_by = 'created_at'  # هذا السطر الجديد
        ordering = ['-created_at']  # إضافة هذا السطر أيضاً للإشارة إلى الترتيب الافتراضي  # منع تكرار المرحلة لنفس الطلب
