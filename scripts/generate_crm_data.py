#!/usr/bin/env python3
"""
Pixel Alchemy - CRM Data Generator (Supabase source)
=====================================================
Lê do Supabase (UNICA fonte de verdade) e gera dashboard-data.json.
"""

import json, subprocess, os, re
from datetime import datetime
from collections import Counter

BASE = '/opt/data/home/site-pixel-alchemy'
OUTPUT = f'{BASE}/admin/dashboard/dashboard-data.json'

SUPABASE_URL = 'https://iedltqijikyptxkpequc.supabase.co/rest/v1/prospects'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImllZGx0cWlqaWt5cHR4a3BlcXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNDg3MzksImV4cCI6MjA5MTkyNDczOX0.lR94oA864AH_3k3TiqTX-sfjLAsKVdAopA8r7F8r2uw'

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}


def fetch_supabase(query=""):
    """Fetch all prospects from Supabase. Returns list of dicts."""
    import urllib.request

    url = SUPABASE_URL + query
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def count_supabase(filter_query=""):
    """Count prospects with optional filter."""
    data = fetch_supabase(f'?select=id{filter_query}')
    return len(data)


def has_valid_phone(telefone):
    """Telefone válido: 10+ dígitos."""
    if not telefone:
        return False
    digits = re.sub(r'\D', '', telefone)
    return len(digits) >= 10


def is_whatsapp_ready(telefone):
    """WhatsApp pronto: DDD brasileiro (11-99) + número."""
    if not telefone:
        return False
    digits = re.sub(r'\D', '', telefone)
    if len(digits) < 10:
        return False
    # DDD brasileiro: 11-99
    try:
        ddd = int(digits[:2])
        return 11 <= ddd <= 99
    except:
        return False


def has_email(email):
    """Tem email válido."""
    if not email:
        return False
    return '@' in str(email) and '.' in str(email)


def get_git_log_commits():
    """Extrai commits do git log."""
    result = subprocess.run(
        ['git', 'log', '--pretty=format:%h|%s|%ai|%ae', '--all', '--name-status'],
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


def build_crm_data():
    import urllib.request

    print(f"[{datetime.now().isoformat()}] Fetching data from Supabase...")

    # Fetch ALL prospects (Supabase returns max 1000 per page, use paginate if needed)
    all_prospects = fetch_supabase('?select=*')

    # Handle pagination if total >= 1000
    if len(all_prospects) >= 1000:
        req = urllib.request.Request(SUPABASE_URL + '?select=id', headers=HEADERS)
        with urllib.request.urlopen(req) as resp:
            count_data = json.loads(resp.read())
            total = len(count_data)
            if total >= 1000:
                all_prospects = []
                for offset in range(0, total, 1000):
                    page = fetch_supabase(f'?select=*&offset={offset}&limit=1000')
                    all_prospects.extend(page)
                    if len(page) < 1000:
                        break

    print(f"  Total fetched: {len(all_prospects)}")

    # ── Funil ──────────────────────────────────────────────────────────────
    pipeline_counter = Counter(p['pipeline_status'] for p in all_prospects)
    funnel_stages = ['Lead', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Fechado']
    funnel_counts = {s: pipeline_counter.get(s, 0) for s in funnel_stages}

    total_leads = len(all_prospects)

    # ── Phone / Email / WhatsApp coverage ──────────────────────────────────
    with_phone = sum(1 for p in all_prospects if has_valid_phone(p.get('telefone')))
    with_email = sum(1 for p in all_prospects if has_email(p.get('email')))
    whatsapp_ready = sum(1 for p in all_prospects if is_whatsapp_ready(p.get('telefone')))

    # ── Sources ─────────────────────────────────────────────────────────────
    source_counter = Counter(p.get('source') or 'unknown' for p in all_prospects)

    # ── Nichos ───────────────────────────────────────────────────────────────
    nicho_counter = Counter(
        p.get('nicho') for p in all_prospects
        if p.get('nicho') and p.get('nicho').strip()
    )

    # ── Notion Status ───────────────────────────────────────────────────────
    notion_counter = Counter(
        p.get('notion_status') for p in all_prospects
        if p.get('notion_status') and p.get('notion_status').strip()
    )

    # ── Demo sites ──────────────────────────────────────────────────────────
    demo_sites_total = sum(1 for p in all_prospects if p.get('url_demo'))
    with_url_demo = sum(1 for p in all_prospects if p.get('url_demo'))
    site_criado_em_count = sum(1 for p in all_prospects if p.get('site_criado_em'))

    # ── Conversion rates ────────────────────────────────────────────────────
    contacted = funnel_counts.get('Contatado', 0)
    respondido = funnel_counts.get('Respondeu', 0)
    reuniao = funnel_counts.get('Reuniao', 0)
    proposta = funnel_counts.get('Proposta', 0)
    fechado = funnel_counts.get('Fechado', 0)

    conversion_rates = {
        'total_to_contacted': round(contacted / total_leads * 100, 1) if total_leads > 0 else 0,
        'contacted_to_responded': round(respondido / contacted * 100, 1) if contacted > 0 else 0,
        'responded_to_reuniao': round(reuniao / respondido * 100, 1) if respondido > 0 else 0,
        'reuniao_to_proposta': round(proposta / reuniao * 100, 1) if reuniao > 0 else 0,
        'proposta_to_fechado': round(fechado / proposta * 100, 1) if proposta > 0 else 0,
    }

    # ── Pending actions ─────────────────────────────────────────────────────
    in_pipeline = pipeline_counter.get('Lead', 0)
    contacted_no_response = contacted  # Contatado mas não Respondeu

    # ── Git production ───────────────────────────────────────────────────────
    commits = get_git_log_commits()
    monthly = {}
    for c in commits:
        msg = c['message'].lower()
        if 'site completo' in msg or 'demo site creation' in msg:
            date_part = c['date'][:7]
            monthly[date_part] = monthly.get(date_part, 0) + 1
    monthly_list = [{'month': m, 'count': c} for m, c in sorted(monthly.items())]

    recent = [{
        'hash': c['hash'],
        'message': c['message'],
        'date': c['date'],
        'author': c['author']
    } for c in commits[:20]]

    # ── Build output ────────────────────────────────────────────────────────
    data = {
        'generated_at': datetime.now().isoformat(),
        'crm': {
            'generated_at': datetime.now().isoformat(),

            'leads_summary': {
                'total_leads': total_leads,
                'with_phone': with_phone,
                'with_email': with_email,
                'whatsapp_ready': whatsapp_ready,
                'in_pipeline': in_pipeline,
                'contacted': contacted,
                'demo_sites_total': demo_sites_total,
                'demo_sites_with_url': with_url_demo,
                'demo_sites_creation_tracked': site_criado_em_count,
                'sources': dict(source_counter),
            },

            'funnel': {
                'stages': funnel_stages,
                'counts': funnel_counts,
                'conversion_rates': conversion_rates,
                'note': f'{total_leads} leads no Supabase. Pipeline Lead={funnel_counts["Lead"]}, Contatado={funnel_counts["Contatado"]}.'
            },

            'outreach_stats': {
                'currently_contatados': contacted,
                'currently_respondeu': respondido,
                'currently_reuniao': reuniao,
                'currently_proposta': proposta,
                'currently_fechado': fechado,
                'notion_status_breakdown': dict(notion_counter),
                'note': 'Dados do Supabase prospects. Fonte unica de verdade.'
            },

            'pending_actions': {
                'leads_pending_contact': in_pipeline,
                'contacted_no_response': contacted_no_response,
            },

            'niche_distribution': dict(nicho_counter.most_common(15)),

            'monthly_production': monthly_list,

            'recent_activity': recent,
        }
    }

    return data


def main():
    data = build_crm_data()
    crm = data['crm']

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    ls = crm['leads_summary']
    print(f"[{datetime.now().isoformat()}] Dashboard data updated")
    print(f"  Total leads: {ls['total_leads']}")
    print(f"  Com telefone: {ls['with_phone']} ({ls['with_phone']/ls['total_leads']*100:.1f}%)")
    print(f"  Com email: {ls['with_email']} ({ls['with_email']/ls['total_leads']*100:.1f}%)")
    print(f"  WhatsApp pronto: {ls['whatsapp_ready']} ({ls['whatsapp_ready']/ls['total_leads']*100:.1f}%)")
    print(f"  Funnel: {crm['funnel']['counts']}")
    print(f"  Pendencias: {crm['pending_actions']}")
    print(f"  Nichos: {dict(list(crm['niche_distribution'].items())[:5])}")
    print(f"  Demo sites: {ls['demo_sites_total']}")


if __name__ == '__main__':
    main()
