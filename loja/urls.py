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
    path("pagar/", views.pagar, name="pagar"),
    path("pagar_listar/", views.pagar_listar, name="pagar_listar"),
    path("pagar_confirmar/", views.pagar_confirmar, name="pagar_confirmar"),



]

# aqui embaixo — sem sobrescrever! apenas adicionando
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
