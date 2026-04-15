#!/usr/bin/env python3
"""
Pixel Alchemy — Email Discovery via SERP + Website Scraping
============================================================
Para prospects que tem telefone mas NAO tem email.

Fluxo:
  1. SERP API: busca "nome negocio + cidade" → pega site_url real
  2. Visit site: extrai emails de mailto:, paginas contact/about
  3. UPDATE prospects.db: email + site_url real

Uso:
  SERP_API_KEY='...' python3 scripts/email_discovery.py [--limit 50]
"""

import json, re, sys, time, random, urllib.parse, urllib.request, sqlite3
from datetime import datetime

SERP_API_KEY = 'e3f5602aa54fded4589424ad6c454f6e0fc168af'
BASE_URL = 'https://google.serper.dev/search'
DB = '/opt/data/home/site-pixel-alchemy/prospects.db'

# ── SERP API ────────────────────────────────────────────────────────────

def serp_search(query, num=3):
    """Busca no Google via SERP API. Retorna lista de resultados."""
    url = f'{BASE_URL}?q={urllib.parse.quote(query)}&num={num}'
    req = urllib.request.Request(url, headers={
        'X-API-Key': SERP_API_KEY,
        'Content-Type': 'application/json'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  SERP HTTP {e.code}: {e.read().decode()[:100]}")
        return {}
    except Exception as e:
        print(f"  SERP error: {e}")
        return {}


def extract_website_from_serp(data):
    """Extrai o melhor site_url de um resultado SERP."""
    organic = data.get('organic', [])
    for r in organic:
        link = r.get('link', '')
        title = r.get('title', '').lower()
        snippet = r.get('snippet', '').lower()
        # Pula nosso demo e agregadores
        skip_patterns = ['pixelalchemy', 'vercel.app', 'instagram.com', 'facebook.com',
                         'youtube.com', 'google.com', 'bing.com', 'linkedin.com',
                         'wa.me', 'whatsapp', 'twitter.com', 'tiktok']
        if any(p in link.lower() for p in skip_patterns):
            continue
        # Pula se titulo/snippet indica que e mapa ou agregador
        if any(w in title + snippet for w in ['mapa', 'localização', ' aggregated',
                                               'encontre ', 'cadastro ', ' ranking']):
            continue
        return link
    return None


# ── Website Scraping ───────────────────────────────────────────────────

def fetch_website_text(url, timeout=10):
    """Baixa HTML de uma URL e retorna texto limpo."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=timeout)
        html = resp.read().decode('utf-8', errors='ignore')
        # Remove scripts e styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        html = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', html).strip()
        return text
    except Exception as e:
        return ''


def extract_emails(text):
    """Extrai emails de texto."""
    # Email pattern
    emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    # also check mailto: links
    mailtos = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', text)
    all_emails = set(e.lower() for e in emails + mailtos)
    # Filtra emails genericos
    generic = {'contato@', 'info@', 'hello@', 'admin@', 'vendas@', 'noreply@',
               'suporte@', 'atendimento@', 'sac@'}
    filtered = [e for e in all_emails if not any(e.startswith(g) for g in generic)]
    return list(filtered)


def extract_contact_url(base_url):
    """Tenta achar URL da pagina de contato."""
    paths_to_try = ['/contact', '/contato', '/about', '/sobre', '/fale-conosco',
                    '/fale', '/contatos', '/contact-us', '/contactus']
    for path in paths_to_try:
        contact_url = base_url.rstrip('/') + path
        text = fetch_website_text(contact_url, timeout=5)
        if text and len(text) > 100:
            emails = extract_emails(text)
            if emails:
                return contact_url, emails
    return None, []


def discover_email_for_url(url):
    """Dado um site_url, tenta descobrir email. Retorna email ou None."""
    text = fetch_website_text(url)
    if not text:
        return None

    emails = extract_emails(text)
    if emails:
        return emails[0]

    # Tenta pagina de contato
    contact_url, contact_emails = extract_contact_url(url)
    if contact_emails:
        return contact_emails[0]

    return None


# ── SQLite ───────────────────────────────────────────────────────────────

def get_prospects_without_email(limit=None):
    """Retorna prospects que precisam de email discovery."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT id, nome, telefone, telefone_norm, endereco, nicho, site_url
        FROM prospects
        WHERE (email IS NULL OR email = '' OR email = 'None' OR email = 'Sem email')
          AND nome IS NOT NULL AND nome != ''
          AND pipeline_status != 'Fechado'
        ORDER BY nicho, nome
    """
    if limit:
        sql += f" LIMIT {limit}"
    return [dict(r) for r in conn.execute(sql).fetchall()], conn


def update_prospect_email(conn, prospect_id, email, real_site_url=None):
    """Atualiza email e possivelmente site_url real de um prospect."""
    now = datetime.now().isoformat()
    if real_site_url:
        conn.execute(
            "UPDATE prospects SET email=?, site_url=?, updated_at=? WHERE id=?",
            (email, real_site_url, now, prospect_id)
        )
    else:
        conn.execute(
            "UPDATE prospects SET email=?, updated_at=? WHERE id=?",
            (email, now, prospect_id)
        )
    conn.commit()


def mark_as_not_found(conn, prospect_id, reason=''):
    """Marca prospect como sem email descoberto."""
    now = datetime.now().isoformat()
    obs = f"[email_discovery] Nao encontrou email. {reason}".strip()
    conn.execute(
        "UPDATE prospects SET observacoes=CONCAT(COALESCE(observacoes, ''), ' | ', ?) WHERE id=?",
        (obs, prospect_id)
    )
    conn.commit()


# ── Main ─────────────────────────────────────────────────────────────────

def build_search_query(prospect):
    """Constrói query de busca para o SERP."""
    nome = prospect['nome'].split(' - ')[0].split(' | ')[0].strip()
    # Pega só primeiros 4 palavras do nome
    nome = ' '.join(nome.split()[:4])

    cidade = 'Ribeirão Preto'
    nicho = prospect.get('nicho', '') or ''

    # Padaria/Pizzaria/Açougue → adiciona tipo
    if nicho.lower() in ('padaria', 'pizzaria', 'acougue', 'barbearia'):
        query = f"{nome} {nicho} {cidade}"
    else:
        query = f"{nome} {cidade}"

    return query


def process_prospect(prospect, conn, stats):
    """Processa um prospect: busca Google → extrai site → extrai email."""
    search_query = build_search_query(prospect)
    print(f"\n[{stats['n']}/{stats['total']}] {prospect['nome'][:45]}")
    print(f"  Query: {search_query}")

    # Delay antip	block
    delay = random.uniform(1.5, 4.0)
    time.sleep(delay)

    # ── Step 1: Google search ─────────────────────────────────────────
    serp_data = serp_search(search_query, num=5)
    site_url = extract_website_from_serp(serp_data)

    if not site_url:
        print(f"  SEM RESULTADO no Google")
        mark_as_not_found(conn, prospect['id'], 'sem resultado no Google')
        stats['no_google'] += 1
        return

    print(f"  Site real: {site_url}")

    # Ja temos esse site_url e e nosso demo? Pula
    if 'pixelalchemy' in site_url:
        print(f"  → E nosso demo, tentando outro resultado...")
        # Tenta segundo resultado
        organic = serp_data.get('organic', [])
        for r in organic[1:]:
            link = r.get('link', '')
            if link and 'pixelalchemy' not in link and 'facebook' not in link:
                site_url = link
                break

    # ── Step 2: Extract email from site ──────────────────────────────
    delay2 = random.uniform(1.0, 2.5)
    time.sleep(delay2)

    email = discover_email_for_url(site_url)

    if email:
        print(f"  ✓ EMAIL: {email}")
        update_prospect_email(conn, prospect['id'], email, site_url)
        stats['found'] += 1
    else:
        print(f"  SEM EMAIL no site {site_url}")
        # Salva o site_url mesmo assim (mesmo sem email)
        update_prospect_email(conn, prospect['id'], '', site_url)
        mark_as_not_found(conn, prospect['id'], f'site={site_url} mas sem email')
        stats['no_email'] += 1

    stats['n'] += 1


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    prospects, conn = get_prospects_without_email(limit=limit)
    total = len(prospects)

    if total == 0:
        print("Todos os prospects ja tem email!")
        conn.close()
        return

    print(f"Email discovery: {total} prospects para processar")
    print(f"Credits: 50.000 disponiveis (SERP)")
    print("=" * 60)

    stats = {'total': total, 'n': 0, 'found': 0, 'no_google': 0, 'no_email': 0}

    try:
        for p in prospects:
            process_prospect(p, conn, stats)
            # Rate limit suave
            if stats['n'] % 10 == 0 and stats['n'] > 0:
                print(f"\n  --- Progresso: {stats['n']}/{total} ---")
                time.sleep(random.uniform(5, 10))
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario")
    finally:
        conn.close()

    print("\n" + "=" * 60)
    print(f"RESULTADO: {stats['found']} emails | {stats['no_email']} sem email | {stats['no_google']} sem Google")
    print(f"Processados: {stats['n']}/{total}")


if __name__ == '__main__':
    main()
