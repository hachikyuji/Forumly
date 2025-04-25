from .models import UserProfile, ForumCategory, Notification

def user_profile_context(request):
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        return {
            "username": request.user.username,
            "profile_picture": profile.profile_picture.url if profile and profile.profile_picture else None,
        }
    return {}

def forum_categories(request):
    categories = ForumCategory.objects.all()
    return {'categories': categories}

def notification_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        count = 0
    return {'notification_count': count }