#!/usr/bin/env python3
"""
Pixel Alchemy - Lead Discovery v2 (Prospect Pool)
=================================================

Usa prospect_pool como fonte de queries - nunca repete leads.

Arquitetura:
  prospect_pool: 31,464 combinacoes (cidade|bairro|modifier|nicho)
  Nicho muda a cada轮转 diaria
  Cidade|bairro|modifier muda para nao repetir
  
Logica:
  1. SELECT pending combos ORDER BY priority DESC LIMIT N
  2. Para cada combo: build query -> SERP Maps -> dedup -> insert
  3. UPDATE pool status + stats
  4. REPEAT

Credit usage: ~1 SERP credit por busca
31,464 combos / 20 buscas/dia = 1,573 dias = 4.3 anos para agotar

Uso:
  python3 lead_discovery_pool.py              # roda 20 buscas padrao
  python3 lead_discovery_pool.py --limit 50    # 50 buscas
  python3 lead_discovery_pool.py --niche "Veterinaria"  # so um nicho
"""

import json, re, sys, time, random, urllib.parse, urllib.request, sqlite3, os, argparse
from datetime import datetime

# -- Config --
DB = os.path.expanduser('~/site-pixel-alchemy/prospects.db')
SERP_API_KEY = os.environ.get('SERP_API_KEY', '')
SERPER_BASE = 'https://google.serper.dev/search'

if not SERP_API_KEY:
    raise ValueError("SERP_API_KEY nao definido. cp .env.example .env e preencha.")

# -- Social skip patterns (Instagram/Facebook/etc = SEM site real) --
SOCIAL_SKIP = ['instagram', 'facebook', 'fb.com', 'wa.me', 'whatsapp',
               'twitter', 'linkedin', 'youtube', 'tiktok', 'pinterest',
               'booking', 'agende', 'schedule', 'yelp', 'google.com/maps',
               'sites.appbarber', 'melhorbarbeiro']


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def has_real_website(place):
    """Verifica se o lugar tem site REAL (nao Instagram/Facebook/booking)."""
    site = place.get('website', '') or ''
    if not site:
        return False
    site_lower = site.lower()
    return not any(s in site_lower for s in SOCIAL_SKIP)


def normalize_phone(raw):
    """Extrai 10 digitos do telefone. Retorna None se invalido."""
    if not raw:
        return None
    digits = re.sub(r'\D', '', str(raw))
    # Remove 55 prefix if present
    if digits.startswith('55') and len(digits) > 10:
        digits = digits[2:]
    if len(digits) == 10:
        return digits
    return None


def score_prospect(place):
    """Score 0-100. Cliente ideal = SEM site real + tem telefone."""
    has_real_site = has_real_website(place)
    has_phone = bool(place.get('phoneNumber'))
    rating = place.get('rating') or 0
    reviews = place.get('ratingCount') or 0

    score = 0
    if not has_real_site:
        score += 50
    if has_phone:
        score += 20
    if rating >= 4.5:
        score += 20
    elif rating >= 4.0:
        score += 15
    elif rating >= 3.5:
        score += 10
    if reviews >= 200:
        score += 15
    elif reviews >= 50:
        score += 10
    elif reviews >= 10:
        score += 5
    return score


def serp_maps_search(query, num=10):
    """Busca SERP Maps. Retorna lista de places ou [] se erro."""
    try:
        url = f"{SERPER_BASE}?q={urllib.parse.quote(query)}&num={num}&type=maps"
        req = urllib.request.Request(url)
        req.add_header('X-API-Key', SERP_API_KEY)
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        places = data.get('places', [])
        return places
    except Exception as e:
        return []


def prospect_exists_by_phone(conn, phone_norm):
    """Retorna dict do prospect ou None."""
    if not phone_norm:
        return None
    row = conn.execute(
        'SELECT id, nome, pipeline_status FROM prospects WHERE telefone_norm = ?',
        (phone_norm,)
    ).fetchone()
    return dict(row) if row else None


def insert_prospect(conn, data, source='serp_pool'):
    """Insere novo prospect. Colunas extras vao para observacoes JSON."""
    now = datetime.now().isoformat()

    # Colunas que existem no schema real
    base_cols = ['nome','telefone','telefone_norm','endereco','nicho',
                 'pipeline_status','source','created_at','updated_at']

    # Colunas extras: armazenadas em observacoes JSON
    extra = {}
    for key in ['rating','review_count','semsite','email','site_url','url_demo',
                'origem','canal_contato','facebook','instagram']:
        if key in data and data[key]:
            extra[key] = data[key]

    # Build vals - base cols only
    vals = []
    for c in base_cols:
        if c == 'created_at' or c == 'updated_at':
            vals.append(now)
        elif c == 'source':
            vals.append(data.get('source', source))
        elif c == 'pipeline_status':
            vals.append(data.get('pipeline_status', 'Lead'))
        else:
            vals.append(data.get(c, '') or '')

    observacoes = json.dumps(extra) if extra else ''

    sql = f"INSERT INTO prospects ({','.join(base_cols)},observacoes) VALUES ({','.join(['?']*len(base_cols))},?)"
    vals.append(observacoes)

    cur = conn.execute(sql, vals)
    conn.commit()
    return cur.lastrowid


def update_pool(conn, pool_id, status, results_new=0, results_dup=0, results_error=0, error=None):
    """Atualiza status e stats de um combo no pool."""
    now = datetime.now().isoformat()
    conn.execute(
        """UPDATE prospect_pool SET
            status=?, searched_at=?, results_new=?,
            results_dup=?, results_error=?,
            updated_at=?
            WHERE id=?""",
        (status, now, results_new, results_dup, results_error, now, pool_id)
    )
    conn.commit()


def build_query(cidade, bairro, modifier, niche):
    """Constrói query de busca a partir dos componentes do combo."""
    parts = [niche]
    if modifier and modifier != 'busca_principal':
        parts.append(modifier)
    parts.append(cidade)
    if bairro and bairro != 'Centro':
        parts.append(bairro)
    return ' '.join(parts)


# ============================================================================
# MAIN WORKER
# ============================================================================

def process_combo(conn, combo, stats):
    """Processa um combo: busca SERP -> dedup -> insere."""
    pool_id = combo['id']
    cidade = combo['cidade']
    bairro = combo['bairro']
    modifier = combo['modifier']
    niche = combo['niche']

    # Build query
    query = build_query(cidade, bairro, modifier, niche)
    print(f"  Query: {query}")

    # Mark as searching
    conn.execute("UPDATE prospect_pool SET status='searching', updated_at=datetime('now') WHERE id=?",
                 (pool_id,))
    conn.commit()

    # Search SERP Maps
    places = serp_maps_search(query, num=10)
    if places is None:  # error
        update_pool(conn, pool_id, 'error', results_error=1, error='SERP_error')
        stats['error'] += 1
        return

    new_inserts = 0
    dups = 0

    for place in places:
        nome = (place.get('title') or '').strip()
        if not nome:
            continue

        # Skip Pixel Alchemy own demos
        if 'pixelalchemy' in (place.get('website') or '').lower():
            continue

        # Extract phone
        phone_raw = place.get('phoneNumber') or ''
        phone_norm = normalize_phone(phone_raw)

        # Check if already exists
        exists = prospect_exists_by_phone(conn, phone_norm)
        if exists:
            dups += 1
            continue

        # Score
        score = score_prospect(place)
        has_real_site = has_real_website(place)

        # Build data dict
        data = {
            'nome': nome,
            'telefone': phone_raw,
            'telefone_norm': phone_norm,
            'endereco': place.get('address') or '',
            'nicho': niche,
            'site_url': place.get('website') or '',
            'pipeline_status': 'Lead',
            'source': 'serp_pool',
            'rating': place.get('rating') or 0,
            'review_count': place.get('ratingCount') or 0,
            'semsite': 'SIM' if not has_real_site else 'NAO',
        }

        try:
            pid = insert_prospect(conn, data)
            new_inserts += 1
            has_site = 'SIM' if has_real_site else 'NAO'
            print(f"    + {nome[:40]} | score={score} | tel={bool(phone_norm)} | site={has_site}")
        except Exception as e:
            pass

    # Update pool
    total_found = new_inserts + dups
    if new_inserts > 0:
        new_status = 'done'
    elif total_found == 0:
        new_status = 'exhausted'  # no results = exhausted combo
    else:
        new_status = 'done'  # only dups

    update_pool(conn, pool_id, new_status, results_new=new_inserts, results_dup=dups)
    stats['new'] += new_inserts
    stats['dup'] += dups


def run_discovery(limit=20, niche_filter=None):
    """Roda discovery em L combos pending do pool."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    stats = {'combo_processed': 0, 'new': 0, 'dup': 0, 'error': 0}

    # Build query
    query = """
        SELECT id, combo_key, cidade, bairro, modifier, niche, priority
        FROM prospect_pool
        WHERE status = 'pending'
    """
    params = []
    if niche_filter:
        query += " AND niche = ?"
        params.append(niche_filter)
    query += " ORDER BY priority DESC, RANDOM() LIMIT ?"
    params.append(limit)

    combos = conn.execute(query, params).fetchall()
    print(f"\n=== LEAD DISCOVERY POOL v2 ===")
    print(f"Combos a processar: {len(combos)}")
    if niche_filter:
        print(f"Filtrado por nicho: {niche_filter}")
    print()

    if not combos:
        print("Nenhum combo pending encontrado.")
        return stats

    for combo in combos:
        pool_id = combo['id']
        combo_key = combo['combo_key']
        niche = combo['niche']
        cidade = combo['cidade']

        print(f"[{stats['combo_processed']+1}/{len(combos)}] {combo_key[:60]}")

        try:
            process_combo(conn, combo, stats)
            stats['combo_processed'] += 1
        except Exception as e:
            print(f"    ERRO: {e}")
            conn.execute(
                "UPDATE prospect_pool SET status='error', last_error=?, updated_at=datetime('now') WHERE id=?",
                (str(e)[:200], pool_id)
            )
            conn.commit()
            stats['error'] += 1

        # Small delay to avoid rate limit
        time.sleep(random.uniform(1.0, 2.5))

    conn.close()

    print()
    print("=== RESULTADO ===")
    print(f"Combos processados: {stats['combo_processed']}")
    print(f"Prospects novos:   {stats['new']}")
    print(f"Duplicados:        {stats['dup']}")
    print(f"Erros:             {stats['error']}")
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lead Discovery v2 - Prospect Pool')
    parser.add_argument('--limit', type=int, default=20, help='Numero de combos a processar (default: 20)')
    parser.add_argument('--niche', type=str, default=None, help='Filtrar por nicho (ex: Veterinaria)')
    args = parser.parse_args()

    if args.niche:
        print(f"Filtrando por nicho: {args.niche}")

    run_discovery(limit=args.limit, niche_filter=args.niche)
