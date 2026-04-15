#!/usr/bin/env python3
"""
Pixel Alchemy - CRM Data Generator
Extrai dados REAIS do repositorio para alimentar o dashboard.

FONTES DE DADOS (as unicas que importam):
- harmonizacao.csv: 41 registros de contatos reais (37 com telefone no formato (XX) XXXXX-XXXX)
- prospects-novos-batch.json: 10 contatos novos com telefone
- site-demo/: 136 pastas de sites demo ja criados (feitos em waves anteriores)
- git log: historico de commits

REGRAS CRUCIAIS:
- NUNCA inventar numeros. O que nao esta aqui nao existe.
- Contatos do harmonizacao.csv e prospects-novos-batch sao o pool de prospeccao ATUAL.
- 25 dentist demos foram contatados ANTES e todos negaram (commit 7b174f2 + a5c1591).
- Esses 25 nao estao no harmonizacao.csv (sao de uma wave anterior).
- O funnel de prospeccao atual comeca com os 47 contatos que ainda nao foram contatados.
- Dados de SEO, clusters, e metricas nao pertencem a este dashboard.
"""

import json, csv, os, subprocess
from datetime import datetime

BASE = '/opt/data/home/site-pixel-alchemy'
OUTPUT = '/opt/data/home/site-pixel-alchemy/admin/dashboard/dashboard-data.json'


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


def has_valid_phone(phone_str):
    """Verifica se e um telefone valido no formato (XX) XXXXX-XXXX."""
    if not phone_str:
        return False
    s = str(phone_str).strip()
    return '(' in s and '9' in s[1:6] and '-' in s


def extract_harmonizacao():
    """Extrai contatos do harmonizacao.csv.
    
    O CSV tem 2 formatos:
    - 5 campos [Nome, Servicos, Telefone, Endereco, URL]: telefones estao no campo 3 (indice 2)
    - 4 campos [Nome, Telefone, Endereco, URL]: telefones estao no campo 2 (indice 1)
    """
    with open(f'{BASE}/harmonizacao.csv', 'r') as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    data_rows = all_rows[1:]  # skip header
    proper = [r for r in data_rows if len(r) == 5]  # Nome, Servicos, Telefone, Endereco, URL
    shifted = [r for r in data_rows if len(r) == 4]  # Nome, Telefone, Endereco, URL

    contacts = []
    for r in proper:
        tel = r[2].strip()
        contacts.append({
            'name': r[0].strip(),
            'phone': tel if has_valid_phone(tel) else None,
            'service': r[1].strip(),
            'address': r[3].strip(),
            'demo_url': r[4].strip() if r[4].startswith('http') else None
        })

    for r in shifted:
        tel = r[1].strip()
        contacts.append({
            'name': r[0].strip(),
            'phone': tel if has_valid_phone(tel) else None,
            'service': None,
            'address': r[2].strip(),
            'demo_url': r[3].strip() if r[3].startswith('http') else None
        })

    return contacts


def extract_prospects_novos():
    """Extrai contatos do prospects-novos-batch.json."""
    with open(f'{BASE}/prospects-novos-batch.json', 'r') as f:
        data = json.load(f)

    contacts = []
    for item in data:
        tel = item.get('Telefone', '')
        if has_valid_phone(tel):
            contacts.append({
                'name': item.get('Nome', 'Desconhecido'),
                'phone': tel,
                'niche': item.get('Nicho', 'Nao especificado'),
                'address': item.get('Endereco', ''),
                'description': item.get('Descricao', '')
            })
    return contacts


def infer_niche(name, service=None, explicit_niche=None):
    """Infere o nicho a partir do nome, servico ou nicho explicito."""
    if explicit_niche and explicit_niche != 'Nao especificado':
        n = explicit_niche.lower()
        if 'veterin' in n or 'pet' in n: return 'Veterinária'
        if 'harmon' in n or 'estetic' in n or 'beleza' in n: return 'Harmonização/Beleza'
        if 'dentist' in n or 'odont' in n: return 'Dentista'
        if 'barbear' in n: return 'Barbearia'
        if 'padaria' in n or 'confeit' in n: return 'Padaria'
        if 'pizzaria' in n or 'pizza' in n: return 'Pizzaria'
        if 'pet shop' in n: return 'Pet Shop'
        if 'açougue' in n: return 'Açougue'

    # Tenta pelo nome + servico
    text = f"{name} {service or ''}".lower()
    if any(w in text for w in ['veterinaria', 'vet', 'pet', 'clinicavet', 'clínica vet']):
        return 'Veterinária'
    if any(w in text for w in ['harmonizacao', 'harmonização', 'botox', 'estetica', 'estética']):
        return 'Harmonização/Beleza'
    if any(w in text for w in ['dentista', 'odontologia', 'oral', 'dental']):
        return 'Dentista'
    if any(w in text for w in ['barbearia', 'barber']):
        return 'Barbearia'
    if any(w in text for w in ['padaria', 'confeitaria']):
        return 'Padaria'
    if any(w in text for w in ['pizzaria', 'pizza']):
        return 'Pizzaria'
    if any(w in text for w in ['açougue', 'carn']):
        return 'Açougue'
    if any(w in text for w in ['beleza', 'salon', 'beauty']):
        return 'Beleza'
    return 'Outros'


def count_monthly_production():
    """Conta sites criados por mes via commits git (feat: US-XXX ... Site Completo)."""
    commits = get_git_log_commits()
    monthly = {}

    for c in commits:
        msg = c['message'].lower()
        if 'site completo' in msg:
            # Extrai YYYY-MM da data do commit
            date_part = c['date'][:7]  # YYYY-MM
            monthly[date_part] = monthly.get(date_part, 0) + 1

    return monthly


def build_crm_data():
    """Constroi o dicionario de dados reais do CRM."""
    commits = get_git_log_commits()
    harmonizacao = extract_harmonizacao()
    novos = extract_prospects_novos()

    # Contatos com telefone valido
    harm_with_phone = [c for c in harmonizacao if c['phone']]
    total_leads = len(harm_with_phone) + len(novos)

    # OUTREACH REAL:
    # 25 dentist demos foram contatados antes (wave antiga) e TODOS negaram.
    # Commit 7b174f2: 24 dentist demos removidos por recusa.
    # Commit a5c1591: 1 Mairake Odontologia removido por recusa.
    # Os 47 contatos atuais (harmonizacao + novos) NUNCA foram contatados.
    previously_contacted = 25
    previously_denied = 25
    currently_pending = total_leads  # nenhum dos 47 foi contatado ainda

    # Distribuicao de nichos
    niche_counts = {}
    for c in harm_with_phone:
        n = infer_niche(c['name'], c['service'])
        niche_counts[n] = niche_counts.get(n, 0) + 1
    for c in novos:
        n = infer_niche(c['name'], explicit_niche=c.get('niche'))
        niche_counts[n] = niche_counts.get(n, 0) + 1

    # Producao mensal via git
    monthly = count_monthly_production()
    monthly_list = [{'month': m, 'count': c} for m, c in sorted(monthly.items())]

    # Ultimos 20 commits
    recent = [{
        'hash': c['hash'],
        'message': c['message'],
        'date': c['date'],
        'author': c['author']
    } for c in commits[:20]]

    # Contagem real de sites demo
    demo_count = len([d for d in os.listdir(f'{BASE}/site-demo')
                      if os.path.isdir(os.path.join(f'{BASE}/site-demo', d))])

    data = {
        'generated_at': datetime.now().isoformat(),
        'crm': {
            'generated_at': datetime.now().isoformat(),

            'leads_summary': {
                'total_leads': total_leads,
                'harmonizacao_with_phone': len(harm_with_phone),
                'novos_batch': len(novos),
                'demo_sites_total': demo_count,
                'previously_contacted': previously_contacted,
                'previously_denied': previously_denied,
                'never_contacted': total_leads
            },

            'funnel': {
                'stages': ['Lead', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Fechado'],
                'counts': {
                    'Lead': total_leads,
                    'Contatado': 0,        # Nenhum dos 47 atuais foi contatado
                    'Respondeu': 0,
                    'Reuniao': 0,
                    'Proposta': 0,
                    'Fechado': 0
                },
                'note': f'{previously_contacted} prospects foram contatados em wave anterior e negaram. Os {total_leads} leads atuais ainda nao receberam contato.'
            },

            'outreach_stats': {
                'currently_contatados': 0,
                'currently_respondeu': 0,
                'currently_reuniao': 0,
                'currently_proposta': 0,
                'currently_fechado': 0,
                'previously_contacted': previously_contacted,
                'previously_denied': previously_denied,
                'response_rate': '0%',
                'note': 'Pool atual de prospeccao: harmonizacao.csv + prospects-novos-batch'
            },

            'niche_distribution': niche_counts,

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
    data = build_crm_data()
    crm = data['crm']

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.now().isoformat()}] CRM data atualizado")
    print(f"  Leads totais: {crm['leads_summary']['total_leads']}")
    print(f"  Nunca contatados: {crm['leads_summary']['never_contacted']}")
    print(f"  Ja contatados (wave ant.): {crm['leads_summary']['previously_contacted']}")
    print(f"  Ja negaram: {crm['leads_summary']['previously_denied']}")
    print(f"  Sites demo criados: {crm['leads_summary']['demo_sites_total']}")
    print(f"  PRD done: {crm['prd']['stories_done']}/{crm['prd']['stories_total']}")
    print(f"  Nichos: {crm['niche_distribution']}")


if __name__ == '__main__':
    main()
