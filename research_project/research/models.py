from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

# ----------------------------
# Research Models
# ----------------------------

class Research(models.Model):
    title = models.CharField(max_length=255)
    pdf_document = models.FileField(upload_to='research_pdfs/')  # 'media/' не нужно — Django сам добавит
    participants = models.ManyToManyField(User, related_name='researches')
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_researches',
        null=True,
        blank=True
    )
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Research"
        verbose_name_plural = "Researches"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def average_rating(self):
        """Возвращает средний рейтинг по всем параметрам данного исследования."""
        avg = self.ratings.aggregate(avg_score=Avg('score'))['avg_score']
        return round(avg, 1) if avg is not None else 0


class Aspect(models.Model):
    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='aspects')
    stage_number = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['stage_number']
        verbose_name = "Aspect"
        verbose_name_plural = "Aspects"

    def __str__(self):
        return f"{self.research.title} — Stage {self.stage_number}: {self.name}"


class Parameter(models.Model):
    aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Parameter"
        verbose_name_plural = "Parameters"

    def __str__(self):
        return self.name

    def average_score(self):
        """Средний балл по этому параметру."""
        avg = self.rating_set.aggregate(avg_score=Avg('score'))['avg_score']
        return round(avg, 1) if avg is not None else 0


class Rating(models.Model):
    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    score = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"
        unique_together = ('user', 'parameter')  # предотвращаем дубли

    def __str__(self):
        return f"{self.user.username} — {self.parameter.name}: {self.score}"


class ResearchResult(models.Model):
    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='results')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    result_value = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Research Result"
        verbose_name_plural = "Research Results"

    def __str__(self):
        return f"{self.research.title} — {self.name}"