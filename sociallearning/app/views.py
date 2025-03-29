from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from .models import UserProfile, ForumThread, ForumCategory, ForumReply, ForumViewHistory, RecommendedTopicHistory
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from .q_learning_recommendation import QLearningRecommender  # Import the Q-learning model
import json
#test
from django.core.exceptions import ObjectDoesNotExist
#Visualization
from django.shortcuts import render
#Permission Denied (403)
from django.core.exceptions import PermissionDenied

# Initialize Q-Learning Model
q_learning_model = QLearningRecommender()

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
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        age = request.POST.get("age", "").strip()

        # Validate required fields
        if not username or not password or not age:
            messages.error(request, "All fields are required.")
            return render(request, "register.html")

        # Check username uniqueness
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register.html")

        # Create the user
        user = User.objects.create_user(username=username, password=password)
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.age = int(age)
        profile.save()

        # Log in the user
        auth_login(request, user)

        messages.success(request, "Registration successful!")
        return redirect("login")

    return render(request, "register.html")

# User Home
@login_required
def homepage(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # Step 1: Gather Data for Q-Learning Model
    state = q_learning_model.get_state(user_profile, request.user.id)

    # Step 2: Generate Recommendations
    recommended_topics = q_learning_model.recommend_topics(user_profile, request.user.id)

    # Step 3: Prepare Data for Frontend
    recommended_data = [
        {
            "title": topic.title,
            "category": topic.category.name,
            "id": topic.id
        }
        for topic in recommended_topics
    ]

    return render(request, 'homepage.html', {
        'recommended_topics': recommended_data
    })

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

#About Us
@login_required
def about_us(request):
    return render(request, 'about_us.html')

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

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Track viewed recommendation
        thread = self.get_object()
        RecommendedTopicHistory.objects.filter(
            user=request.user,
            forum_thread=thread
        ).update(viewed=True)

        return response

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
        
@csrf_exempt
def track_time_spent(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user = request.user
        category_id = data.get("category_id")
        time_spent = data.get("time_spent")

        category = ForumCategory.objects.get(id=category_id)

        ForumViewHistory.objects.create(user=user, category=category, time_spent=time_spent)

        return JsonResponse({"message": "Time recorded"}, status=200)

    return JsonResponse({"error": "Invalid request"}, status=400)

#tests
@login_required
def test_recommendation(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        recommendations = q_learning_model.recommend_topics(user_profile, request.user.id)
        
        recommendation_data = [
            {
                "title": topic.title,
                "category": topic.category.name,
                "reward": q_learning_model.calculate_reward(user_profile, request.user.id, topic.category.name, topic.id)
            }
            for topic in recommendations
        ]
        
        return JsonResponse({"recommendations": recommendation_data})

    except ObjectDoesNotExist:
        return JsonResponse({"error": "User profile not found."}, status=404)

@login_required
def reset_QL(request):
    if not request.user.profile.admin: 
        raise PermissionDenied  # This will trigger Django's 403 error page

    if request.method == "POST":
        q_learning_model.reset_q_learning_data()
        return JsonResponse({"success": "✅ QL-related data has been successfully reset."})

    return render(request, 'reset_QL.html')