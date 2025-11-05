from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

class Research(models.Model):
    title = models.CharField(max_length=255, )
    pdf_document = models.FileField(upload_to='media/research_pdfs/')
    participants = models.ManyToManyField(User, related_name='researches')
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_researches', null=True)
    is_completed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def average_rating(self):
        parameters = Parameter.objects.filter(aspect__research=self)
        ratings = Rating.objects.filter(parameter__in=parameters)
        if not ratings.exists():
            return 0
        average_score = ratings.aggregate(Avg('score'))['score__avg']
        return round(average_score, 1) if average_score is not None else 0
    
    def save(self, *args, **kwargs):
        if not self.author:
            self.author = kwargs.pop('user', None)
        super().save(*args, **kwargs)

class Aspect(models.Model):
    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='aspects')
    stage_number = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Parameter(models.Model):
    aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


    
class ResultResearch(models.Model):
    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='resultResearch')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    result_value = models.TextField(null=True)

    def __str__(self): 
        return f'{self.research} - {self.name}'