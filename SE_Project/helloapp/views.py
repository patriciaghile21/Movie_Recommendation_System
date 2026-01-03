import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler
from .models import Profile, Genre


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
        return JsonResponse({'status': 405, 'message': "Method not allowed"}, status=405)

    result = REVIEW_CHAIN_START.handle(request)

    if result.get('status') == 200:
        try:
            data = json.loads(request.body)
            return JsonResponse({'status': 201, 'message': "Review Posted Successfully"}, status=201)
        except Exception as e:
            return JsonResponse({'status': 400, 'message': f"Error: {e}"}, status=400)
    else:
        return JsonResponse({'status': result.get('status'), 'message': result.get('message')},
                            status=result.get('status'))


def registerPage(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        birthdate = request.POST.get("birthdate")

        if not username or not email or not password1 or not birthdate:
            messages.error(request, "All fields are required.")
            return render(request, 'helloapp/register.html')

        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return render(request, "helloapp/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'helloapp/register.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        Profile.objects.create(user=user, birthdate=birthdate)

        login(request, user)
        return redirect("select_genres")

    return render(request, 'helloapp/register.html')


@login_required
def select_genres(request):
    if request.user.profile.is_onboarded:
        return redirect("index")

    if request.method == "POST":
        selected_genres_ids = request.POST.getlist("genres")
        if not selected_genres_ids:
            messages.error(request, "Please select at least one genre.")
        else:
            profile = request.user.profile
            profile.genres.set(selected_genres_ids)
            profile.is_onboarded = True
            profile.save()
            return redirect("index")

    all_genres = Genre.objects.all()
    return render(request, 'helloapp/select_genres.html', {'all_genres': all_genres})


def loginPage(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        user = authenticate(request, username=username, password=password1)

        if user is not None:
            login(request, user)
            if not user.profile.is_onboarded:
                return redirect("select_genres")
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "helloapp/login.html")


@login_required
def index(request):
    if not request.user.profile.is_onboarded:
        return redirect("select_genres")
    return render(request, 'helloapp/index.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("login")

def error_404_view(request, exception):
    return render(request, 'helloapp/404.html', status=404)