#!/usr/bin/env python3
"""
Pixel Alchemy - CRM Data Generator (SQLite source)
==================================================
Le do SQLite (unica fonte de verdade) e gera dashboard-data.json.

ANTES DE RODAR: rode sync_notion_csv_to_sqlite.py para garantir dados atualizados.
"""

import json, sqlite3, subprocess, os
from datetime import datetime

BASE = '/opt/data/home/site-pixel-alchemy'
DB = f'{BASE}/prospects.db'
OUTPUT = f'{BASE}/admin/dashboard/dashboard-data.json'


def get_git_log_commits():
    """Extrai commits do git log."""
    result = subprocess.run(
        ['git', 'log', '--pretty=format:%h|%s|%ai|%ae', '--all'],
        cwd=BASE, capture_output=True, text=True
    )
    lines = result.stdout.strip().split('\n')
    commits = []
    for line in lines:
        parts = line.split('|')
        if len(parts) >= 4:
            commits.append({
                'hash': parts[0],
                'message': parts[1],
                'date': parts[2],
                'author': parts[3]
            })
    return commits


def query_db(sql, params=None):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params or ())
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def build_crm_data():
    # ── Funnel do SQLite ──────────────────────────────────────────────────
    pipeline = {}
    for row in query_db('SELECT pipeline_status, COUNT(*) as c FROM prospects GROUP BY pipeline_status'):
        pipeline[row['pipeline_status']] = row['c']

    total_leads = sum(pipeline.values())

    funnel_stages = ['Lead', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Fechado']
    funnel_counts = {s: pipeline.get(s, 0) for s in funnel_stages}

    # ── Nichos ───────────────────────────────────────────────────────────
    niches = {}
    for row in query_db("SELECT nicho, COUNT(*) as c FROM prospects WHERE nicho != '' AND nicho IS NOT NULL GROUP BY nicho ORDER BY c DESC"):
        niches[row['nicho']] = row['c']

    # ── Telefone coverage ────────────────────────────────────────────────
    with_phone = query_db("SELECT COUNT(*) as c FROM prospects WHERE telefone IS NOT NULL AND telefone != ''")[0]['c']

    # ── Notion status (referencia) ───────────────────────────────────────
    notion_statuses = {}
    for row in query_db("SELECT notion_status, COUNT(*) as c FROM prospects WHERE notion_status != '' GROUP BY notion_status"):
        notion_statuses[row['notion_status']] = row['c']

    # ── Demo sites criados (site-demo/) ─────────────────────────────────
    demo_count = len([d for d in os.listdir(f'{BASE}/site-demo')
                      if os.path.isdir(os.path.join(f'{BASE}/site-demo', d))])

    # ── Producao mensal via git (feat: US-XXX ... Site Completo) ────────
    commits = get_git_log_commits()
    monthly = {}
    for c in commits:
        msg = c['message'].lower()
        if 'site completo' in msg:
            date_part = c['date'][:7]
            monthly[date_part] = monthly.get(date_part, 0) + 1
    monthly_list = [{'month': m, 'count': c} for m, c in sorted(monthly.items())]

    # ── Ultimos 20 commits ───────────────────────────────────────────────
    recent = [{
        'hash': c['hash'],
        'message': c['message'],
        'date': c['date'],
        'author': c['author']
    } for c in commits[:20]]

    # ── Source breakdown ─────────────────────────────────────────────────
    sources = {}
    for row in query_db("SELECT source, COUNT(*) as c FROM prospects GROUP BY source"):
        sources[row['source']] = row['c']

    # ── Contatados stats ────────────────────────────────────────────────
    contatados = pipeline.get('Contatado', 0)
    respondido = pipeline.get('Respondeu', 0)
    reuniao = pipeline.get('Reuniao', 0)
    proposta = pipeline.get('Proposta', 0)
    fechado = pipeline.get('Fechado', 0)

    data = {
        'generated_at': datetime.now().isoformat(),
        'crm': {
            'generated_at': datetime.now().isoformat(),

            'leads_summary': {
                'total_leads': total_leads,
                'with_phone': with_phone,
                'demo_sites_total': demo_count,
                'sources': sources,
            },

            'funnel': {
                'stages': funnel_stages,
                'counts': funnel_counts,
                'note': f'{total_leads} leads no banco. Pipeline Lead={funnel_counts["Lead"]}, Contatado={funnel_counts["Contatado"]}. Outreach ativo: 0.'
            },

            'outreach_stats': {
                'currently_contatados': contatados,
                'currently_respondeu': respondido,
                'currently_reuniao': reuniao,
                'currently_proposta': proposta,
                'currently_fechado': fechado,
                'notion_status_breakdown': notion_statuses,
                'note': 'Dados do SQLite prospects.db. Pipeline gerenciado via agentes.'
            },

            'niche_distribution': niches,

            'monthly_production': monthly_list,

            'recent_activity': recent,

            'prd': {
                'stories_total': 123,
                'stories_done': 118,
                'stories_pending': 5,
                'reviews_done': 47,
                'reviews_total': 47
            }
        }
    }

    return data


def main():
    # Garantir que sync rodou
    if not os.path.exists(DB) or os.path.getsize(DB) == 0:
        print("ERRO: prospects.db vazio. Rode sync_notion_csv_to_sqlite.py primeiro.")
        return

    data = build_crm_data()
    crm = data['crm']

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    ls = crm['leads_summary']
    print(f"[{datetime.now().isoformat()}] CRM data atualizado")
    print(f"  Total leads: {ls['total_leads']}")
    print(f"  Com telefone: {ls['with_phone']}")
    print(f"  Funnel: {crm['funnel']['counts']}")
    print(f"  Nichos: {crm['niche_distribution']}")
    print(f"  Demo sites: {ls['demo_sites_total']}")


if __name__ == '__main__':
    main()
