from django.shortcuts import render

# Create your views here.
def home(request):  # cria função home
    return render(request, "home.html")  # abre home.html