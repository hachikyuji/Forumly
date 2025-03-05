from django.contrib import admin
from .models import UserProfile, ForumThread, ForumCategory, ForumReply
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(ForumThread)
admin.site.register(ForumCategory)
admin.site.register(ForumReply)