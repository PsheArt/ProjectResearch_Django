from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Research, Aspect, Parameter, Rating
from django.contrib.auth.models import User


class ResearchForm(forms.ModelForm):
    # Явно добавляем поле participants, если оно нужно в форме
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2-multiple',  # можно подключить Select2
            'data-placeholder': 'Выберите экспертов...'
        }),
        required=False,
        label="Эксперты"
    )

    class Meta:
        model = Research
        fields = ['title', 'pdf_document', 'participants']  # добавили participants
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название исследования'
            }),
            'pdf_document': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
        }
        labels = {
            'title': 'Название',
            'pdf_document': 'PDF-документ',
        }


class AspectForm(forms.ModelForm):
    class Meta:
        model = Aspect
        fields = ['name', 'stage_number']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название аспекта'
            }),
            'stage_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Номер этапа'
            })
        }
        labels = {
            'name': 'Аспект',
            'stage_number': 'Этап (номер)',
        }


class ParameterForm(forms.ModelForm):
    class Meta:
        model = Parameter
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название параметра'
            })
        }
        labels = {
            'name': 'Параметр',
        }


class RatingForm(forms.ModelForm):
    score = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control rating-input',
            'min': '1',
            'max': '5',  # настройте по вашей шкале
            'placeholder': '1–5'
        }),
        validators=[
            MinValueValidator(1, message="Оценка не может быть меньше 1"),
            MaxValueValidator(5, message="Оценка не может быть больше 5")
        ],
        label="Оценка"
    )

    class Meta:
        model = Rating
        fields = ['parameter', 'score']
        widgets = {
            'parameter': forms.HiddenInput(),  # обычно параметр не редактируется вручную
        }