from django.urls import path, include
from . import views

urlpatterns = [
    # Add your app-specific URL patterns here
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]