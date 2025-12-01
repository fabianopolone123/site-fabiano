# core/mercadopago_client.py
import requests
from django.conf import settings


class MercadoPagoClient:
    def __init__(self):
        self.base_url = settings.MP_API_BASE.rstrip('/')
        self.token = settings.MP_ACCESS_TOKEN

    def criar_pagamento_pix(self, valor, external_reference, descricao):
        """
        Cria um pagamento PIX no Mercado Pago e retorna
        qr_code (chave copia e cola), qr_code_base64, status e id.
        """
        url = f"{self.base_url}/v1/payments"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            # evita duplicar cobrança se der F5
            "X-Idempotency-Key": external_reference,
        }

        payload = {
            "transaction_amount": float(valor),
            "description": descricao,
            "payment_method_id": "pix",
            "external_reference": external_reference,
            "payer": {
                # pode depois preencher com email/nome real se quiser
                "email": "cliente@example.com"
            },
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        print("STATUS:", resp.status_code)
        print("RESPONSE:", resp.text)
        data = resp.json()

        if resp.status_code not in (200, 201):
            raise Exception(f"Erro Mercado Pago: {resp.status_code} - {data}")

        td = data["point_of_interaction"]["transaction_data"]

        return {
            "id": data["id"],
            "status": data["status"],
            "qr_code": td["qr_code"],
            "qr_code_base64": td["qr_code_base64"],
            "external_reference": data.get("external_reference"),
        }
