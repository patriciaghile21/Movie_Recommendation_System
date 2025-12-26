from abc import ABC, abstractmethod
from django.contrib.auth.models import User
from django.db.models import Count
from datetime import datetime, timedelta
from .models import Profile, Review

class ReviewRequestHandler(ABC):
    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def handler(self, request):
        pass

class AbstractHandler(ReviewRequestHandler):
    next_handler = None

    def set_next(self, handler):
        self.next_handler = handler
        return handler

    def handle(self, request):
        if self.next_handler:
            return self.next_handler(request)
        return {"status": 200, "message": "OK"}


class AuthenticationHandler(AbstractHandler):

    def handler(self, request):
        user = request.user

        if not user.is_authenticated:
            return {"status": 401, "message": "Unauthorized"}

        print("Authorized")
        request.session['authenticated_user'] = user
        return super().handle(request)

class EmailVerificationHandler(AbstractHandler):

    def handler(self, request):
        user = request.session.get('authenticated_user')

        try:
            profile = user.profile
            if not profile.is_email_verified():
                return {"status": 403, "message": "Please verify your email address"}
        except Profile.DoesNotExist:
            return {"status": 500, "message": "User profile not found"}

        print("Email Verified")
        return super().handle(request)

class ReviewRateLimitingHandler(AbstractHandler):
    MAX_REVIEWS_PER_USER_PER_HOUR = 5

    def handler(self, request):
        user = request.session.get('authenticated_user')

        one_hour_ago = datetime.now() - timedelta(hours=1)

        recent_count = Review.objects.filter(
            user=user,
            date_posted__gte=one_hour_ago,
        ).count()

        if recent_count >= self.MAX_REVIEWS_PER_USER_PER_HOUR:
            return {"status": 429, "message": "You have reached the maximum number of reviews per hour."}

        return super().handle(request)
