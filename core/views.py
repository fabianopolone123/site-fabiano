from django.shortcuts import render
from .models import Produto  # importa produtos


def home(request):
    produtos = Produto.objects.all()  # pega todos produtos
    return render(request, "home.html", {"produtos": produtos})  # envia para o html


def carrinho(request):
    return render(request, "carrinho.html")
