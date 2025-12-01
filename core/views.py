from django.shortcuts import render
from .models import Produto, Usuario, Pedido, ItemPedido  # importa produtos
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from decimal import Decimal
from .mercadopago_client import MercadoPagoClient




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

        # SE FOR PIX À VISTA: já manda o cliente para a tela única do QRCode
    if pagamento == "pix":
        # external_reference será tratado lá na pix_qr
        redirect_url = f"/pix/?ref={pedido.id}"
        return JsonResponse({"ok": True, "pedido_id": pedido.id, "redirect_url": redirect_url})

    # se não for pix, fluxo normal
    return JsonResponse({"ok": True, "pedido_id": pedido.id})



def pagar(request):
    clientes = Usuario.objects.all().order_by("nome_completo")
    return render(request, "pagar.html", {"clientes": clientes})


@csrf_exempt
def pagar_listar(request):
    dados = json.loads(request.body)
    cliente_id = dados.get("cliente")

    # VALIDAÇÃO PARA EVITAR ERRO DE ID VAZIO
    if not cliente_id or str(cliente_id).strip() == "":
        return JsonResponse({"ok": False, "erro": "Nenhum cliente selecionado."})

    try:
        cliente_id = int(cliente_id)
    except:
        return JsonResponse({"ok": False, "erro": "ID inválido."})

    cliente = Usuario.objects.get(id=cliente_id)

    # pedidos em aberto (qualquer forma de pagamento exceto 'pago')
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


def pix_qr(request):
    """
    Página única do QRCode PIX.
    Recebe ?ref=35 ou ?ref=35,15,45,2
    """
    ref = request.GET.get("ref")
    if not ref:
        return HttpResponse("Referência não informada.", status=400)

    # lista de IDs de pedidos (1 ou vários)
    try:
        ids = [int(x) for x in ref.split(",") if x.strip()]
    except ValueError:
        return HttpResponse("Referência inválida.", status=400)

    pedidos = Pedido.objects.filter(id__in=ids)
    if not pedidos.exists():
        return HttpResponse("Pedidos não encontrados.", status=404)

    # soma total dos pedidos
    total = sum(p.total for p in pedidos)

    # external_reference = "35" ou "35,15,45,2"
    external_reference = ",".join(str(p.id) for p in pedidos)

    # salvar external_reference em todos os pedidos envolvidos (pra auditoria)
    pedidos.update(external_reference=external_reference)

    mp = MercadoPagoClient()
    try:
        pagamento = mp.criar_pagamento_pix(
            valor=total,
            external_reference=external_reference,
            descricao=f"Pagamento pedido(s): {external_reference}",
        )
    except Exception as e:
        return HttpResponse(f"Erro ao gerar PIX: {e}", status=500)

    contexto = {
        "total": total,
        "ref": external_reference,
        "qr_code": pagamento["qr_code"],
        "qr_code_base64": pagamento["qr_code_base64"],
        "payment_id": pagamento["id"],
    }
    return render(request, "pix.html", contexto)

def pix_status(request):
    """
    Consulta simples: verifica se todos os pedidos do external_reference já estão
    marcados como 'pago' (forma_pagamento='pago').
    """
    ref = request.GET.get("ref")
    if not ref:
        return JsonResponse({"ok": False, "erro": "ref não informado"})

    try:
        ids = [int(x) for x in ref.split(",") if x.strip()]
    except ValueError:
        return JsonResponse({"ok": False, "erro": "ref inválido"})

    pedidos = Pedido.objects.filter(id__in=ids)
    if not pedidos.exists():
        return JsonResponse({"ok": False, "erro": "pedidos não encontrados"})

    # se todos estiverem com forma_pagamento = "pago"
    todos_pagos = all(p.forma_pagamento == "pago" for p in pedidos)

    return JsonResponse({"ok": True, "pago": todos_pagos})

@csrf_exempt
def mp_webhook(request):
    """
    Webhook chamado pelo Mercado Pago.
    Configurar essa URL lá no painel do MP.
    Marca pedidos como pagos quando o pagamento é aprovado.
    """
    import requests

    # MP pode mandar o ID pela querystring ou no body
    payment_id = request.GET.get("id") or request.GET.get("data.id")
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}

    if not payment_id:
        payment_id = (
            body.get("data", {}).get("id")
            or body.get("id")
        )

    if not payment_id:
        return HttpResponse("no id", status=200)

    # busca detalhes do pagamento
    mp = MercadoPagoClient()
    url = f"{mp.base_url}/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {mp.token}"}
    resp = requests.get(url, headers=headers, timeout=20)
    data = resp.json()

    if resp.status_code not in (200, 201):
        return HttpResponse("error fetching payment", status=200)

    status = data.get("status")
    external_reference = data.get("external_reference", "")

    if status in ("approved", "credited") and external_reference:
        try:
            ids = [int(x) for x in external_reference.split(",") if x.strip()]
        except ValueError:
            ids = []

        if ids:
            # marca todos como pagos
            Pedido.objects.filter(id__in=ids).update(forma_pagamento="pago")

    return HttpResponse("ok", status=200)
