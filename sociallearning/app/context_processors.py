from .models import UserProfile

def user_profile_context(request):
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        return {
            "username": request.user.username,
            "profile_picture": profile.profile_picture.url if profile and profile.profile_picture else None,
        }
    return {}