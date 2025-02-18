from django.urls import path
from . import views 

urlpatterns = [
    # Welcome Page
    path('', views.user_login, name='login'),
    path('register', views.register, name='register'),
    
    # Homepage
    path('homepage', views.homepage, name='homepage'),
    path('logout', views.logoutView, name="logout")
]