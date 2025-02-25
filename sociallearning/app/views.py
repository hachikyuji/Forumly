from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Thread, Post
from django.http import JsonResponse
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
@login_required
def homepage(request):
    return render(request, 'homepage.html')

def logoutView(request):
    logout(request)
    return redirect('login')

# Account Settings
@login_required
def update_profile(request):
    if request.method == "POST":
        user = request.user
        username = request.POST.get("username")
        new_password = request.POST.get("new_password")  
        profile_picture = request.FILES.get("profile_picture")
        # Updating user info
        if username:
            user.username = username

        if new_password:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)

        user.save()

        profile, created = UserProfile.objects.get_or_create(user=user)
        if profile_picture:
            profile.profile_picture = profile_picture
            profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("update_profile")
    
    return render(request, 'settings.html')

# Forums
@login_required
def forum_home(request):
    threads = Thread.objects.all().order_by('-created_at')
    return render(request, 'forum_home.html', {'threads': threads})

@login_required
def create_thread(request):
    if request.method == 'POST':
        title = request.POST.get("title", "").strip()
        if title:
            thread = Thread.objects.create(title=title, created_by=request.user)
            return JsonResponse({"status": "success", "thread_id": thread.id, "title": thread.title, "username": request.user.username})
        return JsonResponse({"status": "error", "message": "Title cannot be empty."})
    return JsonResponse({"status": "error", "message": "Invalid request."})

def thread_detail(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    posts = thread.posts.all().order_by("created_at")
    return render(request, "thread_detail.html", {"thread": thread, "posts": posts})

@login_required
def add_post(request, thread_id):
    if request.method == "POST":
        thread = get_object_or_404(Thread, id=thread_id)
        content = request.POST.get("content", "").strip()
        if content:
            post = Post.objects.create(thread=thread, created_by=request.user, content=content)
            return JsonResponse({"status": "success", "content": post.content, "username": request.user.username})
        return JsonResponse({"status": "error", "message": "Reply cannot be empty."})
    return JsonResponse({"status": "error", "message": "Invalid request."})