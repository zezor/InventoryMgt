from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.contrib.auth.decorators import login_required
from .models import CustomUser

# Create your views here.
def login_view(request):
    form = CustomUser()
    return render(request, 'accounts/login.html', {'form': form})