import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .models import Message, Movie, Profile
from .patterns import RecommendationEngine, KFrameworkBridge
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler

# --- AUTHENTICATION VIEWS ---

def index(request):
    return render(request, "Authentication/auth.html")


def sign_up(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("index")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("index")

        user = User.objects.create_user(username, email, password1)
        user.save()

        # Auto-create profile with default birthdate (can be updated later)
        from datetime import date
        Profile.objects.create(user=user, birthdate=date(2000, 1, 1))

        login(request, user)
        messages.success(request, f"Welcome, {username}! Account created.")
        return redirect("main")

    return redirect("index")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")

        user = authenticate(request, username=username, password=password1)

        if user is not None:
            login(request, user)
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
    return render(request, "mainpage/main.html")


@login_required
def user_profile(request):
    mock_friends = [
        {'username': 'Cristina'},
        {'username': 'Andrei'},
        {'username': 'Dolha'},
    ]

    context = {
        'user': request.user,
        'friends': mock_friends
    }
    return render(request, "mainpage/profile.html", context)


@login_required
def recommendations(request):
    if request.method == "POST":
        selected_genres = request.POST.getlist('genres')

        # SWITCH: True = K Framework (Strict/Slow), False = Visitor Pattern (Fast)
        USE_STRICT_K_MODE = True

        if selected_genres:
            candidate_movies = Movie.objects.filter(genres__name__in=selected_genres).distinct()
        else:
            candidate_movies = Movie.objects.all()

        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            from datetime import date
            profile = Profile.objects.create(user=request.user, birthdate=date(2000, 1, 1))

        # Select Verification Engine
        if USE_STRICT_K_MODE:
            print("🔴 MODE: STRICT K-FRAMEWORK (Running krun for each movie...)")
            engine = KFrameworkBridge()
        else:
            print("🟢 MODE: PYTHON VISITOR PATTERN (Fast check)")
            engine = RecommendationEngine()

        valid_movies = []

        for movie in candidate_movies:
            errors = engine.check_movie(request.user, movie, profile)

            if not errors:
                valid_movies.append(movie)
            else:
                print(f"BLOCKED ({'K' if USE_STRICT_K_MODE else 'Visitor'}): {movie.name} -> {errors}")

        context = {
            'movies': valid_movies,
            'selected_genres': selected_genres,
            'is_k_mode': USE_STRICT_K_MODE
        }
        return render(request, "mainpage/recommendations.html", context)

    return redirect("main")


# --- REVIEW CHAIN LOGIC ---

def initialize_review_chain():
    """Initializes the Chain of Responsibility for reviews."""
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
            return JsonResponse({'status': 201, 'message': "Review Posted Successfully"}, status=201)
        except Exception as e:
            return JsonResponse({'status': 400, 'message': f"Error: {e}"}, status=400)
    else:
        return JsonResponse(
            {'status': result.get('status'), 'message': result.get('message')},
            status=result.get('status')
        )