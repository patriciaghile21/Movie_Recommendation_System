import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler
from .models import Profile, Genre
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect


# Session Types
def initialize_review_chain():
    auth_handler = AuthenticationHandler()
    email_handler = EmailVerificationHandler()
    rate_limit_handler = ReviewRateLimitingHandler()

    auth_handler.set_next(email_handler).set_next(rate_limit_handler)
    return auth_handler

REVIEW_CHAIN_START = initialize_review_chain()

@login_required
def post_review_api_view(request):
    if request.method != 'POST':
        return JsonResponse({'status' : 405, 'message' : "Method not allowed"}, status=405)

    result = REVIEW_CHAIN_START.handle(request)

    if result.get('status') == 200:
        try:
            data = json.loads(request.body)

            return JsonResponse({'status' : 201, 'message' : "Review Posted Successfully"}, status=201)
        except Exception as e:
            return JsonResponse({'status' : 400, 'message' : f"Something went wrong, error: {e} "}, status=400)
    else:
        return JsonResponse({'status' : result.get('status'), 'message' : result.get('message')}, status=result.get('status'))

# Login and Register
def show_message(request):
    return render(request, 'helloapp/register.html')
def registerPage(request):
    all_genres = Genre.objects.all()

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        birthdate = request.POST.get("birthdate")
        selected_genres_ids = request.POST.getlist("genres")

        if not username or not email or not password1 or not birthdate or not selected_genres_ids:
            messages.error(request, "All fields are required.")
            return render(request, 'helloapp/register.html', {'all_genres': all_genres})

        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return render(request, "helloapp/register.html", {'all_genres': all_genres})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'helloapp/register.html', {'all_genres': all_genres})

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        new_profile = Profile.objects.create(user=user, birthdate=birthdate)
        if selected_genres_ids:
            new_profile.genres.set(selected_genres_ids)

        return redirect("login")
    return render(request, 'helloapp/register.html', {'all_genres': all_genres})

def loginPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")

        user = authenticate(request, username=username, password=password1)

        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "helloapp/login.html")

    return render(request, "helloapp/login.html")

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("login")

def index(request):
    return render(request, 'helloapp/index.html')