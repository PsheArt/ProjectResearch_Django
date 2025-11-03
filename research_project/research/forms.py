from django import forms
from .models import Research, Aspect, Parameter, Rating

class ResearchForm(forms.ModelForm):
    class Meta:
        model = Research
        fields = ['title', 'pdf_document']
        widgets = {
            "title" : forms.TextInput(attrs={"class" : "title"}),
        }
        labels = {
            "title": "Название",
            'pdf_document': "Документ",
            'participants': "Эксперты",
        }

class AspectForm(forms.ModelForm):
    class Meta:
        model = Aspect
        fields = ['name', 'stage_number']

class ParameterForm(forms.ModelForm):
    class Meta:
        model = Parameter
        fields = ['name']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['parameter','score']


