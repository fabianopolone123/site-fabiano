from django.shortcuts import render
from .models import Produto, Usuario, Pedido, ItemPedido  # importa produtos
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



def home(request):
    produtos = Produto.objects.all()  # pega todos produtos
    return render(request, "home.html", {"produtos": produtos})  # envia para o html


def carrinho(request):
    return render(request, "carrinho.html")


def finalizar(request):
    clientes = Usuario.objects.all().order_by("nome_completo")
    return render(request, "finalizar.html", {"clientes": clientes})


@csrf_exempt
def salvar_cliente(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido"})

    dados = json.loads(request.body)

    nome = dados.get("nome")
    whats = dados.get("whats")

    if not nome or not whats:
        return JsonResponse({"ok": False, "erro": "Dados incompletos"})

    # validar formato simples
    if not whats.isdigit():
        return JsonResponse({"ok": False, "erro": "WhatsApp inválido"})

    # salvar no banco
    u = Usuario(nome_completo=nome, whatsapp=whats)
    u.save()

    return JsonResponse({"ok": True, "id": u.id})



@csrf_exempt
def criar_pedido(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido"})

    dados = json.loads(request.body)

    cliente_id = dados.get("cliente")
    pagamento = dados.get("pagamento")   # "pix" | "6" | "20"
    itens = dados.get("itens")

    if not cliente_id or not pagamento or not itens:
        return JsonResponse({"ok": False, "erro": "Dados incompletos"})

    cliente = Usuario.objects.get(id=cliente_id)

    # Calcular total
    total = sum(item["preco"] * item["qtd"] for item in itens)

    # ================================
    # CALCULAR DATA DE COBRANÇA (6 / 20)
    # ================================
    from datetime import date

    hoje = date.today()
    data_cobranca = None

    if pagamento == "6":
        dia = 6
        mes = hoje.month
        ano = hoje.year

        if hoje.day >= dia:
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1

        data_cobranca = date(ano, mes, dia)

    elif pagamento == "20":
        dia = 20
        mes = hoje.month
        ano = hoje.year

        if hoje.day >= dia:
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1

        data_cobranca = date(ano, mes, dia)

    # ================================
    # CRIAR PEDIDO
    # ================================
    pedido = Pedido.objects.create(
        nome_cliente=cliente.nome_completo,
        whatsapp=cliente.whatsapp,
        forma_pagamento=pagamento,
        data_cobranca=data_cobranca,
        total=total
    )

    # Código único (para PIX futuro)
    pedido.external_reference = f"PEDIDO_{pedido.id}_{cliente.whatsapp}"
    pedido.save()

    # ================================
    # CRIAR ITENS & BAIXAR ESTOQUE
    # ================================
    for item in itens:
        produto = Produto.objects.get(nome=item["nome"])

        if produto.estoque < item["qtd"]:
            return JsonResponse({"ok": False, "erro": f"Sem estoque de {produto.nome}"})

        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=item["qtd"],
            preco_unitario=item["preco"],
        )

        produto.estoque -= item["qtd"]
        produto.save()

    return JsonResponse({"ok": True, "pedido_id": pedido.id})


def pagar(request):
    clientes = Usuario.objects.all().order_by("nome_completo")
    return render(request, "pagar.html", {"clientes": clientes})


@csrf_exempt
def pagar_listar(request):
    dados = json.loads(request.body)
    cliente_id = dados.get("cliente")

    cliente = Usuario.objects.get(id=cliente_id)

    # pedidos em aberto (status: pendente)
    pedidos = Pedido.objects.filter(
        nome_cliente=cliente.nome_completo
    ).exclude(forma_pagamento="pago")

    lista = []
    for p in pedidos:
        lista.append({
            "id": p.id,
            "data": p.data_pedido.strftime("%d/%m/%Y"),
            "total": float(p.total),
            "forma_pagamento": p.forma_pagamento
        })

    return JsonResponse({"ok": True, "pedidos": lista})


@csrf_exempt
def pagar_confirmar(request):
    dados = json.loads(request.body)
    ids = dados.get("pedidos")

    Pedido.objects.filter(id__in=ids).update(forma_pagamento="pago")

    return JsonResponse({"ok": True})
