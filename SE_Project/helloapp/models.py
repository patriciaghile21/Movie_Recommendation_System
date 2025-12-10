
# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractUser


class Message(models.Model):
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text