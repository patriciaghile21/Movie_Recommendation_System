import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Assuming these are defined in your project
from .models import Message, Movie
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler


# --- AUTHENTICATION VIEWS ---

def index(request):
    """Simple view to render the combined Login/Signup page."""
    # Presupunem că auth.html a rămas în folderul Authentication
    return render(request, "Authentication/auth.html")


def sign_up(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # 1. Validation
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("index")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("index")

        # 2. Creation
        user = User.objects.create_user(username, email, password1)
        user.save()

        # 3. Auto-login after signup
        login(request, user)
        messages.success(request, f"Welcome, {username}! Account created.")

        # CORECT: Redirect către URL-ul cu name="main"
        return redirect("main")

    return redirect("index")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")

        user = authenticate(request, username=username, password=password1)

        if user is not None:
            login(request, user)
            # CORECT: Redirect către URL-ul cu name="main"
            return redirect("main")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("index")

    return redirect("index")


def logout_view(request):
    logout(request)
    return redirect("index")


# --- APPLICATION VIEWS ---

@login_required
def main_window(request):
    """Renders the main dashboard for genre selection."""
    # ACTUALIZAT: Caută în folderul mainpage
    return render(request, "mainpage/main.html")


@login_required
def user_profile(request):
    """Renders the user profile page."""
    # Mock data for friends
    mock_friends = [
        {'username': 'Cristina'},
        {'username': 'Andrei'},
        {'username': 'Dolha'},
    ]

    context = {
        'user': request.user,
        'friends': mock_friends
    }
    # ACTUALIZAT: Caută în folderul mainpage
    return render(request, "mainpage/profile.html", context)


@login_required
def recommendations(request):
    """Handles the recommendation logic."""
    if request.method == "POST":
        selected_genres = request.POST.getlist('genres')

        # Mock Movie Data
        mock_movies = [
            {'title': 'Inception', 'year': 2010, 'rating': 8.8, 'genres': 'Sci-Fi'},
            {'title': 'The Dark Knight', 'year': 2008, 'rating': 9.0, 'genres': 'Action'},
            {'title': 'Titanic', 'year': 1997, 'rating': 7.8, 'genres': 'Romance'},
        ]

        context = {
            'movies': mock_movies,
            'selected_genres': selected_genres
        }
        # ACTUALIZAT: Caută în folderul mainpage
        return render(request, "mainpage/recommendations.html", context)

    # Redirect dacă intră direct
    return redirect("main")


# --- REVIEW CHAIN LOGIC ---

def initialize_review_chain():
    """Initializes the Chain of Responsibility for reviews."""
    auth_handler = AuthenticationHandler()
    email_handler = EmailVerificationHandler()
    rate_limit_handler = ReviewRateLimitingHandler()

    # Link the handlers
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
            return JsonResponse({'status': 201, 'message': "Review Posted Successfully"}, status=201)
        except Exception as e:
            return JsonResponse({'status': 400, 'message': f"Error: {e}"}, status=400)
    else:
        return JsonResponse(
            {'status': result.get('status'), 'message': result.get('message')},
            status=result.get('status')
        )