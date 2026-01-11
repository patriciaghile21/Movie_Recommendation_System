from django.urls import path
from . import views

urlpatterns = [
    path("", views.main_window, name="mainn"),
    # Authentification
    path('register/', views.registerPage, name='register'),
    path('select_genres/', views.select_genres, name='select_genres'),
    path("login/", views.loginPage, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('auth/wait/', views.check_login_status, name='check_status'),
    path('auth/yes/<uuid:token>/', views.approve_login_view, name='approve_login'),
    path('auth/no/<uuid:token>/', views.deny_login_view, name='deny_login'),

    # Main Page
    path("main/", views.main_window, name="main"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path('profile/', views.user_profile, name='user_profile'),
    path('add-friend/<int:friend_id>/', views.add_friend, name='add_friend'),
    path('remove-friend/<int:friend_id>/', views.remove_friend, name='remove_friend'),
    path('all-movies/', views.movie_library, name='movie_library'),
    path('review/<int:movie_id>/', views.add_review_page, name='add_review'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
]