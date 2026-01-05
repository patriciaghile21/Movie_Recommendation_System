from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.registerPage, name='register'),
    path('select_genres/', views.select_genres, name='select_genres'),
    path('api/post_review/', views.post_review_api_view, name='post_review'),

    # 2FA Security URLs
    path('auth/wait/', views.check_login_status, name='check_status'),
    path('auth/yes/<uuid:token>/', views.approve_login_view, name='approve_login'),
    path('auth/no/<uuid:token>/', views.deny_login_view, name='deny_login'),
]