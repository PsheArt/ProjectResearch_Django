from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from .views import register

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),  
    path('register/', register, name='register'), 
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
]