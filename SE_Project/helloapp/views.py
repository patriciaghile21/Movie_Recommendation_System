import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Message, Movie, Profile, Review
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler

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

@login_required
def main_window(request):
    return render(request, "mainpage/main.html")

@login_required
def user_profile(request):
    try:
        my_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        from datetime import date
        my_profile = Profile.objects.create(user=request.user, birthdate=date(2000, 1, 1))

    friends = my_profile.friends.all()

    other_users = Profile.objects.exclude(user=request.user).exclude(id__in=friends.values_list('id', flat=True))

    context = {
        'user': request.user,
        'friends': friends,
        'other_users': other_users
    }
    return render(request, "mainpage/profile.html", context)

@login_required
def recommendations(request):
    if request.method == "POST":
        selected_genres = request.POST.getlist('genres')

        mock_movies = [
            {'title': 'Inception', 'year': 2010, 'rating': 8.8, 'genres': 'Sci-Fi'},
            {'title': 'The Dark Knight', 'year': 2008, 'rating': 9.0, 'genres': 'Action'},
            {'title': 'Titanic', 'year': 1997, 'rating': 7.8, 'genres': 'Romance'},
        ]

        context = {
            'movies': mock_movies,
            'selected_genres': selected_genres
        }
        return render(request, "mainpage/recommendations.html", context)

    return redirect("main")

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
            return JsonResponse({'status': 201, 'message': "Review Posted Successfully"}, status=201)
        except Exception as e:
            return JsonResponse({'status': 400, 'message': f"Error: {e}"}, status=400)
    else:
        return JsonResponse(
            {'status': result.get('status'), 'message': result.get('message')},
            status=result.get('status')
        )

@login_required
def add_friend(request, friend_id):
    my_profile = get_object_or_404(Profile, user=request.user)
    friend_profile = get_object_or_404(Profile, id=friend_id)

    my_profile.friends.add(friend_profile)
    return redirect("user_profile")

@login_required
def remove_friend(request, friend_id):
    my_profile = get_object_or_404(Profile, user=request.user)
    friend_profile = get_object_or_404(Profile, id=friend_id)

    my_profile.friends.remove(friend_profile)
    return redirect("user_profile")

@login_required
def add_review_page(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":
        rating = request.POST.get('rating')
        text_content = request.POST.get('text')

        Review.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={
                'rating': rating,
                'text': text_content
            }
        )

        return redirect('movie_library')

    return render(request, "mainpage/add_review.html", {'movie': movie})

@login_required
def movie_library(request):
    all_movies = Movie.objects.all()
    return render(request, "mainpage/movie_library.html", {'movies': all_movies})