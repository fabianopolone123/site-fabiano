from django.contrib import admin
from .models import Produto, Usuario, Pedido, ItemPedido

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    readonly_fields = ("data_pedido",)  # <-- mostra, mas não deixa editar

    list_display = (
        "id",
        "nome_cliente",
        "data_pedido",
        "forma_pagamento",
        "data_cobranca",
        "total",
    )

    list_filter = ("forma_pagamento", "data_pedido")
    search_fields = ("nome_cliente", "whatsapp")


admin.site.register(Produto)
admin.site.register(Usuario)
admin.site.register(ItemPedido)
