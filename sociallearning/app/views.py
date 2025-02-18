from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
# Create your views here.

# Forms
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, "Login successful!")
            return redirect("homepage")
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register.html")
            
        user = User.objects.create_user(username=username, password=password)
        messages.success(request, "Registration successful!")
        return redirect('login')
        
    return render(request, 'register.html')

# User Home
def homepage(request):
    return render(request, 'homepage.html')

def logoutView(request):
    logout(request)
    return redirect('login')