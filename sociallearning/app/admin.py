from django.contrib import admin
from .models import UserProfile, ForumThread, ForumCategory
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(ForumThread)
admin.site.register(ForumCategory) 