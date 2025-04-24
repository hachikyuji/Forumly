from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from .models import UserProfile, ForumThread, ForumCategory, ForumReply, ForumViewHistory, RecommendedTopicHistory, Notification
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from .q_learning_recommendation import QLearningRecommender 
from textblob import TextBlob
from datetime import timedelta
from django.utils import timezone
import json
import re
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
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            
            if user_profile.restricted:
                if user_profile.restricted_expires_at:
                    readable_time = timezone.localtime(user_profile.restricted_expires_at).strftime('%b %d, %Y at %I:%M %p')
                    messages.error(request, f"Account restricted until {readable_time}.")
                else:
                    messages.error(request, "Account is restricted.")
                return redirect("login")
            
            auth_login(request, user)
            messages.success(request, "Login successful!")
            return redirect("homepage")
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

def is_valid_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"\d", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        age = request.POST.get("age", "").strip()
        age_str = request.POST.get("age")
        
        if age_str:
            try:
                validate_age = int(age_str)
                if validate_age < 0:
                    raise ValueError("Age cannot be negative")
            except ValueError:
                # Handle invalid input, e.g., return an error message or render a form with an error
                messages.error(request, "All fields are required.")
                return render(request, "register.html")
        else:
            validate_age = None

        # Validate required fields
        if not username or not password or not age:
            messages.error(request, "All fields are required.")
            return render(request, "register.html")
        
        if not is_valid_password(password):
            messages.error(request, "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.") 
            return render(request, "register.html")
        
        if validate_age < 13:
            messages.error(request, "Age must be 13 or above.")
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

@login_required
def homepage(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # ---------- existing ε‑greedy list ----------
    state = q_learning_model.get_state(user_profile, request.user.id)
    recommended_topics = q_learning_model.recommend_topics(user_profile, request.user.id)
    general_data = [{
        "title": topic.title,
        "category": topic.category.name,
        "id": topic.id
    } for topic in recommended_topics]

    # ---------- NEW: positive‑reward list ----------
    pos_pairs = q_learning_model.get_positive_reward_topics(request.user.id)
    positive_data = [{
        "title": topic.title,
        "category": topic.category.name,
        "id": topic.id,
        "reward": round(reward, 2)
    } for reward, topic in pos_pairs]

    return render(request, 'homepage.html', {
        'recommended_topics': general_data,
        'positive_topics':   positive_data,
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
            if not is_valid_password(new_password):
                messages.error(request, "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.")
                return redirect("update_profile")
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
        thread = self.object
        
        context['replies'] = self.object.replies.select_related('user').all()
        context['category'] = self.object.category
        
        context['user_has_liked'] = thread.likes.filter(id=self.request.user.id).exists()
        context['user_has_disliked'] = thread.dislikes.filter(id=self.request.user.id).exists()
        
        next_thread = ForumThread.objects.filter(
            category=thread.category,
            id__gt=thread.id
        ).order_by('id').first()
        context['next_thread'] = next_thread
        
        return context

    
class ForumReplyCreateView(View):
    def post(self, request, thread_id):
        thread = get_object_or_404(ForumThread, id=thread_id)
        content = request.POST.get('content')

        if content:
            category_name = thread.category.name
            
            sentiment_score = TextBlob(content).sentiment.polarity
            
            ForumReply.objects.create(
                thread=thread,
                user=request.user,
                content=content,
                category=category_name,
                sentiment_score=sentiment_score,
            )

            # Notify the thread owner (if it's not the same user)
            if thread.user != request.user:
                Notification.objects.create(
                    user=thread.user,
                    message=f"{request.user.username} commented on your thread '{thread.title}'.",
                    thread = thread
                )
            
            # Detect mentions and notify mentioned users
            mention_regex = r'@(\w+)'
            mentioned_users = re.findall(mention_regex, content)

            for username in mentioned_users:
                mentioned_user = User.objects.filter(username=username).first()
                if mentioned_user and mentioned_user != request.user:
                    Notification.objects.create(
                        user=mentioned_user,
                        message=f"{request.user.username} mentioned you in a comment on '{thread.title}'.",
                        thread = thread
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

            # Send notification to thread owner
            if request.user != thread.user:
                Notification.objects.create(
                    user=thread.user,
                    message=f"{request.user.username} liked your thread '{thread.title}'.",
                    thread = thread
                )

        thread.save()
        user_profile.save()

        return JsonResponse({"liked": liked, "total_likes": thread.total_likes(), "total_dislikes": thread.total_dislikes()})


class DislikeThreadView(View):
    def post(self, request, thread_id):
        thread = get_object_or_404(ForumThread, id=thread_id)
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)

        category_name = str(thread.category)

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

            # Send notification to thread owner
            if request.user != thread.user:
                Notification.objects.create(
                    user=thread.user,
                    message=f"{request.user.username} disliked your thread '{thread.title}'.",
                    thread = thread
                )

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

#Comment Mentioning Checker
def check_user_exists(request):
    username = request.GET.get("username", "")
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({"exists": exists})

#Notification functions
@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user).select_related('thread').order_by('-created_at')

    return render(request, "notification.html", {"notifications": user_notifications})


@login_required
def read_all_notifications(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({"status": "success"})  # Return JSON instead of re-rendering

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@login_required
def mark_notification_read(request):
    if request.method == "POST":
        notif_id = request.POST.get("notif_id")
        notification = get_object_or_404(Notification, id=notif_id, user=request.user)

        if not notification.is_read:  # Only update if unread
            notification.is_read = True
            notification.save()
        
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@login_required
def clear_notifications(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user).delete()
        return render(request, 'notification.html')
    return JsonResponse({"error": "Invalid request."}, status=400)


@method_decorator(login_required, name='dispatch')
class UserProfilesListView(ListView):
    model = UserProfile
    template_name = "user_data.html"
    context_object_name = "users"

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        if search_query:
            return UserProfile.objects.filter(user__username__icontains=search_query)
        return UserProfile.objects.all()
            
class RestrictUserView(View):
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        user_profile.restricted = True
        user_profile.restricted_expires_at = timezone.now() + timedelta(days=1)
        user_profile.save()
        
        messages.success(request, "User restricted for 3 days!")
        return redirect("user-data")
