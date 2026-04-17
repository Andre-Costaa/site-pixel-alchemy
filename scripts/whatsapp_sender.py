#!/usr/bin/env python3
"""
WhatsApp Sender — Pixel Alchemy
================================
Envia mensagens de prospeccao via Meta Business API.

Limite: 30 msgs/dia com delays humanos (20-60s entre cada).
Fonte de dados: Supabase (prospects)
"""

import os
import sys
import time
import random
import logging
import re
import urllib.request
import urllib.error
import urllib.parse
import json
from datetime import datetime, date
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
TEMPLATE_NAME = "prospecção_pixel"

# Meta Graph API
META_API_URL = "https://graph.facebook.com/v21.0"

# Supabase
SUPABASE_URL = "https://iedltqijikyptxkpequc.supabase.co"
SUPABASE_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImllZGx0cWlqaWt5cHR4a3BlcXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNDg3MzksImV4cCI6MjA5MTkyNDczOX0.lR94oA864AH_3k3TiqTX-sfjLAsKVdAopA8r7F8r2uw"
)
SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1/prospects"

# Rate limiting
MAX_DAILY = 30
MIN_DELAY = 20
MAX_DELAY = 60
RATE_LIMIT_WAIT = 300  # 5 minutos

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("whatsapp_sender")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_dotenv():
    """Carrega .env do projeto se existir."""
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        import re
        key_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if not key_pattern.match(key):
                continue
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)


def validate_phone(phone: str) -> bool:
    """Valida telefone brasileiro: DDD 11-99 + 8 ou 9 digitos."""
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 13 and digits.startswith("55"):
        digits = digits[2:]
    if len(digits) != 11:
        return False
    ddd = int(digits[:2])
    if not (11 <= ddd <= 99):
        return False
    return True


def normalize_phone(phone: str) -> Optional[str]:
    """Normaliza para 55XXXXXXXXX (13 digitos, sem +)."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 13 and digits.startswith("55"):
        return digits
    if len(digits) == 11:
        return "55" + digits
    if len(digits) == 10:
        return "55" + digits
    return None


def build_demo_url(slug: str) -> str:
    """Constrói URL do demo a partir do slug."""
    if not slug:
        return ""
    return f"https://www.pixelalchemy.com.br/site-demo/{slug}/"


def format_message(first_name: str, demo_url: str, niche: str) -> str:
    """Formata mensagem de prospeccao (max 800 caracteres, sem emojis)."""
    msg = (
        f"Ola {first_name}! Vi que voce trabalha com {niche}.\n"
        f"Criei um site demo gratuito para voce ver como ficaria:\n"
        f"{demo_url}\n"
        f"Que tal dar uma olhada? Conto com seu feedback!"
    )
    if len(msg) > 800:
        msg = msg[:797] + "..."
    return msg


def delay_human(min_sec: float = MIN_DELAY, max_sec: float = MAX_DELAY):
    """Delay aleatorio para simular comportamento humano."""
    wait = random.uniform(min_sec, max_sec)
    logger.debug(f"Aguardando {wait:.1f}s entre mensagens...")
    time.sleep(wait)


def get_daily_sent_count() -> int:
    """Retorna quantas mensagens ja foram enviadas hoje (via Supabase)."""
    today = date.today().isoformat()
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    params = {
        "data_1_contato": f"gte.{today}T00:00:00",
        "data_1_contato": f"lt.{today}T23:59:59",
        "select": "id",
    }
    try:
        url = f"{SUPABASE_REST_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read())
                return len(data)
    except Exception as e:
        logger.warning(f"Falha ao verificar count diario: {e}")
    return 0


# ---------------------------------------------------------------------------
# Supabase operations
# ---------------------------------------------------------------------------

def fetch_pending_leads(limit: int = 30) -> list[dict]:
    """Busca prospects com pipeline_status='Lead', ordenados por updated_at ASC."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    params = {
        "pipeline_status": "eq.Lead",
        "order": "updated_at.asc",
        "limit": limit,
        "select": "notion_id,nome,telefone,telefone_norm,nicho,slug,url_demo",
    }
    try:
        url = f"{SUPABASE_REST_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return json.loads(resp.read())
            return []
    except Exception as e:
        logger.error(f"Falha ao buscar leads: {e}")
        return []


def update_lead_status(notion_id: str, status: str = "Contatado") -> bool:
    """Atualiza pipeline_status e data_1_contato no Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    payload = {
        "pipeline_status": status,
        "data_1_contato": datetime.utcnow().isoformat(),
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        url = f"{SUPABASE_REST_URL}?notion_id=eq.{notion_id}"
        req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        logger.error(f"Falha ao atualizar lead {notion_id}: {e}")
        return False


# ---------------------------------------------------------------------------
# Meta WhatsApp API
# ---------------------------------------------------------------------------

def send_whatsapp_template(
    to_phone: str,
    first_name: str,
    demo_url: str,
    niche: str,
) -> tuple[bool, str]:
    """
    Envia template WhatsApp via Meta Graph API.

    Returns:
        (success, message_id or error)
    """
    if not WHATSAPP_PHONE_NUMBER_ID or not ACCESS_TOKEN:
        return False, "WHATSAPP_PHONE_NUMBER_ID ou ACCESS_TOKEN nao configurado"

    normalized = normalize_phone(to_phone)
    if not normalized:
        return False, f"Telefone invalido: {to_phone}"

    url = f"{META_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": normalized,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,
            "language": {"code": "pt_BR"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": first_name},
                        {"type": "text", "text": niche},
                        {"type": "text", "text": demo_url},
                    ],
                }
            ],
        },
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp_data = json.loads(resp.read())
            if resp.status == 200:
                msg_id = resp_data.get("messages", [{}])[0].get("id", "unknown")
                logger.info(f"  Mensagem enviada: message_id={msg_id}")
                return True, msg_id

            error_code = resp_data.get("error", {}).get("code", 0)
            error_msg = resp_data.get("error", {}).get("message", resp.read().decode())

            # Rate limit — espera 5 min e retry
            if error_code in (80001, 80004, 131045):
                logger.warning(f"Rate limit detected ({error_code}). Aguardando {RATE_LIMIT_WAIT}s...")
                time.sleep(RATE_LIMIT_WAIT)
                return send_whatsapp_template(to_phone, first_name, demo_url, niche)

            # Erro permanente — para
            if error_code in (368, 131000, 131016, 100):
                logger.error(f"Erro permanente ({error_code}): {error_msg}. PARANDO.")
                return False, f"Erro permanente: {error_msg}"

            logger.error(f"Falha API: {error_code} — {error_msg}")
            return False, f"{error_code}: {error_msg}"

    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read())
            error_code = err_data.get("error", {}).get("code", 0)
            error_msg = err_data.get("error", {}).get("message", str(e))

            # Rate limit — espera 5 min e retry
            if error_code in (80001, 80004, 131045):
                logger.warning(f"Rate limit detected ({error_code}). Aguardando {RATE_LIMIT_WAIT}s...")
                time.sleep(RATE_LIMIT_WAIT)
                return send_whatsapp_template(to_phone, first_name, demo_url, niche)

            logger.error(f"Falha HTTP API: {error_code} — {error_msg}")
            return False, f"{error_code}: {error_msg}"
        except Exception:
            logger.error(f"HTTP Error: {e}")
            return False, str(e)
    except urllib.error.URLError as e:
        return False, f"URLError: {e.reason}"
    except Exception as e:
        logger.error(f"Excecao ao enviar: {e}")
        return False, str(e)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_dotenv()

    logger.info("=" * 60)
    logger.info(f"WhatsApp Sender — Pixel Alchemy | {datetime.now().isoformat()}")
    logger.info(f"Limite diario: {MAX_DAILY} | Delay: {MIN_DELAY}-{MAX_DELAY}s")
    logger.info("=" * 60)

    if not WHATSAPP_PHONE_NUMBER_ID or not ACCESS_TOKEN:
        logger.error("ERRO: WHATSAPP_PHONE_NUMBER_ID e ACCESS_TOKEN sao obrigatorios.")
        logger.error("Defina as variaveis de ambiente ou edite o script.")
        sys.exit(1)

    start_time = time.time()
    sent = 0
    failed = 0
    skipped = 0

    # Verificar quantas ja foram enviadas hoje
    already_sent = get_daily_sent_count()
    remaining = MAX_DAILY - already_sent
    logger.info(f"Mensagens ja enviadas hoje: {already_sent} | Restantes: {remaining}")

    if remaining <= 0:
        logger.info("Limite diario atingido. Nada a fazer.")
        sys.exit(0)

    # Buscar leads
    leads = fetch_pending_leads(limit=remaining)
    if not leads:
        logger.info("Nenhum lead pendente encontrado.")
        sys.exit(0)

    logger.info(f"Leads encontrados: {len(leads)}")

    for i, lead in enumerate(leads, 1):
        notion_id = lead.get("notion_id", "")
        nome = (lead.get("nome") or "").strip()
        phone = lead.get("telefone_norm") or lead.get("telefone") or ""
        niche = (lead.get("nicho") or "seu negocio").strip()
        slug = lead.get("slug") or ""
        url_demo = lead.get("url_demo") or build_demo_url(slug)

        logger.info(f"[{i}/{len(leads)}] Processando: {nome} | tel={phone} | nicho={niche}")

        # Validacoes
        if not nome:
            logger.warning("  PULADO: nome vazio")
            skipped += 1
            continue

        if not validate_phone(phone):
            logger.warning(f"  PULADO: telefone invalido '{phone}'")
            skipped += 1
            continue

        if not url_demo:
            logger.warning("  PULADO: url_demo ausente")
            skipped += 1
            continue

        # Enviar
        success, result = send_whatsapp_template(
            to_phone=phone,
            first_name=nome.split()[0],
            demo_url=url_demo,
            niche=niche,
        )

        if success:
            update_lead_status(notion_id, "Contatado")
            sent += 1
            logger.info(f"  SUCESSO: {result}")
        else:
            failed += 1
            logger.error(f"  FALHOU: {result}")

        # Delay humano (exceto apos a ultima mensagem)
        if i < len(leads):
            delay_human()

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("RESUMO")
    logger.info(f"  Enviadas : {sent}")
    logger.info(f"  Falhadas : {failed}")
    logger.info(f"  Puladas  : {skipped}")
    logger.info(f"  Duracao  : {elapsed:.1f}s ({elapsed/60:.1f}min)")
    logger.info(f"  Data     : {datetime.now().isoformat()}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
