from django.urls import path
from . import views

urlpatterns = [
    # Page Route
    path("", views.index, name="index"),

    # Auth Logic Routes
    path("signup/", views.sign_up, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # API Routes
    path("api/post-review/", views.post_review_api_view, name="post_review"),
]