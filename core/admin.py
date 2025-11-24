from django.contrib import admin
from .models import Produto, Usuario

admin.site.register(Produto)   # produtos no admin
admin.site.register(Usuario)   # usuários simples no admin
