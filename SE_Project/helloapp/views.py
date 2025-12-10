from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

# Create your views here.

from django.shortcuts import render
from .models import Message

def show_message(request):
    return render(request, 'Authentication/auth.html')

def sign_up(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        print("Username:", username)
        print("Email:", email)
        print("Password1:", password1)
        print("Password2:", password2)

        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return render(request, "Authentication/auth.html")

        user = User.objects.create_user(username, email, password1)
        user.save();


        return redirect("/")
    return render(request, "Authentication/auth.html")


def index(request):
    return render(request, "Authentication/auth.html")