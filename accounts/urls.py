from django.urls import path, include
from . import views

urlpatterns = [
    # Add your app-specific URL patterns here
    path('login/', views.login_view, name='login'),
]