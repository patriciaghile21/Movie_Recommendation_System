from django.urls import path
from . import views

urlpatterns = [
    path('', views.registerPage, name = 'register'),
    path('login/', views.loginPage, name = 'login'),
    path('index/', views.index, name = 'index'),
    path('logout/', views.logout_view, name = 'logout'),
    path('select_genres/', views.select_genres, name = 'select_genres'),

    path("api/post-review/", views.post_review_api_view, name="post_review"),

]