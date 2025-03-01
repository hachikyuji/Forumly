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
    
    # Forums
    path('forums/', views.ForumCategoryListView.as_view(), name='forum_categories'),
    path('forums/<int:category_id>/', views.ForumThreadListView.as_view(), name='forum_threads'),
    path('forums/<int:category_id>/new-thread/', views.ForumThreadCreateView.as_view(), name='new_forum_thread'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)