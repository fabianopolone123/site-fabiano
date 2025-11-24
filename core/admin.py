from django.contrib import admin
from .models import Produto, Usuario, Pedido, ItemPedido


admin.site.register(Produto)   # produtos no admin
admin.site.register(Usuario)   # usuários simples no admin
admin.site.register(Pedido)
admin.site.register(ItemPedido)