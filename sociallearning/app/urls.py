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
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)