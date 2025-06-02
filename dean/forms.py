from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from students.models import *
from committee.models import *

from django.core.validators import MinValueValidator, MaxValueValidator


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        labels = {
            'username': 'اسم المستخدم',
            'password1': 'كلمة المرور',
            'password2': 'تأكيد كلمة المرور',
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'اسم المستخدم'}),
        }

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'phone', 'role', 'email']
        labels = {
            'name': 'الاسم',
            'phone': 'رقم الهاتف',
            'role': 'الدور',
            'email': 'البريد الإلكتروني',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'type': 'tel'}),
            'email': forms.EmailInput(),
            'role': forms.Select(choices=Employee.ROLE_CHOICES),
        }


class DeanDecisionForm(forms.Form):
    DECISION_CHOICES = [
        ('accept', 'قبول ونقل للمرحلة التالية'),
        ('reject', 'رفض الطلب'),
    ]
    
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect,
        label='القرار'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label='التعليق',
        required=True
    )


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['department', 'year']
        widgets = {
            'department': forms.Select(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500'
            }),
            'year': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500',
                'placeholder': 'مثال: 2023-2024'
            }),
        }
        labels = {
            'department': 'القسم',
            'year': 'العام الدراسي',
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['department', 'name', 'material_type']
        widgets = {
            'department': forms.Select(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500'
            }),
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500',
                'placeholder': 'اسم المادة'
            }),
            'material_type': forms.Select(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500'
            }),
        }
        labels = {
            'department': 'القسم',
            'name': 'اسم المادة',
            'material_type': 'نوع المادة',
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500',
                'placeholder': 'اسم القسم'
            }),
        }
        labels = {
            'name': 'اسم القسم',
        }

class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500',
                'placeholder': 'اسم المرحلة'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 bg-gray-50 py-2 px-3 text-sm focus:border-yellow-500 focus:ring-yellow-500',
                'placeholder': 'ترتيب المرحلة (رقم)'
            }),
        }
        labels = {
            'name': 'اسم المرحلة',
            'order': 'ترتيب المرحلة',
        }


class GroupForm(forms.ModelForm):
    capacity = forms.IntegerField(
        min_value=1,
        label="القدرة الاستيعابية",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Group
        fields = ['capacity']

class StatusFilterForm(forms.Form):
    stage = forms.ModelChoiceField(
        queryset=Stage.objects.all(),
        label="المرحلة",
        required=False
    )
    
    status_type = forms.ChoiceField(
        choices=[('all', 'جميع الحالات')] + (ApplicationStatus._meta.get_field('stage').choices or []),
        label="نوع الحالة",
        required=False
    )

class GroupAnnouncementForm(forms.ModelForm):
    announcement_type = forms.CharField(
        initial='private',
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        label='نوع الإعلان'
    )
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'announcement_type', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4})
        }

class PublicAnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'title': 'عنوان الإعلان',
            'content': 'محتوى الإعلان',
            'attachment': 'مرفق (اختياري)',
        }
