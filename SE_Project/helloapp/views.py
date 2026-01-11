from django.db.models import Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

from .models import Movie, Profile, Genre, LoginAttempt, Review
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler
from .patterns import RecommendationEngine
from .protocols import SessionProtocol, SessionState


# --- INITIALIZATION ---

def initialize_review_chain():
    auth_handler = AuthenticationHandler()
    email_handler = EmailVerificationHandler()
    rate_limit_handler = ReviewRateLimitingHandler()
    auth_handler.set_next(email_handler).set_next(rate_limit_handler)
    return auth_handler


REVIEW_CHAIN_START = initialize_review_chain()


# --- AUTHENTICATION & REGISTRATION ---

def registerPage(request):
    protocol = SessionProtocol(request)
    if request.user.is_authenticated and protocol.is_at(SessionState.AUTHENTICATED):
        return redirect("main")

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

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")  # Schimbat din select_genres -> login

    return render(request, 'helloapp/register.html')


def loginPage(request):
    protocol = SessionProtocol(request)
    if request.user.is_authenticated and protocol.is_at(SessionState.AUTHENTICATED):
        return redirect("main")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password1")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            LoginAttempt.objects.filter(user=user).delete()
            attempt = LoginAttempt.objects.create(user=user)

            yes_link = request.build_absolute_uri(reverse('approve_login', args=[str(attempt.token)]))
            no_link = request.build_absolute_uri(reverse('deny_login', args=[str(attempt.token)]))

            text_content = f"Hello {user.username}, Is this you?\nYES: {yes_link}\nNO: {no_link}"
            html_content = f"""
                <div style="font-family: sans-serif; background-color: #fce4ec; padding: 20px; border-radius: 15px;">
                    <h2>Movie Night Security 🍿</h2>
                    <p>Was this you, <strong>{user.username}</strong>?</p>
                    <a href="{yes_link}">YES, IT'S ME</a> | <a href="{no_link}">NO</a>
                </div>"""

            send_mail(
                subject="Security Check",
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content
            )

            request.session['pending_2fa_user'] = user.id
            protocol.transition_to(SessionState.AWAITING_2FA)
            return render(request, "helloapp/wait_for_email.html")
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, "helloapp/login.html")


# --- ONBOARDING & 2FA ---

@login_required
def select_genres(request):
    protocol = SessionProtocol(request)
    # Permitem accesul DOAR dacă este în starea de onboarding
    if not protocol.is_at(SessionState.AWAITING_ONBOARDING):
        return redirect("main")

    if request.method == "POST":
        selected_genres_ids = request.POST.getlist("genres")
        if not selected_genres_ids:
            messages.error(request, "Please select at least one genre.")
        else:
            profile = request.user.profile
            profile.genres.set(selected_genres_ids)
            profile.is_onboarded = True
            profile.save()
            protocol.transition_to(SessionState.AUTHENTICATED)
            return redirect("main")

    all_genres = Genre.objects.all()
    return render(request, 'helloapp/select_genres.html', {'all_genres': all_genres})


def check_login_status(request):
    protocol = SessionProtocol(request)
    user_id = request.session.get('pending_2fa_user')
    if not user_id: return JsonResponse({'status': 'error'})

    try:
        attempt = LoginAttempt.objects.get(user_id=user_id)
        if attempt.is_confirmed:
            user = User.objects.get(id=user_id)
            login(request, user)
            attempt.delete()
            del request.session['pending_2fa_user']

            if hasattr(user, 'profile') and not user.profile.is_onboarded:
                protocol.transition_to(SessionState.AWAITING_ONBOARDING)
                return JsonResponse({'status': 'onboarding'})

            protocol.transition_to(SessionState.AUTHENTICATED)
            return JsonResponse({'status': 'approved'})
    except LoginAttempt.DoesNotExist:
        return JsonResponse({'status': 'denied'})
    return JsonResponse({'status': 'waiting'})


def approve_login_view(request, token):
    attempt = get_object_or_404(LoginAttempt, token=token)
    if request.method == "POST":
        if attempt.is_valid():
            attempt.is_confirmed = True
            attempt.save()
            return render(request, "helloapp/email_result.html", {"message": "Approved!"})
    return render(request, "helloapp/approve_login.html", {'token': token})


def deny_login_view(request, token):
    attempt = get_object_or_404(LoginAttempt, token=token)
    attempt.delete()
    return render(request, "helloapp/email_result.html", {"message": "Blocked."})

# --- MAIN PAGE & LIBRARY ---

@login_required
def main_window(request):
    protocol = SessionProtocol(request)
    if protocol.is_at(SessionState.AWAITING_ONBOARDING):
        return redirect("select_genres")
    if not protocol.is_at(SessionState.AUTHENTICATED):
        return redirect("login")

    return render(request, "mainpage/main.html")


@login_required
def movie_library(request):
    protocol = SessionProtocol(request)
    if not protocol.is_at(SessionState.AUTHENTICATED):
        return redirect("main")

    query = request.GET.get('search', '')

    movies = Movie.objects.exclude(review__user=request.user).annotate(
        avg_rating=Avg('review__rating')
    )

    if query:
        movies = movies.filter(name__icontains=query)

    engine = RecommendationEngine()
    profile = request.user.profile

    safe_movies = [
        movie for movie in movies
        if not engine.check_movie(request.user, movie, profile)
    ]

    return render(request, "mainpage/movie_library.html", {
        'movies': safe_movies,
        'search_query': query
    })


# --- USER SOCIAL & REVIEWS ---

@login_required
def user_profile(request):
    protocol = SessionProtocol(request)
    if not protocol.is_at(SessionState.AUTHENTICATED):
        return redirect("main")

    try:
        my_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        from datetime import date
        my_profile = Profile.objects.create(user=request.user, birthdate=date(2000, 1, 1))

    friends = my_profile.friends.all()
    other_users = Profile.objects.exclude(user=request.user).exclude(id__in=friends.values_list('id', flat=True))

    return render(request, "mainpage/profile.html", {
        'user': request.user, 'friends': friends, 'other_users': other_users
    })

@login_required
def add_friend(request, friend_id):
    protocol = SessionProtocol(request)
    if not protocol.is_at(SessionState.AUTHENTICATED): return redirect("main")

    my_profile = get_object_or_404(Profile, user=request.user)
    friend_profile = get_object_or_404(Profile, id=friend_id)
    my_profile.friends.add(friend_profile)
    friend_profile.friends.add(my_profile)
    return redirect("user_profile")


@login_required
def remove_friend(request, friend_id):
    protocol = SessionProtocol(request)
    if not protocol.is_at(SessionState.AUTHENTICATED): return redirect("main")

    my_profile = get_object_or_404(Profile, user=request.user)
    friend_profile = get_object_or_404(Profile, id=friend_id)
    my_profile.friends.remove(friend_profile)
    return redirect("user_profile")


@login_required
def add_review_page(request, movie_id):
    protocol = SessionProtocol(request)
    if not protocol.is_at(SessionState.AUTHENTICATED): return redirect("main")

    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == "POST":
        Review.objects.update_or_create(
            user=request.user, movie=movie,
            defaults={'rating': request.POST.get('rating'), 'text': request.POST.get('text')}
        )
        return redirect('movie_library')
    return render(request, "mainpage/add_review.html", {'movie': movie})


@login_required
def post_review_api_view(request):
    protocol = SessionProtocol(request)
    if request.method != 'POST':
        return JsonResponse({'status': 405, 'message': "Method not allowed"}, status=405)
    if not protocol.is_at(SessionState.AUTHENTICATED):
        return JsonResponse({'status': 403, 'message': "Protocol Error"}, status=403)

    result = REVIEW_CHAIN_START.handle(request)
    if result.get('status') == 200:
        return JsonResponse({'status': 201, 'message': "Review Posted Successfully"}, status=201)
    return JsonResponse({'status': result.get('status'), 'message': result.get('message')}, status=result.get('status'))


# --- MOVIE DETAILS & RECS ---

@login_required
def movie_detail(request, movie_id):
    protocol = SessionProtocol(request)
    if not protocol.is_at(SessionState.AUTHENTICATED): return redirect("main")

    movie = get_object_or_404(Movie, id=movie_id)
    avg_rating = Review.objects.filter(movie=movie).aggregate(Avg('rating'))['rating__avg']
    return render(request, "mainpage/movie_detail.html", {'movie': movie, 'avg_rating': avg_rating})


@login_required
def recommendations(request):
    protocol = SessionProtocol(request)
    if not protocol.is_at(SessionState.AUTHENTICATED): return redirect("main")

    if request.method == "POST":
        selected_genres = request.POST.getlist('genres')

        # Limit to first 5 movies from DB as requested
        candidate_movies = Movie.objects.all()[:5]

        engine = RecommendationEngine()
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            # Fallback if profile missing
            return redirect("index")

        safe_movies_data = []

        for movie in candidate_movies:
            errors = engine.check_movie(request.user, movie, profile)

            if not errors:
                avg_rating = Review.objects.filter(movie=movie).aggregate(Avg('rating'))['rating__avg']
                if avg_rating is None:
                    avg_rating = 0.0

                genres_str = ", ".join([g.name for g in movie.genres.all()])

                movie_data = {
                    'title': movie.name,
                    'year': movie.releaseDate.year,
                    'rating': round(avg_rating, 1),
                    'genres': genres_str
                }
                safe_movies_data.append(movie_data)

        context = {
            'movies': safe_movies_data,
            'selected_genres': selected_genres
        }
        return render(request, "mainpage/recommendations.html", context)

    return redirect("main")


# --- SYSTEM VIEWS ---

def logout_view(request):
    request.session['protocol_state'] = SessionState.ANONYMOUS.name
    logout(request)
    return redirect("login")


def error_404_view(request, exception):
    return render(request, 'helloapp/404.html', status=404)