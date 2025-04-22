from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.IntegerField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
    category_comment_count = models.JSONField(default=dict)
    category_like_count = models.JSONField(default=dict)
    category_dislike_count = models.JSONField(default=dict)
    admin = models.BooleanField(default=False)
    super_admin = models.BooleanField(default=False)
    
    # Deprecated
    interests = models.JSONField(default=list, null=True, blank=True)  # List of user interests
    historical_preferences = models.JSONField(default=list, null=True, blank=True)  # Previous topic preferences
    
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
    sentiment_score = models.FloatField(default=0)
    
    def __str__(self):
        return self.content

class ForumViewHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE)
    time_spent = models.IntegerField(default=0)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.time_spent}s"

class RecommendationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(ForumThread, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    
class RecommendedTopicHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    forum_thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE)
    recommended_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.forum_thread.title} - Viewed: {self.viewed}"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_thread_url(self):
        return reverse('forum_thread_detail', args=[self.thread.id]) if self.thread else "#"

