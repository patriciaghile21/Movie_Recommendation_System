import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from .models import Message
from .handlers import AuthenticationHandler, EmailVerificationHandler, ReviewRateLimitingHandler
from .models import Movie

def show_message(request):
    message = Message.objects.first()
    return render(request, 'helloapp/index.html', {'message' : message})

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