from django.urls import path
from . import views

urlpatterns = [

    path("", views.index, name="index"),
    path("signup/", views.sign_up, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("main/", views.main_window, name="main"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path('profile/', views.user_profile, name='user_profile'),
    path('add-friend/<int:friend_id>/', views.add_friend, name='add_friend'),
    path('remove-friend/<int:friend_id>/', views.remove_friend, name='remove_friend'),
    path('all-movies/', views.movie_library, name='movie_library'),
path('review/<int:movie_id>/', views.add_review_page, name='add_review'),

]