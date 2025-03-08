from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from .models import UserProfile, ForumThread, ForumCategory, ForumReply
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
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
@method_decorator(login_required, name='dispatch')
class ForumCategoryListView(ListView):
    model = ForumCategory
    template_name = 'forum_categories.html'
    context_object_name = 'categories'

@method_decorator(login_required, name='dispatch')
class ForumThreadListView(ListView):
    model = ForumThread
    template_name = 'forum_threads.html'
    context_object_name = 'threads'

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return ForumThread.objects.filter(category__id=category_id) if category_id else ForumThread.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('category_id')
        context['category'] = get_object_or_404(ForumCategory, id=category_id)
        return context
    
class ForumThreadCreateView(View):
    def get(self, request, category_id):
        category = get_object_or_404(ForumCategory, id=category_id)
        return render(request, 'new_thread.html', {'category': category})

    def post(self, request, category_id):
        category = get_object_or_404(ForumCategory, id=category_id)
        title = request.POST.get('title')
        content = request.POST.get('content')

        if title and content:
            ForumThread.objects.create(
                category=category,
                user=request.user,
                title=title,
                content=content
            )
            return redirect('forum_threads', category_id=category.id)

        return render(request, 'new_thread.html', {'category': category, 'error': 'All fields are required'})
    
@method_decorator(login_required, name='dispatch')
class ForumThreadDetailView(DetailView):
    model = ForumThread
    template_name = 'forum_thread_detail.html'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['replies'] = self.object.replies.select_related('user').all()
        context['category'] = self.object.category
        return context

    
class ForumReplyCreateView(View):
    def post(self, request, thread_id):
        thread = get_object_or_404(ForumThread, id=thread_id)
        content = request.POST.get('content')

        if content:
            category_name = thread.category.name 
            
            ForumReply.objects.create(
                thread=thread,
                user=request.user,
                content=content,
                category=category_name
            )
            
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            user_profile.increment_category_count(category_name)
            
            return redirect('forum_thread_detail', pk=thread.id)

        return redirect('forum_thread_detail', pk=thread.id)

class LikeThreadView(View):
    def post(self, request, thread_id):
        thread = get_object_or_404(ForumThread, id=thread_id)
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)

        category_name = str(thread.category)

        if not user_profile.category_like_count:
            user_profile.category_like_count = {}

        if not user_profile.category_dislike_count:
            user_profile.category_dislike_count = {}

        if request.user in thread.likes.all():
            thread.likes.remove(request.user)
            user_profile.category_like_count[category_name] -= 1
            liked = False
        else:
            thread.likes.add(request.user)
            thread.dislikes.remove(request.user)
            user_profile.category_like_count[category_name] = user_profile.category_like_count.get(category_name, 0) + 1
            user_profile.category_dislike_count[category_name] = max(user_profile.category_dislike_count.get(category_name, 0) - 1, 0)
            liked = True

        thread.save()
        user_profile.save()

        return JsonResponse({"liked": liked, "total_likes": thread.total_likes(), "total_dislikes": thread.total_dislikes()})


class DislikeThreadView(View):
    def post(self, request, thread_id):
        thread = get_object_or_404(ForumThread, id=thread_id)
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)

        category_name = str(thread.category)

        if not user_profile.category_like_count:
            user_profile.category_like_count = {}

        if not user_profile.category_dislike_count:
            user_profile.category_dislike_count = {}

        if request.user in thread.dislikes.all():
            thread.dislikes.remove(request.user)
            user_profile.category_dislike_count[category_name] -= 1
            disliked = False
        else:
            thread.dislikes.add(request.user)
            thread.likes.remove(request.user)
            user_profile.category_dislike_count[category_name] = user_profile.category_dislike_count.get(category_name, 0) + 1
            user_profile.category_like_count[category_name] = max(user_profile.category_like_count.get(category_name, 0) - 1, 0)
            disliked = True

        thread.save()
        user_profile.save()

        return JsonResponse({"disliked": disliked, "total_likes": thread.total_likes(), "total_dislikes": thread.total_dislikes()})

class UserProfileView(TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        context['profile'] = user_profile
        return context

class LikeDislikeStatsView(LoginRequiredMixin, TemplateView):
    template_name = "like_dislike_stats.html"

    def get(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        return render(request, self.template_name, {
            "category_like_count": user_profile.category_like_count,
            "category_dislike_count": user_profile.category_dislike_count
        })