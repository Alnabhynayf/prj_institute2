from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from django.core.validators import MinValueValidator, MaxValueValidator
from dean.models import *   
from students.models import *   


class CommitteeOpinionForm(forms.ModelForm):
    class Meta:
        model = CommitteeOpinion
        fields = ['opinion', 'description']
        labels = {
            'opinion': 'الرأي',
            'description': 'التعليق',
        }
        widgets = {
            'opinion': forms.RadioSelect(choices=CommitteeOpinion.OPINION_CHOICES),
            # 'notes': forms.Textarea(attrs={'rows': 3}),            
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'أدخل تعليقك المفصل هنا'
            }),
        }

class StageResultForm(forms.ModelForm):
    class Meta:
        model = StageResult
        fields = ['document', 'description']
        labels = {
            'document': 'المستند',
            'description': 'الوصف',
        }
        widgets = {
            'document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'أدخل وصفاً للنتائج'
            }),
        }

class SubjectResultForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.HiddenInput()
    )
    score = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='الدرجة'
    )

    def __init__(self, *args, **kwargs):
        department = kwargs.pop('department', None)
        material_type = kwargs.pop('material_type', None)
        super().__init__(*args, **kwargs)
        if department and material_type:
            self.fields['subject'].queryset = Subject.objects.filter(
                department=department,
                material_type=material_type
            )
