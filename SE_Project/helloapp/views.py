from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from .models import Message

def show_message(request):
    message = Message.objects.first()
    return render(request, 'helloapp/index.html', {'message' : message})

