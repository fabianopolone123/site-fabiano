from django.db import models
from django.contrib.auth.models import User  # importa user normal
import re  # regex
class Produto(models.Model):
    nome = models.CharField(max_length=100)  # nome do produto
    preco = models.DecimalField(max_digits=8, decimal_places=2)  # preço
    estoque = models.IntegerField(default=0)  # quantidade em estoque
    imagem = models.ImageField(upload_to='produtos/')  # upload imagem

    def __str__(self):
        return self.nome  # mostra nome no admin

def validar_whatsapp(numero):
    numero = re.sub(r'\D', '', numero)  # remove tudo que não é número

    # se vier só 9 dígitos: ex 988208134 → inválido (não tem DDD)
    if len(numero) == 9:
        raise ValueError("Número incompleto (faltou DDD).")

    # se vier 11 dígitos: DDD + número → adiciona +55
    if len(numero) == 11:
        return "55" + numero

    # se vier 13 dígitos: formato internacional correto
    if len(numero) == 13:
        return numero

    raise ValueError("Número de WhatsApp inválido")

class Usuario(models.Model):
    nome_completo = models.CharField(max_length=150)  # nome
    whatsapp = models.CharField(max_length=20)        # telefone limpo

    def save(self, *args, **kwargs):
        self.whatsapp = validar_whatsapp(self.whatsapp)  # valida antes de salvar
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome_completo  # mostra nome no admin
    


class Pedido(models.Model):
    nome_cliente = models.CharField(max_length=150)     # nome da pessoa
    whatsapp = models.CharField(max_length=20)          # telefone validado
    data = models.DateTimeField(auto_now_add=True)      # data do pedido
    total = models.DecimalField(max_digits=10, decimal_places=2)  # total geral

    def __str__(self):
        return f"Pedido #{self.id} - {self.nome_cliente}"
        


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)   # relação
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT) # produto
    quantidade = models.IntegerField()                             # qtd
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2)  # preço no momento

    def subtotal(self):
        return self.quantidade * self.preco_unitario

