from django.contrib import admin
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('finalizar/', views.finalizar, name='finalizar'),
    path("salvar_cliente/", views.salvar_cliente, name="salvar_cliente"),
    path("criar_pedido/", views.criar_pedido, name="criar_pedido"),

    # === PIX / MERCADO PAGO ===
    path("pix/", views.pix_qr, name="pix_qr"),
    path("pix/status/", views.pix_status, name="pix_status"),
    path("mp_webhook/", views.mp_webhook, name="mp_webhook"),

    # pagar pedidos (se já não tiver)
    path("pagar/", views.pagar, name="pagar"),
    path("pagar_listar/", views.pagar_listar, name="pagar_listar"),

    path("painel/", views.painel_login, name="painel_login"),
    path("painel/entrar/", views.painel_entrar, name="painel_entrar"),
    path("painel/home/", views.painel_home, name="painel_home"),

    # ENVIO DE MENSAGEM PARA TODOS
    path("painel/msg_enviar/", views.painel_msg_enviar, name="painel_msg_enviar"),

    # COBRAR ATRASADOS
    path("painel/cobrar_enviar/", views.painel_cobrar_enviar, name="painel_cobrar_enviar"),

    path("painel/template/salvar/", views.salvar_template),
    path("painel/template/<int:id>/", views.carregar_template),


]


# aqui embaixo — sem sobrescrever! apenas adicionando
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
