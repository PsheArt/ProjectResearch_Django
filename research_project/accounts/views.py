from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect

from research_project.settings import EMAIL_HOST_USER
from .forms import CustomUserCreationForm

from django.core.mail import send_mail
from django.contrib import messages

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm


def register(request):
    form = UserCreationForm() 
    if request.method == 'POST': 
        if form.is_valid(): 
            form.save() 
            authenticate(username=request.user.username, password=request.user.password)
            login(request, request.user)
            print(request.user)
            return redirect('research_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('research_list')
        else:
            messages.error(request, "Неверные учетные данные")
    
    return render(request, 'registration/login.html')

def user_logout(request):
    logout(request)
    return redirect('research_list')