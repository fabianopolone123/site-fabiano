from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Produto, Usuario, Pedido, ItemPedido, TemplateMensagem
from .mercadopago_client import MercadoPagoClient

import json
import requests
from decimal import Decimal
from datetime import date

import time


# ===========================================================
# ====================== PÁGINAS PRINCIPAIS =================
# ===========================================================

def home(request):
    produtos = Produto.objects.all()
    return render(request, "home.html", {"produtos": produtos})


def carrinho(request):
    return render(request, "carrinho.html")


def finalizar(request):
    clientes = Usuario.objects.all().order_by("nome_completo")
    return render(request, "finalizar.html", {"clientes": clientes})


# ===========================================================
# ====================== CLIENTE NOVO =======================
# ===========================================================

@csrf_exempt
def salvar_cliente(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido"})

    dados = json.loads(request.body)
    nome = dados.get("nome")
    whats = dados.get("whats")

    if not nome or not whats:
        return JsonResponse({"ok": False, "erro": "Dados incompletos"})

    if not whats.isdigit():
        return JsonResponse({"ok": False, "erro": "WhatsApp inválido"})

    u = Usuario(nome_completo=nome, whatsapp=whats)
    u.save()

    return JsonResponse({"ok": True, "id": u.id})


def montar_msg_cliente(pedido, itens):
    lista_itens = ""
    for item in itens:
        lista_itens += f"• {item['nome']} x{item['qtd']}\n"

    msg = (
        f"🧊 *Seu pedido foi confirmado!*\n\n"
        f"🛍 *Itens do pedido:*\n"
        f"{lista_itens}\n"
        f"💰 *Total:* R$ {pedido.total}\n"
    )

    if pedido.forma_pagamento == "pix":
        msg += "💳 *Forma de pagamento:* PIX à vista\n"
    elif pedido.forma_pagamento == "6":
        msg += "💳 *Pagamento agendado para o dia 6*\n"
    elif pedido.forma_pagamento == "20":
        msg += "💳 *Pagamento agendado para o dia 20*\n"

    if pedido.data_cobranca:
        msg += f"📅 *Data do pagamento:* {pedido.data_cobranca.strftime('%d/%m/%Y')}\n"

    msg += (
        "\n🤝 Muito obrigado!\n"
        "Qualquer dúvida estou à disposição 😊"
    )

    return msg


def montar_msg_admin(pedido, itens):
    lista_itens = ""
    for item in itens:
        lista_itens += f"- {item['nome']} x{item['qtd']} (R$ {item['preco']})\n"

    msg = (
        f"📢 *NOVO PEDIDO RECEBIDO*\n\n"
        f"🧾 *Pedido ID:* {pedido.id}\n"
        f"👤 *Cliente:* {pedido.nome_cliente}\n"
        f"📞 *Whats:* {pedido.whatsapp}\n"
        f"💰 *Total:* R$ {pedido.total}\n"
        f"💳 *Forma de pagamento:* {pedido.forma_pagamento}\n"
    )

    if pedido.data_cobranca:
        msg += f"📅 *Data programada:* {pedido.data_cobranca.strftime('%d/%m/%Y')}\n"

    msg += (
        f"\n🛍 *Itens do pedido:*\n"
        f"{lista_itens}"
        "\n⚙️ Enviado automaticamente pelo sistema."
    )

    return msg

# ===========================================================
# ====================== CRIAR PEDIDO =======================
# ===========================================================

@csrf_exempt
def criar_pedido(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido"})

    dados = json.loads(request.body)

    # ==========================================================
    # 🔥 BLOQUEIO CONTRA CLIQUE DUPLO / REQUISIÇÃO DUPLICADA
    # ==========================================================
    token = dados.get("token")

    if not token:
        return JsonResponse({"ok": False, "erro": "Token ausente"})

    ultimo_token = request.session.get("ultimo_pedido_token")

    if ultimo_token == token:
        return JsonResponse({"ok": False, "erro": "Pedido já foi processado."})

    request.session["ultimo_pedido_token"] = token
    # ==========================================================

    cliente_id = dados.get("cliente")
    pagamento = dados.get("pagamento")
    itens = dados.get("itens")

    if not cliente_id or not pagamento or not itens:
        return JsonResponse({"ok": False, "erro": "Dados incompletos"})

    cliente = Usuario.objects.get(id=cliente_id)

    # Calcular total
    total = sum(item["preco"] * item["qtd"] for item in itens)

    hoje = date.today()
    data_cobranca = None

    if pagamento in ("6", "20"):
        dia = 6 if pagamento == "6" else 20
        mes = hoje.month
        ano = hoje.year

        if hoje.day >= dia:
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1

        data_cobranca = date(ano, mes, dia)

    # Criar pedido
    pedido = Pedido.objects.create(
        nome_cliente=cliente.nome_completo,
        whatsapp=cliente.whatsapp,
        forma_pagamento=pagamento,
        data_cobranca=data_cobranca,
        total=total
    )

    pedido.external_reference = f"PEDIDO_{pedido.id}_{cliente.whatsapp}"
    pedido.save()

    # Criar itens
    for item in itens:
        produto = Produto.objects.get(nome=item["nome"])

        if produto.estoque < item["qtd"]:
            return JsonResponse({"ok": False, "erro": f"Sem estoque de {produto.nome}"})

        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=item["qtd"],
            preco_unitario=item["preco"]
        )

        produto.estoque -= item["qtd"]
        produto.save()

    # Enviar mensagens
    msg_cliente = montar_msg_cliente(pedido, itens)
    enviar_whatsapp(pedido.whatsapp, msg_cliente)

    msg_admin = montar_msg_admin(pedido, itens)
    enviar_whatsapp("5514988208134", msg_admin)

    # PIX → Redireciona
    if pagamento == "pix":
        redirect_url = f"/pix/?ref={pedido.id}"
        return JsonResponse({"ok": True, "pedido_id": pedido.id, "redirect_url": redirect_url})

    return JsonResponse({"ok": True, "pedido_id": pedido.id})


# ===========================================================
# ========================== PAGAR ==========================
# ===========================================================

def pagar(request):
    clientes = Usuario.objects.all().order_by("nome_completo")
    return render(request, "pagar.html", {"clientes": clientes})


@csrf_exempt
def pagar_listar(request):
    dados = json.loads(request.body)
    cliente_id = dados.get("cliente")

    if not cliente_id or str(cliente_id).strip() == "":
        return JsonResponse({"ok": False, "erro": "Nenhum cliente selecionado."})

    try:
        cliente_id = int(cliente_id)
    except:
        return JsonResponse({"ok": False, "erro": "ID inválido."})

    cliente = Usuario.objects.get(id=cliente_id)

    pedidos = Pedido.objects.filter(nome_cliente=cliente.nome_completo).exclude(forma_pagamento="pago")

    lista = []

    for p in pedidos:
        itens = ItemPedido.objects.filter(pedido=p)

        lista.append({
            "id": p.id,
            "data_pedido": p.data_pedido.strftime("%d/%m/%Y"),
            "data_cobranca": p.data_cobranca.strftime("%d/%m/%Y") if p.data_cobranca else "--",
            "total": float(p.total),
            "itens": [f"{i.produto.nome} x{i.quantidade}" for i in itens]
        })


    return JsonResponse({"ok": True, "pedidos": lista})


@csrf_exempt
def pagar_confirmar(request):
    dados = json.loads(request.body)
    ids = dados.get("pedidos")
    Pedido.objects.filter(id__in=ids).update(forma_pagamento="pago")
    return JsonResponse({"ok": True})


# ===========================================================
# ========================== PIX ============================
# ===========================================================

def pix_qr(request):
    ref = request.GET.get("ref")
    if not ref:
        return HttpResponse("Referência não informada.", status=400)

    try:
        ids = [int(x) for x in ref.split(",") if x.strip()]
    except:
        return HttpResponse("Referência inválida.", status=400)

    pedidos = Pedido.objects.filter(id__in=ids)
    if not pedidos.exists():
        return HttpResponse("Pedidos não encontrados.", status=404)

    total = sum(p.total for p in pedidos)
    external_reference = ",".join(str(p.id) for p in pedidos)

    pedidos.update(external_reference=external_reference)

    mp = MercadoPagoClient()
    pagamento = mp.criar_pagamento_pix(
        valor=total,
        external_reference=external_reference,
        descricao=f"Pagamento pedido(s): {external_reference}"
    )

    contexto = {
        "total": total,
        "ref": external_reference,
        "qr_code": pagamento["qr_code"],
        "qr_code_base64": pagamento["qr_code_base64"],
        "payment_id": pagamento["id"],
    }
    return render(request, "pix.html", contexto)


def pix_status(request):
    ref = request.GET.get("ref")
    if not ref:
        return JsonResponse({"ok": False, "erro": "ref não informado"})

    try:
        ids = [int(x) for x in ref.split(",") if x.strip()]
    except:
        return JsonResponse({"ok": False, "erro": "ref inválido"})

    pedidos = Pedido.objects.filter(id__in=ids)

    todos_pagos = all(p.forma_pagamento == "pago" for p in pedidos)

    return JsonResponse({"ok": True, "pago": todos_pagos})


@csrf_exempt
def mp_webhook(request):
    payment_id = request.GET.get("id") or request.GET.get("data.id")

    try:
        body = json.loads(request.body or "{}")
    except:
        body = {}

    if not payment_id:
        payment_id = body.get("data", {}).get("id") or body.get("id")

    if not payment_id:
        return HttpResponse("no id", status=200)

    mp = MercadoPagoClient()
    url = f"{mp.base_url}/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {mp.token}"}

    resp = requests.get(url, headers=headers)
    data = resp.json()

    status = data.get("status")
    external_reference = data.get("external_reference", "")

    if status in ("approved", "credited") and external_reference:
        try:
            ids = [int(x) for x in external_reference.split(",") if x.strip()]
        except:
            ids = []

        Pedido.objects.filter(id__in=ids).update(forma_pagamento="pago")

    return HttpResponse("ok", status=200)


# ===========================================================
# ====================== PAINEL ADMIN =======================
# ===========================================================

PAINEL_SENHA = "12345"


def painel_login(request):
    return render(request, "painel_login.html")


def painel_entrar(request):
    senha = request.POST.get("senha")

    if senha == PAINEL_SENHA:
        request.session["painel_logado"] = True
        return redirect("/painel/home/")

    return render(request, "painel_login.html", {"erro": "Senha incorreta!"})


def painel_home(request):
    if not request.session.get("painel_logado"):
        return redirect("/painel/")

    pedidos = Pedido.objects.all().order_by("-id")
    pendentes = Pedido.objects.exclude(forma_pagamento="pago")
    templates = TemplateMensagem.objects.all().order_by("nome")

    return render(request, "painel_home.html", {
        "pedidos": pedidos,
        "pendentes": pendentes,
        "templates": templates
    })

# ===========================================================
# ========== ENVIAR MENSAGEM PARA TODOS (W-API) =============
# ===========================================================

def enviar_whatsapp(numero, msg):
    url = settings.WAPI_URL
    headers = {
        "Authorization": f"Bearer {settings.WAPI_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "phone": numero,
        "message": msg
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def painel_msg_enviar(request):
    if request.method != "POST":
        return redirect("/painel/home/")

    texto = request.POST.get("mensagem")

    for cli in Usuario.objects.all():
        msg = texto.replace("{nome}", cli.nome_completo)\
                   .replace("{telefone}", cli.whatsapp)

        enviar_whatsapp(cli.whatsapp, msg)
        time.sleep(7)

    return redirect("/painel/home/")


# ===========================================================
# ====================== COBRAR ATRASADOS ===================
# ===========================================================

def painel_cobrar_enviar(request):
    if request.method != "POST":
        return redirect("/painel/home/")

    texto = request.POST.get("mensagem")

    pendentes = Pedido.objects.filter(forma_pagamento__in=["6", "20", "pix"])

    dados = {}
    for p in pendentes:
        cli = Usuario.objects.get(whatsapp=p.whatsapp)
        if cli.id not in dados:
            dados[cli.id] = {"cliente": cli, "total": 0, "pedidos": []}
        dados[cli.id]["total"] += p.total
        dados[cli.id]["pedidos"].append(str(p.id))

    for item in dados.values():
        cli = item["cliente"]
        total = item["total"]
        ids = ", ".join(item["pedidos"])

        msg = texto.replace("{nome}", cli.nome_completo)\
                   .replace("{total}", str(total))\
                   .replace("{pedidos}", ids)

        enviar_whatsapp(cli.whatsapp, msg)
        time.sleep(7)

    return redirect("/painel/home/")


def carregar_template(request, id):
    try:
        t = TemplateMensagem.objects.get(id=id)
        return JsonResponse({"ok": True, "texto": t.conteudo})
    except:
        return JsonResponse({"ok": False})


@csrf_exempt
def salvar_template(request):
    if request.method != "POST":
        return JsonResponse({"ok": False})

    nome = request.POST.get("nome")
    texto = request.POST.get("texto")

    if not nome or not texto:
        return JsonResponse({"ok": False, "erro": "Dados inválidos"})

    t = TemplateMensagem(nome=nome, conteudo=texto)
    t.save()

    return JsonResponse({"ok": True, "id": t.id})


def enviar_notificacao_admin(pedido):
    try:
        itens = ItemPedido.objects.filter(pedido=pedido)

        texto_itens = ""
        for item in itens:
            texto_itens += f"- {item.produto.nome} x{item.quantidade} (R$ {item.preco_unitario})\n"

        msg = (
            "📦 *NOVO PEDIDO REALIZADO!*\n\n"
            f"👤 Cliente: {pedido.nome_cliente}\n"
            f"📱 WhatsApp: {pedido.whatsapp}\n"
            f"💰 Total: R$ {pedido.total}\n"
            f"📄 Forma de pagamento: {pedido.forma_pagamento.upper()}\n"
        )

        if pedido.data_cobranca:
            msg += f"📅 Cobrança agendada para: {pedido.data_cobranca.strftime('%d/%m/%Y')}\n"

        msg += "\n🛒 *Itens do pedido:*\n" + texto_itens

        enviar_whatsapp("5514988208134", msg)

    except Exception as e:
        print("Erro ao enviar notificação ADM:", e)
