from django import forms
from .models import Student, LearningPath
from django.core.exceptions import ValidationError
from datetime import datetime, date

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_id', 'first_name', 'last_name', 'photo']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter student ID'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if not student_id:
            raise ValidationError("Student ID is required.")
        if Student.objects.filter(student_id=student_id).exists() and self.instance.pk is None:
            raise ValidationError("A student with this ID already exists.")
        return student_id

class LearningPathForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        fields = ['task_name', 'start_date', 'estimated_end_date', 'required_duration', 'used_leave', 'notes']
        widgets = {
            'task_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task name'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'estimated_end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'required_duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2 weeks'
            }),
            'used_leave': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2 days (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['used_leave'].required = False
        self.fields['notes'].required = False
        # Form alanlarının modal içinde düzgün görünmesi için ek class'lar
        for field in self.fields.values():
            if 'class' in field.widget.attrs and 'form-control' in field.widget.attrs['class']:
                field.widget.attrs['class'] += ' update-learning-path-form-control'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        estimated_end_date = cleaned_data.get('estimated_end_date')
        used_leave = cleaned_data.get('used_leave')
        notes = cleaned_data.get('notes')

        # Tarih kontrolü: Başlangıç tarihi bitiş tarihinden sonra olamaz
        if start_date and estimated_end_date:
            if isinstance(start_date, date):
                start_date = datetime.combine(start_date, datetime.min.time())
            if isinstance(estimated_end_date, date):
                estimated_end_date = datetime.combine(estimated_end_date, datetime.min.time())
            if start_date > estimated_end_date:
                raise ValidationError("Start date cannot be later than the estimated end date.")
            # Başlangıç tarihinin geçmişte olup olmadığını kontrol et
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if start_date < today and not self.instance.pk:  # Yeni kayıtlar için
                raise ValidationError("Start date cannot be in the past for new learning paths.")

        # Used_leave ve notes alanlarını temizleme
        if used_leave:
            cleaned_data['used_leave'] = used_leave.strip()
        else:
            cleaned_data['used_leave'] = None

        if notes:
            cleaned_data['notes'] = notes.strip()
        else:
            cleaned_data['notes'] = None

        return cleaned_data

    def clean_required_duration(self):
        required_duration = self.cleaned_data.get('required_duration')
        if not required_duration:
            raise ValidationError("Required duration is mandatory.")
        return required_duration.strip()