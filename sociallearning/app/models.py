from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.IntegerField(null=True, blank=True)
    interests = models.JSONField(default=list, null=True, blank=True)  # List of user interests
    historical_preferences = models.JSONField(default=list, null=True, blank=True)  # Previous topic preferences
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
    
    def __str__(self):
        return self.user.username