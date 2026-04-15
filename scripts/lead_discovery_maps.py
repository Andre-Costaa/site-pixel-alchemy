#!/usr/bin/env python3
"""
Pixel Alchemy — Lead Discovery via SERP Maps + Email/WhatsApp Extraction
========================================================================
ESTRATEGIA INVERTIDA:
  Em vez de procurar email em sites, USAMOS SERP Maps para encontrar
  negocios QUE NAO TEM SITE = nosso cliente ideal.

  Para cada negocio SEM site → tentamos descobrir email via redes sociais
  ou buscamos no Google "proprietario" para chegar via WhatsApp/email.

Filtros de cliente ideal:
  1. SEM website (website == null) → PRIORIDADE MAXIMA
  2. Telefone disponivel → da para WhatsApp
  3. Sem 'pixelalchemy' no site (nao e nosso cliente atual)
  4. Review count > 10 (negocio ativo, confiavel)
  5. Rating > 3.5 (nao e negocio abandonando)

Uso:
  SERP_API_KEY='...' python3 scripts/lead_discovery_maps.py [--niche "Veterinaria"] [--city "Ribeirão Preto"]
"""

import json, re, sys, time, random, urllib.parse, urllib.request, sqlite3
from datetime import datetime

SERP_API_KEY = 'e3f5602aa54fded4589424ad6c454f6e0fc168af'
MAPS_URL = 'https://google.serper.dev/search'
NORMAL_URL = 'https://google.serper.dev/search'
DB = '/opt/data/home/site-pixel-alchemy/prospects.db'

# Nichos que queremos prospectar
NICHOS = [
    'Veterinária',
    'Clínica de Harmonização',
    'Dentista',
    'Clínica de Beleza',
    'Pet Shop',
    'Barbearia',
    'Padaria',
    'Pizzaria',
    'Açougue',
]

# Cidades/regioes
CIDADES = [
    'Ribeirão Preto',
    'Serra Negra',
    'Holambra',
    'Amparo',
    'Jaguariúna',
]

# ── SERP Maps ─────────────────────────────────────────────────────────

def maps_search(query, num=20):
    """Busca businesses no Google Maps via SERP API."""
    url = f'{MAPS_URL}?q={urllib.parse.quote(query)}&num={num}&type=maps'
    req = urllib.request.Request(url, headers={
        'X-API-Key': SERP_API_KEY,
        'Content-Type': 'application/json'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  SERP Maps HTTP {e.code}: {e.read().decode()[:100]}")
        return {}
    except Exception as e:
        print(f"  SERP Maps error: {e}")
        return {}


def normal_search(query, num=5):
    """Busca normal no Google."""
    url = f'{NORMAL_URL}?q={urllib.parse.quote(query)}&num={num}'
    req = urllib.request.Request(url, headers={
        'X-API-Key': SERP_API_KEY,
        'Content-Type': 'application/json'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except:
        return {}


# ── Phone normalization ─────────────────────────────────────────────

def normalize_phone(raw):
    """Normaliza telefone para 10 digitos."""
    if not raw:
        return None
    digits = re.sub(r'\D', '', str(raw))
    if digits.startswith('55') and len(digits) > 10:
        digits = digits[2:]
    if len(digits) >= 10:
        return digits[-10:]
    return digits if len(digits) == 10 else None


# ── Email from Google (business name search) ───────────────────────

def try_find_email_via_google(business_name, address=''):
    """
    Para negocios SEM site: tenta achar email via Google search.
    Busca "business_name contato email" ou "business_name sobre".
    """
    cidade = address.split(' - ')[-1] if address else ''

    queries = [
        f'"{business_name}" {cidade} email',
        f'"{business_name}" {cidade} contato',
        f'"{business_name}" {cidade} whatsapp',
    ]

    for q in queries[:2]:
        time.sleep(random.uniform(1.0, 2.0))
        data = normal_search(q, num=5)
        organic = data.get('organic', [])

        for r in organic:
            link = r.get('link', '')
            snippet = r.get('snippet', '') or ''
            title = r.get('title', '') or ''

            # Pula agregadores e maps
            skip = ['pixelalchemy', 'google.com/maps', 'instagram.com', 'facebook.com',
                    'wa.me', 'whatsapp', 'linkedin.com', 'twitter.com', 'tiktok',
                    'booking', 'agende', 'schedule', 'yelp']
            if any(s in link.lower() for s in skip):
                continue

            # Procura email no snippet ou busca no site
            emails = re.findall(
                r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
                snippet + ' ' + title
            )
            if emails:
                return emails[0].lower()

            # Se parece site real, tenta extrair email do site
            if link and not any(s in link for s in skip):
                email = try_email_from_site(link)
                if email:
                    return email

    return None


def try_email_from_site(url, timeout=5):
    """Tenta extrair email de um site."""
    if not url or url.startswith('http') == False:
        if url:
            url = 'https://' + url
        else:
            return None

    skip_patterns = ['instagram', 'facebook', 'twitter', 'linkedin', 'youtube',
                     'tiktok', 'pinterest', 'wa.me', 'whatsapp']
    if any(p in url.lower() for p in skip_patterns):
        return None

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=timeout)
        html = resp.read().decode('utf-8', errors='ignore')
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text)

        emails = re.findall(
            r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
            text
        )

        generic = {'contato@', 'info@', 'hello@', 'admin@', 'vendas@',
                   'noreply@', 'suporte@', 'atendimento@', 'sac@',
                   ' reception@', 'contato@', 'email@'}
        filtered = [e for e in emails if not any(e.startswith(g) for g in generic)
                    and len(e) < 50]
        return filtered[0] if filtered else None
    except:
        return None


# ── WhatsApp link from Maps data ────────────────────────────────────

def get_whatsapp_link(place):
    """Extrai link WhatsApp dos bookingLinks ou gera de phone."""
    booking = place.get('bookingLinks', []) or []
    for b in booking:
        # bookingLinks pode ser string ou dict
        if isinstance(b, dict):
            url = b.get('url', '')
        else:
            url = str(b)
        if url and 'whatsapp' in url.lower():
            return url
    phone = place.get('phoneNumber', '')
    if phone:
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 10:
            return f"https://wa.me/55{digits[-10:]}?text={token_text()}"
    return None


def token_text():
    """Texto inicial para WhatsApp."""
    return urllib.parse.quote(
        "Olá! Vi sua clínica no Google e achei o trabalho de vocês incrível! "
        "Somos a Pixel Alchemy e criamos sites profissionais para profissionais de saúde e beleza. "
        "Posso te enviar uma proposta gratuita?"
    )


# ── SQLite ───────────────────────────────────────────────────────────

def prospect_exists_by_phone(phone_norm):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        'SELECT id, nome, pipeline_status, source FROM prospects WHERE telefone_norm = ?',
        (phone_norm,)
    ).fetchone()
    result = dict(row) if row else None
    conn.close()
    return result


def prospect_exists_by_name(nome):
    """Verifica se prospect com nome similar ja existe."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    nome_clean = ' '.join(nome.split()[:3]).lower()
    rows = conn.execute(
        "SELECT id, nome, telefone, pipeline_status FROM prospects WHERE LOWER(nome) LIKE ?",
        (f'%{nome_clean}%',)
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def insert_prospect(data):
    """Insere novo prospect no banco."""
    conn = sqlite3.connect(DB)
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO prospects
        (nome, telefone, telefone_norm, email, endereco, nicho,
         pipeline_status, notion_status, site_url, origem,
         canal_contato, observacoes, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'Lead', '', ?, ?,
                ?, ?, 'serp_maps', ?, ?)
    """, (
        data['nome'], data.get('telefone', ''), data.get('telefone_norm'),
        data.get('email', ''), data.get('endereco', ''), data.get('nicho', ''),
        data.get('site_url', ''), data.get('origem', ''),
        data.get('canal_contato', ''), data.get('observacoes', ''),
        now, now
    ))
    conn.commit()
    new_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return new_id


def update_prospect_phone(id, telefone, telefone_norm):
    conn = sqlite3.connect(DB)
    conn.execute(
        "UPDATE prospects SET telefone=?, telefone_norm=?, updated_at=? WHERE id=?",
        (telefone, telefone_norm, datetime.now().isoformat(), id)
    )
    conn.commit()
    conn.close()


def get_whatsapp_link_from_phone(phone_norm):
    """Gera link WhatsApp a partir de telefone normalizado."""
    if phone_norm and len(phone_norm) == 10:
        return f"https://wa.me/55{phone_norm}?text={token_text()}"
    return None


# ── Scoring ───────────────────────────────────────────────────────────

def score_prospect(place):
    """
    Score de quao bom e esse prospect.
    Maior score = melhor cliente em potencial.

    Prioridades:
    - SEM website = score alto (nosso cliente ideal!)
    - Tem telefone = pode WhatsApp
    - Rating alto = ativo
    - Review count alto = confiavel
    """
    score = 0

    has_website = bool(place.get('website'))
    has_phone = bool(place.get('phoneNumber'))
    rating = place.get('rating') or 0
    reviews = place.get('ratingCount') or 0

    # SEM site = cliente ideal (+50)
    if not has_website:
        score += 50

    # Telefone disponivel (+20)
    if has_phone:
        score += 20

    # Rating bom (+10-20)
    if rating >= 4.5:
        score += 20
    elif rating >= 4.0:
        score += 15
    elif rating >= 3.5:
        score += 10

    # Reviews suficientes (+5-15)
    if reviews >= 200:
        score += 15
    elif reviews >= 50:
        score += 10
    elif reviews >= 10:
        score += 5

    return score, has_website


# ── Main ─────────────────────────────────────────────────────────────

def discover_for_niche(nicho, cidade='Ribeirão Preto', limit_per_run=30):
    """
    Para um nicho especifico:
    1. Busca no Maps (SERPer)
    2. Filtra: sem site = cliente ideal
    3. Para cada: tenta achar email
    4. Insere no SQLite
    5. Retorna lista de prospects descobertos
    """
    print(f"\n{'='*60}")
    print(f"NICHO: {nicho} | CIDADE: {cidade}")
    print(f"{'='*60}")

    # Decide query
    query = f"{nicho} {cidade}"

    data = maps_search(query, num=20)
    places = data.get('places', [])

    if not places:
        print(f"  Nenhum resultado para: {query}")
        return []

    print(f"  {len(places)} negocios encontrados no Maps")

    results = []
    stats = {'total': 0, 'new': 0, 'dup': 0, 'no_phone': 0, 'email_found': 0}

    for place in places:
        stats['total'] += 1
        nome = place.get('title', '')
        if not nome:
            continue

        phone_raw = place.get('phoneNumber', '') or ''
        phone_norm = normalize_phone(phone_raw)
        site_url = place.get('website', '') or ''
        endereco = place.get('address', '') or ''
        rating = place.get('rating') or 0
        reviews = place.get('ratingCount') or 0
        whatsapp = get_whatsapp_link(place) or ''

        score, has_website = score_prospect(place)

        # Negocio JÁ TEM site nosso? Pula
        if site_url and 'pixelalchemy' in site_url.lower():
            print(f"  [JA E CLIENTE] {nome}")
            continue

        # Check duplicado por telefone
        dup_by_phone = None
        if phone_norm:
            dup_by_phone = prospect_exists_by_phone(phone_norm)

        if dup_by_phone:
            print(f"  [DUPLICADO TELEFONE] {nome} → {dup_by_phone['nome']}")
            # Atualiza telefone se tiver mais info
            if dup_by_phone.get('telefone') != phone_raw and phone_raw:
                update_prospect_phone(dup_by_phone['id'], phone_raw, phone_norm)
            stats['dup'] += 1
            continue

        # Check duplicado por nome
        dup_by_name = prospect_exists_by_name(nome)
        if dup_by_name:
            print(f"  [DUPLICADO NOME] {nome}")
            stats['dup'] += 1
            continue

        # Cliente ideal: SEM site
        if not has_website:
            priority = "★★★ IDEAL"
        elif score >= 30:
            priority = "★★☆ BOM"
        else:
            priority = "★☆☆ SECUNDARIO"

        print(f"\n  [{priority}] {nome}")
        print(f"    Endereco: {endereco[:50]}")
        print(f"    Telefone: {phone_raw} | Score: {score}")
        print(f"    Rating: {rating} ({reviews} reviews)")

        # Tenta descobrir email
        email = None
        if not has_website:
            # Cliente sem site = tenta mais agressivamente
            email = try_find_email_via_google(nome, endereco)
            time.sleep(random.uniform(1.0, 2.0))
        else:
            # Tem site = extrai email do site
            if site_url:
                email = try_email_from_site(site_url)

        if email:
            print(f"    ✓ EMAIL: {email}")
            stats['email_found'] += 1
        else:
            print(f"    ✗ Sem email")

        # Salva no banco
        new_id = insert_prospect({
            'nome': nome,
            'telefone': phone_raw,
            'telefone_norm': phone_norm,
            'email': email or '',
            'endereco': endereco,
            'nicho': nicho,
            'site_url': site_url,
            'origem': f'Maps:{nicho} - {cidade}',
            'canal_contato': 'whatsapp' if phone_norm else 'email',
            'observacoes': f"Score:{score} | Rating:{rating}({reviews}) | "
                           f"SemSite:{'SIM' if not has_website else 'NAO'} | "
                           f"WhatsApp:{whatsapp[:50] if whatsapp else 'N/A'}"
        })

        results.append({
            'id': new_id,
            'nome': nome,
            'phone': phone_raw,
            'phone_norm': phone_norm,
            'email': email,
            'endereco': endereco,
            'has_website': has_website,
            'score': score,
            'whatsapp': whatsapp or (get_whatsapp_link_from_phone(phone_norm) if phone_norm else None),
            'priority': priority,
        })

        stats['new'] += 1
        if not phone_norm:
            stats['no_phone'] += 1

        # Delay antipattern
        time.sleep(random.uniform(2.0, 5.0))

        if stats['new'] >= limit_per_run:
            print(f"\n  Limite de {limit_per_run} por nicho atingido")
            break

    print(f"\n  RESUMO {nicho}: {stats['new']} novos | {stats['dup']} duplicados | "
          f"{stats['email_found']} emails | {stats['no_phone']} sem fone")

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Lead discovery via SERP Maps')
    parser.add_argument('--niche', default=None, help='Nicho especifico')
    parser.add_argument('--city', default='Ribeirão Preto', help='Cidade')
    parser.add_argument('--limit', type=int, default=30, help='Max prospects por nicho')
    args = parser.parse_args()

    niches_to_run = [args.niche] if args.niche else NICHOS

    all_results = []
    for nicho in niches_to_run:
        results = discover_for_niche(nicho, args.city, limit_per_run=args.limit)
        all_results.extend(results)
        time.sleep(random.uniform(5.0, 10.0))  # Pause entre nichos

    print(f"\n{'='*60}")
    print(f"RESULTADO TOTAL: {len(all_results)} prospects descobertos")

    # Resume
    with_email = [r for r in all_results if r.get('email')]
    without_email = [r for r in all_results if not r.get('email')]
    no_site = [r for r in all_results if not r.get('has_website')]
    with_whatsapp = [r for r in all_results if r.get('whatsapp')]

    print(f"  Com email:       {len(with_email)}")
    print(f"  Sem email:       {len(without_email)}")
    print(f"  SEM SITE (ideal): {len(no_site)}")
    print(f"  Com WhatsApp:    {len(with_whatsapp)}")

    print(f"\n  Nichos processados: {niches_to_run}")
    print(f"\nPronto para outreach!rode generate_crm_data.py para atualizar dashboard.")


if __name__ == '__main__':
    main()
