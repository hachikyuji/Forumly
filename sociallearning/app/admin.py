from django.contrib import admin
from .models import UserProfile, ForumThread, ForumCategory, ForumReply, ForumViewHistory
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(ForumThread)
admin.site.register(ForumCategory)
admin.site.register(ForumReply)
admin.site.register(ForumViewHistory)