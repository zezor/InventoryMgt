from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import CustomUser



User = get_user_model()

# Create your views here.
def login_view(request):
    form = get_user_model()  # Assuming you have a form for login
    
    return render(request, 'accounts/login.html', {'form': form})