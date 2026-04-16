#!/usr/bin/env python3
"""
Pixel Alchemy — Email Discovery v2 (Maps-First)
================================================
Estratégia multi-camada para descobrir emails de prospects:

  Camada 1: SERPer Maps → phone + website real (não agregadores)
  Camada 2: Site real → scraping de /contato, /about, footer
  Camada 3: Knowledge Graph → email direto do Google
  Camada 4: WhatsApp fallback → se tem telefone, email não é obrigatório

Uso:
  SERP_API_KEY='***' python3 scripts/email_discovery_v2.py --limit 20
"""

import json, re, sys, time, random, urllib.parse, urllib.request, urllib.error
import sqlite3, os
from datetime import datetime

SERP_API_KEY = os.environ.get('SERP_API_KEY', '')
if not SERP_API_KEY:
    try:
        with open('/opt/data/home/site-pixel-alchemy/.env', 'r') as f:
            for line in f:
                if line.startswith('SERP_API_KEY'):
                    SERP_API_KEY = line.split('=')[1].strip()
    except:
        pass

if not SERP_API_KEY:
    raise ValueError("SERP_API_KEY não definida. Verifique .env")

BASE_URL = 'https://google.serper.dev/search'
DB = '/opt/data/home/site-pixel-alchemy/prospects.db'

# ── SERP API ────────────────────────────────────────────────────────────

def serp_search(query, num=5, search_type=None):
    """Busca no Google via SERP API."""
    q = urllib.parse.quote(query)
    url = f'{BASE_URL}?q={q}&num={num}'
    if search_type:
        url += f'&type={search_type}'
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


def serp_maps_search(query, num=3):
    """Busca no Google Maps via SERP API."""
    return serp_search(query, num=num, search_type='maps')


# ── Website Scraping ───────────────────────────────────────────────────

SOCIAL_SKIP = ['instagram', 'facebook', 'fb.com', 'wa.me', 'whatsapp',
               'twitter', 'linkedin', 'youtube', 'tiktok', 'pinterest',
               'booking', 'agende', 'schedule', 'yelp', 'google.com/maps',
               'sites.appbarber', 'fresha.com', 'melhorbarbeiro', 'linktr.ee',
               'agendas.link']

GENERIC_EMAILS = {'contato@', 'info@', 'hello@', 'admin@', 'vendas@',
                  'noreply@', 'suporte@', 'atendimento@', 'sac@'}


def has_real_website(url):
    """Verifica se URL é um site real (não rede social ou agregador)."""
    if not url:
        return False
    url_lower = url.lower()
    return not any(s in url_lower for s in SOCIAL_SKIP)


def fetch_website_text(url, timeout=8):
    """Baixa HTML de uma URL e retorna texto limpo."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=timeout)
        html = resp.read().decode('utf-8', errors='ignore')
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', html)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        return ''


def extract_emails(text):
    """Extrai emails de texto, filtrando genéricos."""
    emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    mailtos = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', text)
    all_emails = set(e.lower() for e in emails + mailtos)
    return [e for e in all_emails if not any(e.startswith(g) for g in GENERIC_EMAILS)]


def extract_contact_urls(base_url):
    """Tenta achar URL da página de contato."""
    paths = ['/contato', '/contact', '/fale-conosco', '/sobre', '/about',
             '/quem-somos', '/empresa']
    base = base_url.rstrip('/')
    results = []
    for path in paths:
        url = base + path
        text = fetch_website_text(url, timeout=5)
        if text and len(text) > 100:
            emails = extract_emails(text)
            if emails:
                results.append((url, emails))
    return results


def discover_email_from_site(site_url, call_counter):
    """
    Dado um site_url, descobre email.
    MAX 2 chamadas: homepage + 1 contact page.
    """
    if call_counter['calls'] >= 3:
        return None, None

    text = fetch_website_text(site_url)
    call_counter['calls'] += 1
    if not text:
        return None, None

    emails = extract_emails(text)
    if emails:
        return emails[0], None  # Email found on homepage

    # Try contact pages (costs 1 more call if we try one)
    contacts = extract_contact_urls(site_url)
    if contacts and contacts[0][1]:
        call_counter['calls'] += 1
        return contacts[0][1][0], contacts[0][0]

    return None, None


# ── Maps-First Discovery ──────────────────────────────────────────────

def maps_discovery(prospect, call_counter):
    """
    Usa SERPer Maps para encontrar phone + website real do negócio.
    MAX 1 call.
    Returns: (phone, website, title)
    """
    if call_counter['calls'] >= 3:
        return None, None, None

    nome = prospect['nome'].split(' - ')[0].split(' | ')[0].strip()
    nome = ' '.join(nome.split()[:4])
    nicho = prospect.get('nicho', '') or ''
    cidade = 'Ribeirão Preto'

    if nicho.lower() in ('padaria', 'pizzaria', 'acougue', 'barbearia'):
        query = f"{nome} {nicho} {cidade}"
    else:
        query = f"{nome} {cidade}"

    time.sleep(random.uniform(1.0, 2.5))
    data = serp_maps_search(query, num=3)
    call_counter['calls'] += 1

    places = data.get('places', [])
    if not places:
        return None, None, None

    # Find best match
    for place in places:
        website = place.get('website', '')
        if not has_real_website(website):
            continue
        phone = place.get('phoneNumber', '')
        title = place.get('title', '')
        return phone, website, title

    # No real website found
    if places:
        first = places[0]
        return first.get('phoneNumber', ''), first.get('website', ''), first.get('title', '')

    return None, None, None


def search_discovery(prospect, call_counter):
    """
    Fallback: SERP normal search para encontrar site real.
    MAX 1 call.
    Returns: website_url
    """
    if call_counter['calls'] >= 3:
        return None

    nome = prospect['nome'].split(' - ')[0].split(' | ')[0].strip()
    nome = ' '.join(nome.split()[:4])
    nicho = prospect.get('nicho', '') or ''
    cidade = 'Ribeirão Preto'

    if nicho.lower() in ('padaria', 'pizzaria', 'acougue', 'barbearia'):
        query = f"{nome} {nicho} {cidade}"
    else:
        query = f"{nome} {cidade}"

    time.sleep(random.uniform(1.0, 2.5))
    data = serp_search(query, num=5)
    call_counter['calls'] += 1

    organic = data.get('organic', [])
    for r in organic:
        link = r.get('link', '')
        title = r.get('title', '').lower()
        snippet = r.get('snippet', '').lower()
        # Skip demos, social media, aggregators
        if any(s in link.lower() for s in ['pixelalchemy', 'instagram', 'facebook',
                                             'youtube', 'twitter', 'linkedin', 'wa.me']):
            continue
        if any(w in title + snippet for w in ['mapa', 'localização', ' aggregated',
                                               'encontre ', 'cadastro ', ' ranking']):
            continue
        return link

    # Knowledge Graph email check
    kg = data.get('knowledgeGraph', {})
    kg_text = json.dumps(kg)
    emails = extract_emails(kg_text)
    if emails:
        return f"kg-email:{emails[0]}"  # Special marker for KG email

    return None


# ── SQLite ───────────────────────────────────────────────────────────────

def get_prospects_needing_email(limit=None):
    """Prospects que têm telefone mas não email (prioridade: com telefone)."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT id, nome, telefone, telefone_norm, endereco, nicho, site_url, pipeline_status
        FROM prospects
        WHERE telefone IS NOT NULL AND telefone != '' AND telefone != 'None'
          AND (email IS NULL OR email = '' OR email = 'None' OR email = 'Sem email')
          AND pipeline_status NOT IN ('Fechado', 'Perdido', 'Descartado')
        ORDER BY RANDOM()
    """
    if limit:
        sql += f" LIMIT {limit}"
    return [dict(r) for r in conn.execute(sql).fetchall()], conn


def update_prospect(conn, prospect_id, updates):
    """Atualiza campos de um prospect."""
    now = datetime.now().isoformat()
    sets = []
    params = []
    for k, v in updates.items():
        sets.append(f"{k}=?")
        params.append(v)
    sets.append("updated_at=?")
    params.append(now)
    params.append(prospect_id)
    conn.execute(f"UPDATE prospects SET {','.join(sets)} WHERE id=?", params)
    conn.commit()


def append_observation(conn, prospect_id, obs):
    """Adiciona observação ao prospect."""
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE prospects SET observacoes=CONCAT(COALESCE(observacoes,''), ' | ', ?) WHERE id=?",
        (f"[v2][{now[:10]}] {obs}", prospect_id)
    )
    conn.commit()


# ── Main ─────────────────────────────────────────────────────────────────

def process_prospect(prospect, conn, stats):
    """Processa um prospect com estratégia Maps-first."""
    search_query = prospect['nome'].split(' - ')[0].split(' | ')[0].strip()[:40]
    print(f"\n[{stats['n']}/{stats['total']}] {search_query}")
    print(f"  Phone atual: {prospect['telefone']}")
    print(f"  Site demo: {('site demo' if prospect['site_url'] and 'pixelalchemy' in str(prospect['site_url']) else 'outro')}")

    call_counter = {'calls': 0}
    results_log = []

    # ── CAMADA 1: Maps ──────────────────────────────────────────────
    phone, website, maps_title = maps_discovery(prospect, call_counter)

    updates = {}
    if phone and phone != prospect.get('telefone'):
        updates['telefone'] = phone
        results_log.append(f"phone_updated:{phone}")
        print(f"  + Phone Maps: {phone}")

    if website and has_real_website(website):
        results_log.append(f"site_found:{website}")
        print(f"  + Site real: {website}")
        updates['site_url'] = website

    # ── CAMADA 2: Email from site ──────────────────────────────────
    email_found = None
    if website and has_real_website(website) and call_counter['calls'] < 3:
        email_found, contact_url = discover_email_from_site(website, call_counter)
        if email_found:
            updates['email'] = email_found
            results_log.append(f"email:{email_found}")
            print(f"  + EMAIL: {email_found}")
            if contact_url:
                print(f"    From: {contact_url}")

    # ── CAMADA 3: Search fallback (se Maps não deu site) ───────────
    if not website and call_counter['calls'] < 3:
        site_from_search = search_discovery(prospect, call_counter)
        if site_from_search and site_from_search.startswith('kg-email:'):
            kg_email = site_from_search.replace('kg-email:', '')
            updates['email'] = kg_email
            results_log.append(f"email_kg:{kg_email}")
            print(f"  + KG EMAIL: {kg_email}")
        elif site_from_search and has_real_website(site_from_search):
            updates['site_url'] = site_from_search
            results_log.append(f"site_search:{site_from_search}")
            print(f"  + Site search: {site_from_search}")
            # Try to get email from this site
            email_found, contact_url = discover_email_from_site(site_from_search, call_counter)
            if email_found:
                updates['email'] = email_found
                results_log.append(f"email:{email_found}")
                print(f"  + EMAIL: {email_found}")

    # ── Apply updates ───────────────────────────────────────────────
    if updates:
        update_prospect(conn, prospect['id'], updates)
        print(f"  -> DB updated: {list(updates.keys())}")
        stats['updated'] += 1
    else:
        append_observation(conn, prospect['id'], f"sem email. calls={call_counter['calls']} {results_log}")
        print(f"  -> Sem email. calls={call_counter['calls']}")
        stats['no_email'] += 1

    stats['n'] += 1


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    prospects, conn = get_prospects_needing_email(limit=limit)
    total = len(prospects)

    if total == 0:
        print("Todos os prospects ja tem email!")
        conn.close()
        return

    print(f"Email Discovery v2 — {total} prospects para processar")
    print(f"Strategy: Maps-first -> site scraping -> search fallback")
    print("=" * 60)

    stats = {'total': total, 'n': 0, 'updated': 0, 'no_email': 0}

    try:
        for p in prospects:
            process_prospect(p, conn, stats)
            if stats['n'] % 10 == 0 and stats['n'] > 0:
                print(f"\n  --- Progresso: {stats['n']}/{total} ---")
                time.sleep(random.uniform(5, 10))
    except KeyboardInterrupt:
        print("\nInterrompido")
    finally:
        conn.close()

    print("\n" + "=" * 60)
    print(f"RESULTADO: {stats['updated']} atualizados | {stats['no_email']} sem email")
    print(f"Processados: {stats['n']}/{total}")


if __name__ == '__main__':
    main()
