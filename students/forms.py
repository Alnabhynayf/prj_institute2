from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from django.core.validators import MinValueValidator, MaxValueValidator
from dean.models import *   


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'nickname', 'phone', 'email', 'gender']  # إضافة حقل الجنس
        labels = {
            'full_name': 'الاسم الرباعي',
            'nickname': 'اللقب',
            'phone': 'رقم الهاتف',
            'email': 'البريد الإلكتروني',
            'gender': 'الجنس',  # تسمية الحقل الجديد
        }
        widgets = {
            'phone': forms.TextInput(attrs={'type': 'tel'}),
            'email': forms.EmailInput(),
            'gender': forms.Select(choices=Student.GENDER_CHOICES),  # إضافة عنصر واجهة المستخدم لحقل الجنس
        }


class BirthInfoForm(forms.ModelForm):
    class Meta:
        model = BirthInfo
        fields = ['birth_date', 'birth_place', 'governorate', 'district', 'directorate']  # إضافة حقل المديرية
        labels = {
            'birth_date': 'تاريخ الميلاد',
            'birth_place': 'مكان الميلاد',
            'governorate': 'المحافظة',
            'district': 'العزلة',
            'directorate': 'المديرية',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }


class FatherInfoForm(forms.ModelForm):
    class Meta:
        model = FatherInfo
        fields = ['father_name', 'father_phone', 'father_job', 'father_job_type', 'father_work_place', 'father_address']  # إضافة الحقول الجديدة
        labels = {
            'father_name': 'اسم الأب',
            'father_phone': 'رقم هاتف الأب',
            'father_job': 'عمل الأب',
            'father_job_type': 'نوع عمل الأب',  # الحقل الجديد
            'father_work_place': 'مكان عمل الأب',  # الحقل الجديد
            'father_address': 'سكن الأب',
        }
        widgets = {
            'father_phone': forms.TextInput(attrs={'type': 'tel'}),
        }


class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = PersonalInfo
        fields = [
            'marital_status', 'current_address', 'permanent_address', 'id_number', 'id_type',
            'id_issue_date', 'id_issue_place', 'current_job', 'work_place', 'employment_date', 'secondary_phone'
        ]  # إضافة الحقول الجديدة
        labels = {
            'marital_status': 'الحالة الاجتماعية',
            'current_address': 'السكن الحالي',
            'permanent_address': 'السكن الدائم',
            'id_number': 'رقم البطاقة',
            'id_type': 'نوع البطاقة',
            'id_issue_date': 'تاريخ إصدار البطاقة',  # الحقل الجديد
            'id_issue_place': 'مكان إصدار البطاقة',  # الحقل الجديد
            'current_job': 'العمل الحالي',  # الحقل الجديد
            'work_place': 'مكان العمل',  # الحقل الجديد
            'employment_date': 'تاريخ التوظيف',  # الحقل الجديد
            'secondary_phone': 'هاتف آخر',  # الحقل الجديد
        }
        widgets = {
            'marital_status': forms.Select(choices=PersonalInfo.MARITAL_STATUS_CHOICES),
            'id_type': forms.Select(choices=PersonalInfo.ID_TYPE_CHOICES),
            'id_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'employment_date': forms.DateInput(attrs={'type': 'date'}),
        }


class StudentDocumentsForm(forms.ModelForm):
    class Meta:
        model = StudentDocuments
        fields = ['id_image', 'high_school_certificate', 'grade_data', 'criminal_record', 'birth_certificate']  # تعديل الحقول
        labels = {
            'id_image': 'صورة البطاقة',
            'high_school_certificate': 'صورة الشهادة الثانوية',
            'grade_data': 'بيانات الدرجات',  # الحقل المعدل
            'criminal_record': 'الصحيفة الجنائية',  # الحقل المعدل
            'birth_certificate': 'شهادة الميلاد',  # الحقل الجديد
        }
        widgets = {
            'id_image': forms.ClearableFileInput(),
            'high_school_certificate': forms.ClearableFileInput(),
            'grade_data': forms.ClearableFileInput(),
            'criminal_record': forms.ClearableFileInput(),
            'birth_certificate': forms.ClearableFileInput(),
        }


class QualificationForm(forms.ModelForm):
    class Meta:
        model = Qualification
        fields = ['qualification_type', 'university', 'gpa', 'certificate_image', 'qualification_date', 'grade']  # إضافة الحقول الجديدة
        labels = {
            'qualification_type': 'نوع المؤهل',
            'university': 'الجامعة',
            'gpa': 'المعدل',
            'certificate_image': 'صورة الشهادة',
            'qualification_date': 'تاريخ المؤهل',  # الحقل الجديد
            'grade': 'التقدير',  # الحقل الجديد
        }
        widgets = {
            'qualification_type': forms.Select(choices=Qualification.QUALIFICATION_TYPE_CHOICES),
            'gpa': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '4'}),
            'certificate_image': forms.ClearableFileInput(),
            'qualification_date': forms.DateInput(attrs={'type': 'date'}),  # الحقل الجديد
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['department', 'academic_year']
        labels = {
            'department': 'القسم',
            'academic_year': 'العام الدراسي',
        }
