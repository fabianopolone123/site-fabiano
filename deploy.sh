#!/usr/bin/env bash
set -euo pipefail

# Configuracoes basicas (sobrescreva com variaveis de ambiente antes de rodar)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/.venv}"
SERVICE_NAME="${SERVICE_NAME:-loja}"
DOMAIN="${DOMAIN:-fabianopolone.com.br}"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env}"
RUN_AS_USER="${RUN_AS_USER:-$(whoami)}"
RUN_AS_GROUP="${RUN_AS_GROUP:-$RUN_AS_USER}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DB_ENGINE="${DB_ENGINE:-sqlite}"
DB_NAME="${DB_NAME:-db.sqlite3}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-loja}"
DB_PASSWORD="${DB_PASSWORD:-}"
MP_ACCESS_TOKEN="${MP_ACCESS_TOKEN:-}"
MP_API_BASE="${MP_API_BASE:-https://api.mercadopago.com}"
WAPI_TOKEN="${WAPI_TOKEN:-}"
WAPI_INSTANCE="${WAPI_INSTANCE:-}"

echo ">>> Preparando ambiente em $PROJECT_ROOT"

if ! command -v sudo >/dev/null 2>&1; then
  echo "Este script precisa de sudo para instalar pacotes e configurar servicos." >&2
  exit 1
fi

echo ">>> Instalando dependencias do sistema (python, pip, nginx)..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip nginx

echo ">>> Garantindo virtualenv em $VENV_PATH"
if [ ! -d "$VENV_PATH" ]; then
  "$PYTHON_BIN" -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"

if [ ! -f "$ENV_FILE" ]; then
  echo ">>> Criando .env em $ENV_FILE"

  prompt_secret() {
    local var_name="$1"
    local prompt_msg="$2"
    local current="${!var_name:-}"
    if [ -n "$current" ]; then
      echo ">>> Usando ${var_name} da variavel de ambiente"
      return
    fi
    read -r -s -p "${prompt_msg}: " input
    echo ""
    eval "$var_name=\"\$input\""
  }

  prompt_text() {
    local var_name="$1"
    local prompt_msg="$2"
    local current="${!var_name:-}"
    if [ -n "$current" ]; then
      echo ">>> Usando ${var_name} da variavel de ambiente"
      return
    fi
    read -r -p "${prompt_msg}: " input
    eval "$var_name=\"\$input\""
  }

  prompt_secret "MP_ACCESS_TOKEN" "Informe o token do Mercado Pago (obrigatorio)"
  prompt_secret "WAPI_TOKEN" "Informe o token do WhatsApp API (opcional, pode deixar vazio)"
  prompt_text   "WAPI_INSTANCE" "Informe o instanceId do WhatsApp API (opcional, pode deixar vazio)"

  SECRET_KEY_GEN="$("$PYTHON_BIN" - <<'PY'
import secrets
print(secrets.token_urlsafe(50))
PY
)"
  cat > "$ENV_FILE" <<EOF
DEBUG=False
SECRET_KEY=${SECRET_KEY_GEN}
ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN},127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}

DB_ENGINE=${DB_ENGINE}
DB_NAME=${DB_NAME}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

MP_ACCESS_TOKEN=${MP_ACCESS_TOKEN}
MP_API_BASE=${MP_API_BASE}

WAPI_TOKEN=${WAPI_TOKEN}
WAPI_INSTANCE=${WAPI_INSTANCE}
EOF
fi

ENV_FILE_ABS="$(realpath "$ENV_FILE")"

echo ">>> Executando migracoes e collectstatic..."
cd "$PROJECT_ROOT"
"$VENV_PATH/bin/python" manage.py migrate --noinput
"$VENV_PATH/bin/python" manage.py collectstatic --noinput

echo ">>> Criando servico systemd $SERVICE_NAME.service"
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" >/dev/null <<EOF
[Unit]
Description=Gunicorn daemon for ${SERVICE_NAME}
After=network.target

[Service]
User=${RUN_AS_USER}
Group=${RUN_AS_GROUP}
WorkingDirectory=${PROJECT_ROOT}
EnvironmentFile=${ENV_FILE_ABS}
ExecStart=${VENV_PATH}/bin/gunicorn --workers ${GUNICORN_WORKERS} --timeout 120 --bind 127.0.0.1:8000 loja.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo ">>> Configurando Nginx (dominio: ${DOMAIN})"
sudo tee "/etc/nginx/sites-available/${SERVICE_NAME}.conf" >/dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    client_max_body_size 20M;

    location /static/ {
        alias ${PROJECT_ROOT}/staticfiles/;
    }

    location /media/ {
        alias ${PROJECT_ROOT}/media/;
    }

    location / {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 120;
    }
}
EOF

sudo ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}.conf" "/etc/nginx/sites-enabled/${SERVICE_NAME}.conf"
sudo rm -f /etc/nginx/sites-enabled/default

echo ">>> Validando configuracao do Nginx"
sudo nginx -t

echo ">>> Habilitando e iniciando servicos"
sudo systemctl daemon-reload
sudo systemctl enable --now "${SERVICE_NAME}.service"
sudo systemctl restart nginx

echo ">>> Deploy finalizado. A aplicacao deve estar acessivel em http://${DOMAIN}"
