from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.IntegerField(null=True, blank=True)
    interests = models.JSONField(default=list, null=True, blank=True)  # List of user interests
    historical_preferences = models.JSONField(default=list, null=True, blank=True)  # Previous topic preferences
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
    category_comment_count = models.JSONField(default=dict)
    category_like_count = models.JSONField(default=dict)
    category_dislike_count = models.JSONField(default=dict)
    
    def increment_category_count(self, category_name):
        """Increase the count for a given category"""
        if not self.category_comment_count:
            self.category_comment_count = {} 
        
        if category_name in self.category_comment_count:
            self.category_comment_count[category_name] += 1
        else:
            self.category_comment_count[category_name] = 1
        
        self.save()
    
    def increment_like_count(self, category_name):
        """Increase the like count for a given category"""
        if not self.category_like_count:
            self.category_like_count = {}

        self.category_like_count[category_name] = self.category_like_count.get(category_name, 0) + 1
        self.save()

    def decrement_like_count(self, category_name):
        """Decrease the like count for a given category (if > 0)"""
        if self.category_like_count and category_name in self.category_like_count and self.category_like_count[category_name] > 0:
            self.category_like_count[category_name] -= 1
            self.save()

    def increment_dislike_count(self, category_name):
        """Increase the dislike count for a given category"""
        if not self.category_dislike_count:
            self.category_dislike_count = {}

        self.category_dislike_count[category_name] = self.category_dislike_count.get(category_name, 0) + 1
        self.save()

    def decrement_dislike_count(self, category_name):
        """Decrease the dislike count for a given category (if > 0)"""
        if self.category_dislike_count and category_name in self.category_dislike_count and self.category_dislike_count[category_name] > 0:
            self.category_dislike_count[category_name] -= 1
            self.save()
    
    def __str__(self):
        return self.user.username

class ForumCategory(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
    
class ForumThread(models.Model):
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name="threads")
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='like_threads', blank=True)
    dislikes = models.ManyToManyField(User, related_name='dislike_threads', blank=True)
    
    def __str__(self):
        return self.title
    
    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()

class ForumReply(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name="replies")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=200)
    
    def __str__(self):
        return self.content
    