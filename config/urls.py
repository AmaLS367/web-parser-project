#config/urls.py
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse("Главная страница работает!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),  # Главная страница
]

