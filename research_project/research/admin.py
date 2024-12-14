
from django.contrib import admin
from .models import Aspect, Research, Parameter, Rating, ResultResearch

# Register your models here.
admin.site.register(Research)
admin.site.register(Aspect)
admin.site.register(Parameter)
admin.site.register(Rating)
admin.site.register(ResultResearch)