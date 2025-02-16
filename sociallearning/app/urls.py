from django.urls import path
from . import views 

urlpatterns = [
    # Welcome Page
    path('', views.user_login, name='login'),
    path('register', views.register, name='register'),
    path('homepage', views.homepage, name='homepage'),
]