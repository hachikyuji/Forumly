from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Welcome Page
    path('', views.user_login, name='login'),
    path('register', views.register, name='register'),
    
    # Homepage
    path('homepage', views.homepage, name='homepage'),
    path('logout', views.logoutView, name="logout"),
    
    # Account Settings
    path('profile/update', views.update_profile, name="update_profile"),
    
    #AboutUs
    path('about_us/', views.about_us, name="about_us"),
    
    # Forums
    path('forums/', views.ForumCategoryListView.as_view(), name='forum_categories'),
    path('forums/<int:category_id>/', views.ForumThreadListView.as_view(), name='forum_threads'),
    path('forums/<int:category_id>/new-thread/', views.ForumThreadCreateView.as_view(), name='new_forum_thread'),
    path('thread/<int:pk>/', views.ForumThreadDetailView.as_view(), name='forum_thread_detail'),
    path('thread/<int:thread_id>/reply/', views.ForumReplyCreateView.as_view(), name='forum_reply_create'),
    path('thread/<int:thread_id>/like/', views.LikeThreadView.as_view(), name='like_thread'),
    path('thread/<int:thread_id>/dislike/', views.DislikeThreadView.as_view(), name='dislike_thread'),
    
    # Tracking
    path('profile', views.UserProfileView.as_view(), name='profile'),
    path('likedislike', views.LikeDislikeStatsView.as_view(), name='likedislike'),
    path('track-time/', views.track_time_spent, name="track_time_spent"),
    
    #Test Q-learning
    path('test_recommendation/', views.test_recommendation, name='test_recommendation'),
    
    #Q-learning Data
    path('reset_QL/', views.reset_QL, name='reset_QL'),
    
    #Check Mentioned User
    path('check_user_exists/', views.check_user_exists, name="check_user_exists"),
    
    #Notifications
    path('notifications/', views.notifications, name="notifications"),
    path('notifications/read_all/', views.read_all_notifications, name='read_all_notifications'),
    path('notifications/clear/', views.clear_notifications, name='clear_notifications'),
    path('notifications/mark_read/', views.mark_notification_read, name='mark_notification_read'),
    
    #Superadmin
    path('user_data/', views.UserProfilesListView.as_view(), name='user-data'),
    path('restrict-user/<int:user_id>/', views.RestrictUserView.as_view(), name='restrict-user'),

]

#403 Forbidden Error
from django.conf.urls import handler403
from django.shortcuts import render

def custom_403_view(request, exception):
    return render(request, "403.html", status=403)

handler403 = custom_403_view  # Tells Django to use this view for 403 errors


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)