from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import *

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Profile)
admin.site.register(Review)
admin.site.register(Recommendation)