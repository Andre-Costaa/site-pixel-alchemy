#!/usr/bin/env python3
"""
Pixel Alchemy - CRM SQLite Sync
================================
Popula e mantem o SQLite (fonte unica de verdade) com dados do Notion + CSV.

FONTES (leem, nao escrevem):
  - Notion: 278 registros (telefone, status, nicho, site, etc)
  - harmonizacao.csv: 47 registros (contatos com telefone)
  - prospects-novos-batch.json: 10 registros

DESTINO (unica fonte, agentes sempre consultam aqui):
  - ~/site-pixel-alchemy/prospects.db (SQLite)

REGRAS:
  - Deduplicacao por telefone (normalizado, digitos apenas)
  - Notion sobrescreve CSV para campos em comum (mantem dados do Notion)
  - Campos exclusivos do CSV (sem email, sem site_url) sao preservados
  - pipeline_status e gerenciado manualmente ou via agente (nao vem do Notion)
  - created_at = data de criacao do registro (Notion ou CSV)
  - updated_at = agora em todo sync

Pipeline Status (padrao):
  Lead → Contatado → Respondeu → Reuniao → Proposta → Fechado
  Lost (descartado, fora do funnel)
"""

import sqlite3, csv, json, re, os, sys
from datetime import datetime
from urllib.request import urlopen
import urllib.request, json as json_lib

BASE = '/opt/data/home/site-pixel-alchemy'
DB = f'{BASE}/prospects.db'

# ── helpers ──────────────────────────────────────────────────────────────────

def norm_phone(raw):
    """Extrai apenas digitos do telefone."""
    if not raw or raw == 'Não encontrado':
        return None
    digits = re.sub(r'\D', '', str(raw))
    if len(digits) >= 10:
        return digits[-10:]  # ultimos 10 digitos (remove 55 do naoxelular)
    return None

def clean_text(val):
    """Limpa texto malformado."""
    if not val or val == 'Não encontrado':
        return ''
    return ' '.join(str(val).split()).strip()

# ── Notion ───────────────────────────────────────────────────────────────────

NOTION_TOKEN = os.environ.get('NOTION_API_TOKEN', '')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID', '2f76f51e-b8a5-8088-a52c-db29fc3c1f81')

if not NOTION_TOKEN:
    raise RuntimeError("NOTION_API_TOKEN nao definido. Use: export NOTION_API_TOKEN='ntn_...'")

def notion_query_all():
    url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
    all_results = []
    payload = {'page_size': 100}
    headers = {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }
    while True:
        data = json_lib.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        resp = urlopen(req, timeout=20)
        result = json_lib.loads(resp.read())
        all_results.extend(result.get('results', []))
        if not result.get('has_more'):
            break
        payload['start_cursor'] = result.get('next_cursor')
    return all_results

def notion_field(page, field, field_type):
    props = page['properties']
    f = props.get(field, {})
    t = f.get('type', '')

    if field_type == 'title':
        if t == 'title':
            return ''.join([x.get('plain_text', '') for x in f.get('title', [])])
    elif field_type in ('text', 'rich_text'):
        if t == 'rich_text':
            return ''.join([x.get('plain_text', '') for x in f.get('rich_text', [])])
    elif field_type == 'phone':
        if t == 'rich_text':
            return ''.join([x.get('plain_text', '') for x in f.get('rich_text', [])])
        elif t == 'phone_number':
            return f.get('phone_number') or ''
    elif field_type == 'email':
        if t == 'rich_text':
            return ''.join([x.get('plain_text', '') for x in f.get('rich_text', [])])
        elif t == 'email':
            return f.get('email') or ''
    elif field_type == 'select':
        if t == 'select':
            return (f.get('select') or {}).get('name', '') or ''
    elif field_type == 'status':
        if t == 'status':
            return (f.get('status') or {}).get('name', '') or ''
        elif t == 'select':
            return (f.get('select') or {}).get('name', '') or ''
    elif field_type == 'url':
        if t == 'url':
            return f.get('url') or ''
        elif t == 'rich_text':
            return ''.join([x.get('plain_text', '') for x in f.get('rich_text', [])])
    elif field_type == 'number':
        return f.get('number') or 0
    elif field_type == 'checkbox':
        return f.get('checkbox', False)
    elif field_type == 'date':
        if t == 'date':
            d = f.get('date')
            return (d.get('start', '') or '') if d else ''
    return ''

def fetch_notion_records():
    """Busca todos os registros do Notion."""
    pages = notion_query_all()
    records = []
    for p in pages:
        orig_status = notion_field(p, 'Status', 'status') or notion_field(p, 'Status', 'select')
        records.append({
            'notion_id':      p['id'],
            'nome':           notion_field(p, 'Nome',              'title'),
            'pipeline_status': normalize_pipeline(orig_status),
            'notion_status':  orig_status,  # ORIGINAL do Notion, nao normalizado
            'nicho':          notion_field(p, 'Nicho',             'select'),
            'telefone':       notion_field(p, 'Telefone',          'phone'),
            'email':          notion_field(p, 'Email',              'email'),
            'endereco':       notion_field(p, 'Endereço',          'rich_text'),
            'site_url':       notion_field(p, 'Site',              'url') or notion_field(p, 'Site', 'rich_text'),
            'url_demo':       notion_field(p, 'URL Demo',          'url'),
            'slug':           notion_field(p, 'Slug',              'rich_text'),
            'origem':         notion_field(p, 'Origem',            'select'),
            'canal_contato':  notion_field(p, 'Canal Contato',    'select'),
            'resposta':       notion_field(p, 'Resposta',          'rich_text'),
            'observacoes':     notion_field(p, 'Observações',       'rich_text'),
            'tentativas':     notion_field(p, 'Tentativas Contato','number'),
            'valor':          notion_field(p, 'Valor',             'number'),
            'us_id':          notion_field(p, 'US ID',             'rich_text'),
            'facebook':       notion_field(p, 'Facebook',           'rich_text'),
            'instagram':      notion_field(p, 'Instagram',          'rich_text'),
            'descricao':      notion_field(p, 'Descrição',         'rich_text'),
            'data_1_contato': notion_field(p, 'Data 1º Contato',  'date'),
            'site_criado_em': notion_field(p, 'Site Criado Em',   'date'),
            'motivo_perda':   notion_field(p, 'Motivo Perda',      'select'),
        })
    return records

# ── CSV ───────────────────────────────────────────────────────────────────────

def fetch_csv_records():
    """Lê registros do harmonizacao.csv."""
    records = []
    path = f'{BASE}/harmonizacao.csv'
    if not os.path.exists(path):
        return records
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    for row in rows[1:]:  # skip header
        if len(row) == 5:
            nome, servicos, telefone, endereco, site_url = [x.strip() for x in row]
        elif len(row) == 4:
            nome, telefone, endereco, site_url = [x.strip() for x in row]
            servicos = ''
        else:
            continue
        records.append({
            'nome':     clean_text(nome),
            'telefone': clean_text(telefone),
            'endereco': clean_text(endereco),
            'site_url': clean_text(site_url) if site_url.startswith('http') else '',
            'servicos': clean_text(servicos),
            'nicho':    infer_niche(clean_text(nome), clean_text(servicos)),  # <-- infere e salva
            'source':   'harmonizacao_csv',
        })
    return records

# ── prospects-novos-batch.json ────────────────────────────────────────────────

def fetch_json_records():
    """Lê registros do prospects-novos-batch.json."""
    records = []
    path = f'{BASE}/prospects-novos-batch.json'
    if not os.path.exists(path):
        return records
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data:
        records.append({
            'nome':     clean_text(item.get('Nome', '')),
            'telefone': clean_text(item.get('Telefone', '')),
            'endereco': clean_text(item.get('Endereço', '')),
            'nicho':    clean_text(item.get('Nicho', '')),
            'descricao': clean_text(item.get('Descrição', '')),
            'source':   'prospects_novos',
        })
    return records

# ── Pipeline normalizado ──────────────────────────────────────────────────────

PIPELINE_STAGES = ['Lead', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Fechado']

NOTION_TO_PIPELINE = {
    'Lead':             'Lead',
    'Qualificado':      'Lead',
    'Mensagem Pronta': 'Contatado',
    'Enviado':         'Contatado',
    'Site em Criação':  'Lead',
    'Respondeu':       'Respondeu',
    'Reunião':         'Reuniao',
    'Proposta':        'Proposta',
    'Fechado':         'Fechado',
    'Perdido':         'Lost',
    'Descartado':      'Lost',
}

def normalize_pipeline(notion_status):
    """Converte status do Notion para pipeline padrao. Default = Lead."""
    if not notion_status or notion_status == 'None':
        return 'Lead'
    return NOTION_TO_PIPELINE.get(notion_status, 'Lead')

def infer_niche(nome, servicos=''):
    """Infere nicho a partir do nome."""
    text = f"{nome} {servicos}".lower()
    if any(w in text for w in ['veterinaria', 'vet', 'pet', 'clinicavet']): return 'Veterinária'
    if any(w in text for w in ['harmonizacao', 'harmonização', 'botox', 'estetica facial']): return 'Harmonização'
    if any(w in text for w in ['beleza', 'salao', 'salão', 'hair', 'cabelo', 'coloracao']): return 'Beleza'
    if any(w in text for w in ['dentista', 'odontologia', 'oral', 'dental']): return 'Dentista'
    if any(w in text for w in ['barbearia', 'barber']): return 'Barbearia'
    if any(w in text for w in ['padaria', 'confeitaria']): return 'Padaria'
    if any(w in text for w in ['pizzaria', 'pizza']): return 'Pizzaria'
    if any(w in text for w in ['pet shop', 'petshop']): return 'Pet Shop'
    if any(w in text for w in ['açougue']): return 'Açougue'
    return 'Outros'

# ── Schema SQLite ─────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS prospects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    notion_id           TEXT,
    nome                TEXT NOT NULL,
    telefone            TEXT,
    telefone_norm       TEXT,  -- digitos apenas, para dedup
    email               TEXT,
    endereco            TEXT,
    nicho               TEXT,
    pipeline_status     TEXT DEFAULT 'Lead',
    -- Notion original (referencia, nao influencia trabalho)
    notion_status       TEXT,
    site_url            TEXT,
    url_demo            TEXT,
    slug                TEXT,
    origem              TEXT,
    canal_contato       TEXT,
    resposta            TEXT,
    observacoes         TEXT,
    tentativas_contato INTEGER DEFAULT 0,
    valor               REAL,
    us_id               TEXT,
    facebook            TEXT,
    instagram           TEXT,
    descricao           TEXT,
    data_1_contato      TEXT,
    site_criado_em      TEXT,
    motivo_perda        TEXT,
    source              TEXT,  -- 'notion', 'harmonizacao_csv', 'prospects_novos'
    created_at          TEXT,
    updated_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_phone_norm ON prospects(telefone_norm);
CREATE INDEX IF NOT EXISTS idx_pipeline ON prospects(pipeline_status);
CREATE INDEX IF NOT EXISTS idx_nicho ON prospects(nicho);
CREATE INDEX IF NOT EXISTS idx_notion_id ON prospects(notion_id);
"""

def get_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    return conn

# ── Merge logic ───────────────────────────────────────────────────────────────

def merge_and_insert(conn, records, source):
    """
    Insere registros de uma fonte.
    - Notion: upsert por notion_id (sobrescreve tudo)
    - CSV/JSON: upsert por telefone_norm (deduplicacao)
    """
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    inserted = 0
    updated = 0

    for rec in records:
        phone_norm = norm_phone(rec.get('telefone', ''))
        rec['telefone_norm'] = phone_norm
        rec['source'] = source
        rec['updated_at'] = now
        # Nunca usar Python None para campos texto — vira string 'None' no SQLite
        for key in ('notion_id', 'notion_status', 'origem', 'canal_contato',
                    'resposta', 'observacoes', 'slug', 'url_demo', 'site_url',
                    'email', 'facebook', 'instagram', 'descricao',
                    'data_1_contato', 'site_criado_em', 'motivo_perda'):
            if rec.get(key) is None:
                rec[key] = ''

        if source == 'notion':
            # Upsert por notion_id
            existing = conn.execute(
                'SELECT id FROM prospects WHERE notion_id = ?',
                (rec.get('notion_id'),)
            ).fetchone()

            if existing:
                # Preserve local pipeline_status se existir
                existing_row = conn.execute(
                    'SELECT pipeline_status FROM prospects WHERE notion_id = ?',
                    (rec['notion_id'],)
                ).fetchone()
                if existing_row and existing_row['pipeline_status'] not in (None, ''):
                    rec['pipeline_status'] = existing_row['pipeline_status']
                else:
                    rec['pipeline_status'] = normalize_pipeline(rec.get('pipeline_status', ''))
                if not rec.get('created_at'):
                    rec['created_at'] = now

                EXPLICIT_COLS = [
                    'notion_id', 'nome', 'pipeline_status', 'notion_status', 'nicho',
                    'telefone', 'telefone_norm', 'email', 'endereco',
                    'site_url', 'url_demo', 'slug', 'origem',
                    'canal_contato', 'resposta', 'observacoes',
                    'tentativas_contato', 'valor', 'us_id',
                    'facebook', 'instagram', 'descricao',
                    'data_1_contato', 'site_criado_em', 'motivo_perda',
                    'source', 'created_at', 'updated_at'
                ]
                set_clause = ', '.join([f"{c} = ?" for c in EXPLICIT_COLS])
                vals = [rec.get(c) for c in EXPLICIT_COLS]
                conn.execute(
                    f"UPDATE prospects SET {set_clause} WHERE notion_id = ?",
                    vals + [rec['notion_id']]
                )
                updated += 1
            else:
                rec['pipeline_status'] = normalize_pipeline(rec.get('pipeline_status', ''))
                rec['created_at'] = now
                EXPLICIT_COLS = [
                    'notion_id', 'nome', 'pipeline_status', 'notion_status', 'nicho',
                    'telefone', 'telefone_norm', 'email', 'endereco',
                    'site_url', 'url_demo', 'slug', 'origem',
                    'canal_contato', 'resposta', 'observacoes',
                    'tentativas_contato', 'valor', 'us_id',
                    'facebook', 'instagram', 'descricao',
                    'data_1_contato', 'site_criado_em', 'motivo_perda',
                    'source', 'created_at', 'updated_at'
                ]
                vals = [rec.get(c) for c in EXPLICIT_COLS]
                conn.execute(
                    f"INSERT INTO prospects ({', '.join(EXPLICIT_COLS)}) VALUES ({', '.join(['?' for _ in EXPLICIT_COLS])})",
                    vals
                )
                inserted += 1

        else:
            # CSV/JSON: upsert por telefone_norm (ignora se ja existe Notion com mesmo telefone)
            if not phone_norm:
                continue

            # Verifica se ja existe desse telefone_norm
            existing = conn.execute(
                'SELECT id, source FROM prospects WHERE telefone_norm = ?',
                (phone_norm,)
            ).fetchone()

            if existing:
                # Se ja veio do Notion, mantem Notion
                if existing['source'] == 'notion':
                    continue
                # Caso contrario, atualiza
                rec['created_at'] = now
                rec['pipeline_status'] = 'Lead'
                rec['notion_status'] = ''
                if not rec.get('nicho'):
                    rec['nicho'] = infer_niche(rec.get('nome', ''), rec.get('servicos', ''))
                EXPLICIT_COLS = [
                    'nome', 'pipeline_status', 'nicho',
                    'telefone', 'telefone_norm', 'email', 'endereco',
                    'site_url', 'origem', 'resposta', 'observacoes',
                    'tentativas_contato', 'valor', 'source',
                    'updated_at'
                ]
                set_clause = ', '.join([f"{c} = ?" for c in EXPLICIT_COLS])
                vals = [rec.get(c) for c in EXPLICIT_COLS]
                conn.execute(
                    f"UPDATE prospects SET {set_clause} WHERE telefone_norm = ?",
                    vals + [phone_norm]
                )
                updated += 1
            else:
                rec['pipeline_status'] = 'Lead'
                rec['notion_status'] = ''
                rec['created_at'] = now
                # Infere nicho se vazio
                if not rec.get('nicho'):
                    rec['nicho'] = infer_niche(rec.get('nome', ''), rec.get('servicos', ''))
                EXPLICIT_COLS = [
                    'nome', 'pipeline_status', 'nicho',
                    'telefone', 'telefone_norm', 'email', 'endereco',
                    'site_url', 'origem', 'resposta', 'observacoes',
                    'tentativas_contato', 'valor', 'source',
                    'created_at', 'updated_at'
                ]
                vals = [rec.get(c) for c in EXPLICIT_COLS]
                conn.execute(
                    f"INSERT INTO prospects ({', '.join(EXPLICIT_COLS)}) VALUES ({', '.join(['?' for _ in EXPLICIT_COLS])})",
                    vals
                )
                inserted += 1

    conn.commit()
    return inserted, updated

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print(f"[{datetime.now().isoformat()}] === CRM Sync: Notion + CSV → SQLite ===")

    conn = init_db()
    print(f"Schema initialized. DB: {DB}")

    # Notion
    print("Fetching Notion records...")
    try:
        notion_records = fetch_notion_records()
        print(f"  Notion: {len(notion_records)} records fetched")
    except Exception as e:
        print(f"  Notion fetch failed: {e}")
        notion_records = []

    # CSV
    csv_records = fetch_csv_records()
    print(f"  harmonizacao.csv: {len(csv_records)} records")

    # JSON
    json_records = fetch_json_records()
    print(f"  prospects-novos-batch.json: {len(json_records)} records")

    # Merge Notion
    print("Merging Notion records...")
    ni, nu = merge_and_insert(conn, notion_records, 'notion')
    print(f"  Notion → inserted={ni}, updated={nu}")

    # Merge CSV
    print("Merging harmonizacao.csv...")
    ci, cu = merge_and_insert(conn, csv_records, 'harmonizacao_csv')
    print(f"  CSV → inserted={ci}, updated={cu}")

    # Merge JSON
    print("Merging prospects-novos-batch.json...")
    ji, ju = merge_and_insert(conn, json_records, 'prospects_novos')
    print(f"  JSON → inserted={ji}, updated={ju}")

    # Stats
    total = conn.execute('SELECT COUNT(*) as c FROM prospects').fetchone()['c']
    pipeline_counts = {}
    for row in conn.execute('SELECT pipeline_status, COUNT(*) as c FROM prospects GROUP BY pipeline_status'):
        pipeline_counts[row['pipeline_status']] = row['c']

    niche_counts = {}
    for row in conn.execute('SELECT nicho, COUNT(*) as c FROM prospects WHERE nicho != "" GROUP BY nicho'):
        niche_counts[row['nicho']] = row['c']

    with_phone = conn.execute('SELECT COUNT(*) as c FROM prospects WHERE telefone_norm IS NOT NULL').fetchone()['c']

    print(f"\n=== SQLite Prospectos: {total} ===")
    print(f"Com telefone: {with_phone}")
    print(f"Pipeline: {dict(pipeline_counts)}")
    print(f"Nichos: {dict(sorted(niche_counts.items(), key=lambda x: -x[1]))}")

    # Notion-only stats (prospects originally from Notion)
    notion_total = conn.execute(
        "SELECT COUNT(*) as c FROM prospects WHERE notion_id IS NOT NULL AND notion_id != ''"
    ).fetchone()['c']
    print(f"\nNotion records in DB: {notion_total}")

    conn.close()
    print(f"\n[{datetime.now().isoformat()}] Done.")

if __name__ == '__main__':
    run()
