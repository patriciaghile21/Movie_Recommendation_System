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
        return redirect("index")

    return redirect("index")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")

        user = authenticate(request, username=username, password=password1)

        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("index")

    return redirect("index")


def logout_view(request):
    logout(request)
    return redirect("index")


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

    # Pass the request through the chain
    result = REVIEW_CHAIN_START.handle(request)

    # If the chain returns a successful status
    if result.get('status') == 200:
        try:
            # data = json.loads(request.body)
            # Logic to save the review to the database would go here
            return JsonResponse({'status': 201, 'message': "Review Posted Successfully"}, status=201)
        except Exception as e:
            return JsonResponse({'status': 400, 'message': f"Error: {e}"}, status=400)
    else:
        # Return the specific error from the handler that failed (Auth, Email, or Rate Limit)
        return JsonResponse(
            {'status': result.get('status'), 'message': result.get('message')},
            status=result.get('status')
        )