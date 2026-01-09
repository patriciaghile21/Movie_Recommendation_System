import uuid

from django.db import models
from django.utils import timezone

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

class Genre(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthdate = models.DateField()
    genres = models.ManyToManyField(Genre, blank=True)
    is_onboarded = models.BooleanField(default=False)

    friends = models.ManyToManyField("self", blank=True, symmetrical=False)

    def __str__(self):
        return self.user.username

class Movie(models.Model):
    name = models.CharField(max_length=200)
    releaseDate = models.DateField()
    genres = models.ManyToManyField(Genre)
    duration_minutes = models.IntegerField(default=0)
    director = models.CharField(max_length=200)
    studio = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    text = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return "Review from " + self.user.username + " for " + self.movie.name


class LoginAttempt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)

    def is_valid(self):
        return (timezone.now() - self.created_at).total_seconds() < 300