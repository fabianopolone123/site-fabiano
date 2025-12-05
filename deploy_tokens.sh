#!/usr/bin/env bash
set -euo pipefail

# PREENCHA SEUS VALORES ANTES DE RODAR (nao deixe vazio)
MP_ACCESS_TOKEN="COLE_SEU_TOKEN_MERCADOPAGO"
WAPI_TOKEN="COLE_SEU_TOKEN_WHATSAPP"
WAPI_INSTANCE="COLE_SEU_INSTANCE_ID_WHATSAPP"

# Ajuste o dominio/servico se precisar
DOMAIN="fabianopolone.com.br"
SERVICE_NAME="loja"

# Banco de dados: use "sqlite" ou "postgres" e preencha se for Postgres
DB_ENGINE="sqlite"   # troque para "postgres" se usar Postgres
DB_NAME="db.sqlite3" # exemplo: "loja"
DB_HOST="127.0.0.1"  # exemplo: "localhost" ou IP do DB
DB_PORT="5432"
DB_USER="loja"
DB_PASSWORD=""

# --------------------------------------------------------------------
# Nao edite abaixo: apenas exporta as variaveis e chama o deploy
# --------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export MP_ACCESS_TOKEN WAPI_TOKEN WAPI_INSTANCE DOMAIN SERVICE_NAME
export DB_ENGINE DB_NAME DB_HOST DB_PORT DB_USER DB_PASSWORD

exec "$SCRIPT_DIR/deploy.sh" "$@"
