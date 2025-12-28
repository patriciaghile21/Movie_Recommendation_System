from django.urls import path
from . import views

urlpatterns = [
    # --- Authentication Routes ---
    path("", views.index, name="index"),
    path("signup/", views.sign_up, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # --- Application Routes ---
    path("main/", views.main_window, name="main"),                   # Pagina cu genurile
    path("recommendations/", views.recommendations, name="recommendations"), # Rezultatele
    path("profile/", views.user_profile, name="profile"),            # Profilul userului
]