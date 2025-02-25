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
    path("forums/", views.forum_home, name="forum_home"),
    path("forums/create_thread/", views.create_thread, name="create_thread"),
    path("forums/thread/<int:thread_id>/", views.thread_detail, name="thread_detail"),
    path("forums/thread/<int:thread_id>/add_post/", views.add_post, name="add_post"),   
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)