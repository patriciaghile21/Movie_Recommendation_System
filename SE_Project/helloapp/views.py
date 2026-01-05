import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

# Project imports
from .models import Message, Movie, Profile, Genre, LoginAttempt
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler


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
            data = json.loads(request.body)
            # Add logic to save review here if needed
            return JsonResponse({'status': 201, 'message': "Review Posted Successfully"}, status=201)
        except Exception as e:
            return JsonResponse({'status': 400, 'message': f"Error: {e}"}, status=400)
    else:
        return JsonResponse(
            {'status': result.get('status'), 'message': result.get('message')},
            status=result.get('status')
        )


# --- AUTHENTICATION & ONBOARDING ---

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

        # Log them in immediately after signup (Skipping 2FA for first registration)
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


# --- 2FA LOGIN LOGIC ---

def loginPage(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password1")

        # 1. Verify Password
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 2. Cleanup old attempts & Create new one
            LoginAttempt.objects.filter(user=user).delete()
            attempt = LoginAttempt.objects.create(user=user)

            # 3. Generate Links
            yes_link = request.build_absolute_uri(reverse('approve_login', args=[str(attempt.token)]))
            no_link = request.build_absolute_uri(reverse('deny_login', args=[str(attempt.token)]))

            # 4. Send Email
            email_body = f"""
            Hello {user.username},

            We noticed a login attempt. Is this you?

            [ YES - LOG ME IN ]
            {yes_link}

            [ NO - BLOCK THIS ]
            {no_link}
            """

            # Note: Ensure EMAIL_BACKEND is set in settings.py
            send_mail(
                "Security Check: Is this you?",
                email_body,
                settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                [user.email],
                fail_silently=False,
            )

            # 5. Store ID in session so the polling view knows who to check
            request.session['pending_2fa_user'] = user.id

            # 6. Show the "Waiting" screen
            return render(request, "helloapp/wait_for_email.html")

        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "helloapp/login.html")


def check_login_status(request):
    """Called by JS every few seconds to check if the user clicked YES."""
    user_id = request.session.get('pending_2fa_user')

    if not user_id:
        return JsonResponse({'status': 'error'})

    try:
        attempt = LoginAttempt.objects.get(user_id=user_id)

        if attempt.is_confirmed:
            # SUCCESS: Log the user in
            user = User.objects.get(id=user_id)
            login(request, user)

            # Cleanup
            attempt.delete()
            del request.session['pending_2fa_user']

            # Check onboarding status
            if hasattr(user, 'profile') and not user.profile.is_onboarded:
                return JsonResponse({'status': 'onboarding'})  # Special status for JS redirect

            return JsonResponse({'status': 'approved'})

    except LoginAttempt.DoesNotExist:
        # If the record is gone, it means they clicked NO (deleted)
        return JsonResponse({'status': 'denied'})

    return JsonResponse({'status': 'waiting'})


def approve_login_view(request, token):
    """Triggered when user clicks YES in the email."""
    attempt = get_object_or_404(LoginAttempt, token=token)

    if attempt.is_valid():
        attempt.is_confirmed = True
        attempt.save()
        return render(request, "helloapp/email_result.html", {"message": "Login Approved! You can close this tab."})
    else:
        return render(request, "helloapp/email_result.html", {"message": "Link expired."})


def deny_login_view(request, token):
    """Triggered when user clicks NO in the email."""
    attempt = get_object_or_404(LoginAttempt, token=token)
    attempt.delete()
    return render(request, "helloapp/email_result.html", {"message": "Login Blocked."})


# --- MAIN APP VIEWS ---

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