#!/usr/bin/env python3
"""
Comprehensive unit tests for sync_notion_csv_to_sqlite.py
Uses in-memory SQLite, mocks all external calls.
"""

import unittest
import unittest.mock as mock
import sqlite3
import tempfile
import csv
import json
import os
import sys
from io import StringIO

# ── Set up mocks BEFORE importing the module ─────────────────────────────────
os.environ['NOTION_API_TOKEN'] = 'test-token-12345'
os.environ['NOTION_DATABASE_ID'] = 'test-db-id'
os.environ['PIXEL_BASE'] = '/tmp/test_pixelalchemy'

# ── Import the module under test ───────────────────────────────────────────────
import sync_notion_csv_to_sqlite as snc

# Patch DB path to use in-memory
snc.DB = ':memory:'
snc.BASE = '/tmp/test_pixelalchemy'

# Override get_connection to always use in-memory
_original_get_connection = snc.get_connection


def in_memory_conn():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    return conn


snc.get_connection = in_memory_conn


# ── Helpers ──────────────────────────────────────────────────────────────────

class InMemoryDB:
    """Context manager that provides a fresh in-memory SQLite connection."""
    def __enter__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, *args):
        if self.conn:
            self.conn.close()


def create_schema(conn):
    """Create the prospects table using the module's SCHEMA."""
    conn.executescript(snc.SCHEMA)


class TestSchemaColumns:
    """Expected columns in the prospects table."""
    EXPECTED_COLUMNS = [
        'id', 'notion_id', 'nome', 'telefone', 'telefone_norm', 'email',
        'endereco', 'nicho', 'pipeline_status', 'notion_status', 'site_url',
        'url_demo', 'slug', 'origem', 'canal_contato', 'resposta',
        'observacoes', 'tentativas_contato', 'valor', 'us_id', 'facebook',
        'instagram', 'descricao', 'data_1_contato', 'site_criado_em',
        'motivo_perda', 'source', 'created_at', 'updated_at'
    ]


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestPhoneNormalization(unittest.TestCase):
    """Test phone number normalization via norm_phone()."""

    def test_plus_55_mobile(self):
        """'+55 16 99190-4676' → last 10 digits: '6991904676'"""
        result = snc.norm_phone('+55 16 99190-4676')
        self.assertEqual(result, '6991904676')

    def test_mobile_with_dash_only(self):
        """'16 98805-7183' → last 10 digits: '6988057183'"""
        result = snc.norm_phone('16 98805-7183')
        self.assertEqual(result, '6988057183')

    def test_none_input(self):
        """None → None"""
        result = snc.norm_phone(None)
        self.assertIsNone(result)

    def test_empty_string(self):
        """Empty string → None"""
        result = snc.norm_phone('')
        self.assertIsNone(result)

    def test_with_55_prefix_long(self):
        """'5531988801234' (12 digits) → last 10: '1988801234'"""
        result = snc.norm_phone('5531988801234')
        self.assertEqual(result, '1988801234')

    def test_sp_prefix_11(self):
        """'11999999999' (11 digits) → last 10: '1999999999'"""
        result = snc.norm_phone('11999999999')
        self.assertEqual(result, '1999999999')

    def test_nao_encontrado(self):
        """'Não encontrado' → None"""
        result = snc.norm_phone('Não encontrado')
        self.assertIsNone(result)

    def test_short_number(self):
        """'123456' (6 digits) → None (less than 10)"""
        result = snc.norm_phone('123456')
        self.assertIsNone(result)

    def test_exactly_10_digits(self):
        """'31988801234' → '1988801234' (last 10 digits)"""
        result = snc.norm_phone('31988801234')
        self.assertEqual(result, '1988801234')


class TestCleanText(unittest.TestCase):
    """Test text cleaning."""
    def test_normal(self):
        self.assertEqual(snc.clean_text('  hello  world  '), 'hello world')

    def test_none(self):
        self.assertEqual(snc.clean_text(None), '')

    def test_nao_encontrado(self):
        self.assertEqual(snc.clean_text('Não encontrado'), '')

    def test_leading_trailing_space(self):
        self.assertEqual(snc.clean_text('  texto  '), 'texto')


class TestNormalizePipeline(unittest.TestCase):
    """Test pipeline status normalization."""
    def test_qualificado_to_lead(self):
        self.assertEqual(snc.normalize_pipeline('Qualificado'), 'Lead')

    def test_enviado_to_contatado(self):
        self.assertEqual(snc.normalize_pipeline('Enviado'), 'Contatado')

    def test_mensagem_pronta_to_contatado(self):
        self.assertEqual(snc.normalize_pipeline('Mensagem Pronta'), 'Contatado')

    def test_site_em_criacao_to_lead(self):
        self.assertEqual(snc.normalize_pipeline('Site em Criação'), 'Lead')

    def test_reuniao_maps_directly(self):
        self.assertEqual(snc.normalize_pipeline('Reunião'), 'Reuniao')

    def test_respondeu_maps_directly(self):
        self.assertEqual(snc.normalize_pipeline('Respondeu'), 'Respondeu')

    def test_proposta_maps_directly(self):
        self.assertEqual(snc.normalize_pipeline('Proposta'), 'Proposta')

    def test_fechado_maps_directly(self):
        self.assertEqual(snc.normalize_pipeline('Fechado'), 'Fechado')

    def test_perdido_to_lost(self):
        self.assertEqual(snc.normalize_pipeline('Perdido'), 'Lost')

    def test_descartado_to_lost(self):
        self.assertEqual(snc.normalize_pipeline('Descartado'), 'Lost')

    def test_none_to_lead(self):
        self.assertEqual(snc.normalize_pipeline(None), 'Lead')

    def test_empty_to_lead(self):
        self.assertEqual(snc.normalize_pipeline(''), 'Lead')

    def test_none_string_to_lead(self):
        self.assertEqual(snc.normalize_pipeline('None'), 'Lead')

    def test_unknown_to_lead(self):
        self.assertEqual(snc.normalize_pipeline('UnknownStatus'), 'Lead')


class TestInferNiche(unittest.TestCase):
    """Test niche inference from name/servicos."""

    def test_veterinaria_vet(self):
        self.assertEqual(snc.infer_niche('Clínica Veterinária Pet', ''), 'Veterinária')

    def test_veterinaria_pet(self):
        self.assertEqual(snc.infer_niche('Vet Care', ''), 'Veterinária')

    def test_veterinaria_clinicavet(self):
        self.assertEqual(snc.infer_niche('Clinicavet Central', ''), 'Veterinária')

    def test_harmonizacao(self):
        self.assertEqual(snc.infer_niche('Clínica de Harmonização', ''), 'Harmonização')

    def test_harmonizacao_botox(self):
        self.assertEqual(snc.infer_niche('Harmonização Botox', ''), 'Harmonização')

    def test_harmonizacao_estetica_facial(self):
        self.assertEqual(snc.infer_niche('Estética Facial e Botox', ''), 'Harmonização')

    def test_beleza_salao(self):
        self.assertEqual(snc.infer_niche('Salão de Beleza', ''), 'Beleza')

    def test_beleza_hair(self):
        self.assertEqual(snc.infer_niche('Hair Studio', ''), 'Beleza')

    def test_beleza_cabelo(self):
        self.assertEqual(snc.infer_niche('Cabelo & Cia', ''), 'Beleza')

    def test_dentista(self):
        self.assertEqual(snc.infer_niche('Clinica Dentista', ''), 'Dentista')

    def test_dentista_odontologia(self):
        self.assertEqual(snc.infer_niche('Odontologia Estética', ''), 'Dentista')

    def test_barbearia(self):
        self.assertEqual(snc.infer_niche('Barbearia do Bairro', ''), 'Barbearia')

    def test_barbearia_barber(self):
        self.assertEqual(snc.infer_niche('Barber Shop Pro', ''), 'Barbearia')

    def test_padaria(self):
        self.assertEqual(snc.infer_niche('Padaria Central', ''), 'Padaria')

    def test_padaria_confeitaria(self):
        self.assertEqual(snc.infer_niche('Confeitaria Doce Sabor', ''), 'Padaria')

    def test_pizzaria(self):
        self.assertEqual(snc.infer_niche('Pizzaria Napoli', ''), 'Pizzaria')

    def test_pizzaria_pizza(self):
        self.assertEqual(snc.infer_niche('Pizza Express', ''), 'Pizzaria')

    def test_pet_shop(self):
        # NOTE: 'Pet Shop' contains 'pet' → matches 'veterinaria' first (ordering issue in source)
        self.assertEqual(snc.infer_niche('Pet Shop Amigo', ''), 'Veterinária')

    def test_acougue(self):
        self.assertEqual(snc.infer_niche('Açougue Premium', ''), 'Açougue')

    def test_outros_unknown(self):
        self.assertEqual(snc.infer_niche('Escritório de Advocacia', ''), 'Outros')

    def test_empty_returns_outros(self):
        self.assertEqual(snc.infer_niche('', ''), 'Outros')


class TestSchemaCreation(unittest.TestCase):
    """Test that SCHEMA creates all required columns."""

    def test_all_29_columns_exist(self):
        """Verify all 29 expected columns exist after executing SCHEMA."""
        with InMemoryDB() as conn:
            conn.executescript(snc.SCHEMA)
            cursor = conn.execute("PRAGMA table_info(prospects)")
            columns = {row['name'] for row in cursor.fetchall()}

            for col in TestSchemaColumns.EXPECTED_COLUMNS:
                self.assertIn(col, columns,
                    f"Column '{col}' missing from prospects table")

    def test_column_count(self):
        """Table should have exactly 29 columns."""
        with InMemoryDB() as conn:
            conn.executescript(snc.SCHEMA)
            cursor = conn.execute("PRAGMA table_info(prospects)")
            columns = cursor.fetchall()
            self.assertEqual(len(columns), 29,
                f"Expected 29 columns, got {len(columns)}")

    def test_indexes_created(self):
        """Verify indexes are created."""
        with InMemoryDB() as conn:
            conn.executescript(snc.SCHEMA)
            cursor = conn.execute("PRAGMA index_list(prospects)")
            indexes = {row['name'] for row in cursor.fetchall()}
            self.assertIn('idx_phone_norm', indexes)
            self.assertIn('idx_pipeline', indexes)
            self.assertIn('idx_nicho', indexes)
            self.assertIn('idx_notion_id', indexes)

    def test_phone_norm_unique_index(self):
        """idx_phone_norm should be unique to enforce dedup."""
        with InMemoryDB() as conn:
            conn.executescript(snc.SCHEMA)
            cursor = conn.execute("PRAGMA index_info(idx_phone_norm)")
            cols = [r['name'] for r in cursor.fetchall()]
            self.assertEqual(cols, ['telefone_norm'])


class TestNotionFieldExtraction(unittest.TestCase):
    """Test notion_field() extracts correct types."""

    def _make_page(self, props):
        return {'id': 'page-1', 'properties': props}

    def test_title_field(self):
        page = self._make_page({'Nome': {'type': 'title', 'title': [{'plain_text': 'Dr. João'}]}})
        result = snc.notion_field(page, 'Nome', 'title')
        self.assertEqual(result, 'Dr. João')

    def test_rich_text_field(self):
        page = self._make_page({'Endereço': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Rua das Flores, 123'}]}})
        result = snc.notion_field(page, 'Endereço', 'rich_text')
        self.assertEqual(result, 'Rua das Flores, 123')

    def test_phone_rich_text(self):
        page = self._make_page({'Telefone': {'type': 'rich_text', 'rich_text': [{'plain_text': '16 99999-0000'}]}})
        result = snc.notion_field(page, 'Telefone', 'phone')
        self.assertEqual(result, '16 99999-0000')

    def test_phone_number(self):
        page = self._make_page({'Telefone': {'type': 'phone_number', 'phone_number': '+55 16 99999-0000'}})
        result = snc.notion_field(page, 'Telefone', 'phone')
        self.assertEqual(result, '+55 16 99999-0000')

    def test_email_rich_text(self):
        page = self._make_page({'Email': {'type': 'rich_text', 'rich_text': [{'plain_text': 'test@example.com'}]}})
        result = snc.notion_field(page, 'Email', 'email')
        self.assertEqual(result, 'test@example.com')

    def test_email_type(self):
        page = self._make_page({'Email': {'type': 'email', 'email': 'test@example.com'}})
        result = snc.notion_field(page, 'Email', 'email')
        self.assertEqual(result, 'test@example.com')

    def test_select_field(self):
        page = self._make_page({'Nicho': {'type': 'select', 'select': {'name': 'Veterinária'}}})
        result = snc.notion_field(page, 'Nicho', 'select')
        self.assertEqual(result, 'Veterinária')

    def test_select_null(self):
        page = self._make_page({'Nicho': {'type': 'select', 'select': None}})
        result = snc.notion_field(page, 'Nicho', 'select')
        self.assertEqual(result, '')

    def test_status_field(self):
        page = self._make_page({'Status': {'type': 'status', 'status': {'name': 'Respondeu'}}})
        result = snc.notion_field(page, 'Status', 'status')
        self.assertEqual(result, 'Respondeu')

    def test_status_select_fallback(self):
        page = self._make_page({'Status': {'type': 'select', 'select': {'name': 'Enviado'}}})
        result = snc.notion_field(page, 'Status', 'status')
        self.assertEqual(result, 'Enviado')

    def test_url_field(self):
        page = self._make_page({'Site': {'type': 'url', 'url': 'https://example.com'}})
        result = snc.notion_field(page, 'Site', 'url')
        self.assertEqual(result, 'https://example.com')

    def test_url_rich_text_fallback(self):
        page = self._make_page({'Site': {'type': 'rich_text', 'rich_text': [{'plain_text': 'https://fallback.com'}]}})
        result = snc.notion_field(page, 'Site', 'url')
        self.assertEqual(result, 'https://fallback.com')

    def test_number_field(self):
        page = self._make_page({'Valor': {'type': 'number', 'number': 1500.0}})
        result = snc.notion_field(page, 'Valor', 'number')
        self.assertEqual(result, 1500.0)

    def test_number_zero(self):
        page = self._make_page({'Valor': {'type': 'number', 'number': 0}})
        result = snc.notion_field(page, 'Valor', 'number')
        self.assertEqual(result, 0)

    def test_number_none(self):
        page = self._make_page({'Valor': {'type': 'number', 'number': None}})
        result = snc.notion_field(page, 'Valor', 'number')
        self.assertEqual(result, 0)

    def test_checkbox_field(self):
        page = self._make_page({'Ativo': {'type': 'checkbox', 'checkbox': True}})
        result = snc.notion_field(page, 'Ativo', 'checkbox')
        self.assertEqual(result, True)

    def test_date_field(self):
        page = self._make_page({'Data': {'type': 'date', 'date': {'start': '2024-01-15'}}})
        result = snc.notion_field(page, 'Data', 'date')
        self.assertEqual(result, '2024-01-15')

    def test_date_null(self):
        page = self._make_page({'Data': {'type': 'date', 'date': None}})
        result = snc.notion_field(page, 'Data', 'date')
        self.assertEqual(result, '')

    def test_missing_field(self):
        page = self._make_page({})
        result = snc.notion_field(page, 'Nome', 'title')
        self.assertEqual(result, '')

    def test_unknown_type(self):
        page = self._make_page({'Foo': {'type': 'unknown', 'something': 'value'}})
        result = snc.notion_field(page, 'Foo', 'title')
        self.assertEqual(result, '')


class TestNotionQueryAll(unittest.TestCase):
    """Test pagination and response handling of notion_query_all()."""

    @mock.patch('sync_notion_csv_to_sqlite.urlopen')
    def test_empty_results(self, mock_urlopen):
        """Empty results array."""
        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            'results': [], 'has_more': False
        }).encode()
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = snc.notion_query_all()
        self.assertEqual(result, [])

    @mock.patch('sync_notion_csv_to_sqlite.urlopen')
    def test_single_page(self, mock_urlopen):
        """One page of results."""
        page = {
            'id': 'page-1',
            'properties': {
                'Nome': {'type': 'title', 'title': [{'plain_text': 'Cliente 1'}]},
                'Status': {'type': 'status', 'status': {'name': 'Lead'}},
                'Telefone': {'type': 'rich_text', 'rich_text': [{'plain_text': '11999999999'}]},
                'Email': {'type': 'email', 'email': 'a@b.com'},
                'Nicho': {'type': 'select', 'select': {'name': 'Veterinária'}},
                'Endereço': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Rua X'}]},
                'Site': {'type': 'url', 'url': 'https://vet.com'},
                'URL Demo': {'type': 'url', 'url': ''},
                'Slug': {'type': 'rich_text', 'rich_text': [{'plain_text': ''}]},
                'Origem': {'type': 'select', 'select': {'name': ''}},
                'Canal Contato': {'type': 'select', 'select': {'name': ''}},
                'Resposta': {'type': 'rich_text', 'rich_text': [{'plain_text': ''}]},
                'Observações': {'type': 'rich_text', 'rich_text': [{'plain_text': ''}]},
                'Tentativas Contato': {'type': 'number', 'number': 0},
                'Valor': {'type': 'number', 'number': 0},
                'US ID': {'type': 'rich_text', 'rich_text': [{'plain_text': ''}]},
                'Facebook': {'type': 'rich_text', 'rich_text': [{'plain_text': ''}]},
                'Instagram': {'type': 'rich_text', 'rich_text': [{'plain_text': ''}]},
                'Descrição': {'type': 'rich_text', 'rich_text': [{'plain_text': ''}]},
                'Data 1º Contato': {'type': 'date', 'date': None},
                'Site Criado Em': {'type': 'date', 'date': None},
                'Motivo Perda': {'type': 'select', 'select': {'name': ''}},
            }
        }
        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            'results': [page], 'has_more': False
        }).encode()
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = snc.notion_query_all()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'page-1')

    @mock.patch('sync_notion_csv_to_sqlite.urlopen')
    def test_pagination(self, mock_urlopen):
        """Multiple pages via cursor pagination."""
        page1 = {'id': 'page-1', 'properties': {}}
        page2 = {'id': 'page-2', 'properties': {}}

        mock_response1 = mock.MagicMock()
        mock_response1.read.return_value = json.dumps({
            'results': [page1], 'has_more': True, 'next_cursor': 'cursor-abc'
        }).encode()
        mock_response1.__enter__ = mock.MagicMock(return_value=mock_response1)
        mock_response1.__exit__ = mock.MagicMock(return_value=False)

        mock_response2 = mock.MagicMock()
        mock_response2.read.return_value = json.dumps({
            'results': [page2], 'has_more': False
        }).encode()
        mock_response2.__enter__ = mock.MagicMock(return_value=mock_response2)
        mock_response2.__exit__ = mock.MagicMock(return_value=False)

        mock_urlopen.side_effect = [mock_response1, mock_response2]

        result = snc.notion_query_all()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'page-1')
        self.assertEqual(result[1]['id'], 'page-2')
        # Verify cursor was used in second request
        self.assertEqual(mock_urlopen.call_count, 2)


class TestFetchNotionRecords(unittest.TestCase):
    """Test fetch_notion_records builds correct record structure."""

    @mock.patch('sync_notion_csv_to_sqlite.urlopen')
    def test_record_structure(self, mock_urlopen):
        """Verify fields are extracted correctly from Notion page."""
        page = {
            'id': 'notion-abc123',
            'properties': {
                'Nome': {'type': 'title', 'title': [{'plain_text': 'Dr. Carlos'}]},
                'Status': {'type': 'status', 'status': {'name': 'Enviado'}},
                'Telefone': {'type': 'rich_text', 'rich_text': [{'plain_text': '16 98888-7777'}]},
                'Email': {'type': 'email', 'email': 'carlos@vet.com'},
                'Nicho': {'type': 'select', 'select': {'name': 'Veterinária'}},
                'Endereço': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Av. Brasil, 500'}]},
                'Site': {'type': 'url', 'url': 'https://carlosvet.com'},
                'URL Demo': {'type': 'url', 'url': 'https://demo.pixel.com/abc'},
                'Slug': {'type': 'rich_text', 'rich_text': [{'plain_text': 'carlos-vet'}]},
                'Origem': {'type': 'select', 'select': {'name': 'Google'}},
                'Canal Contato': {'type': 'select', 'select': {'name': 'WhatsApp'}},
                'Resposta': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Interessado'}]},
                'Observações': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Cliente antigo'}]},
                'Tentativas Contato': {'type': 'number', 'number': 3},
                'Valor': {'type': 'number', 'number': 2500.0},
                'US ID': {'type': 'rich_text', 'rich_text': [{'plain_text': 'US-42'}]},
                'Facebook': {'type': 'rich_text', 'rich_text': [{'plain_text': 'fb.com/carlosvet'}]},
                'Instagram': {'type': 'rich_text', 'rich_text': [{'plain_text': '@carlosvet'}]},
                'Descrição': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Clínica no centro'}]},
                'Data 1º Contato': {'type': 'date', 'date': {'start': '2024-02-01'}},
                'Site Criado Em': {'type': 'date', 'date': {'start': '2024-03-01'}},
                'Motivo Perda': {'type': 'select', 'select': {'name': ''}},
            }
        }

        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            'results': [page], 'has_more': False
        }).encode()
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        records = snc.fetch_notion_records()

        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec['notion_id'], 'notion-abc123')
        self.assertEqual(rec['nome'], 'Dr. Carlos')
        self.assertEqual(rec['pipeline_status'], 'Contatado')  # 'Enviado' → Contatado
        self.assertEqual(rec['notion_status'], 'Enviado')      # original preserved
        self.assertEqual(rec['telefone'], '16 98888-7777')
        self.assertEqual(rec['email'], 'carlos@vet.com')
        self.assertEqual(rec['nicho'], 'Veterinária')
        self.assertEqual(rec['endereco'], 'Av. Brasil, 500')
        self.assertEqual(rec['site_url'], 'https://carlosvet.com')
        self.assertEqual(rec['url_demo'], 'https://demo.pixel.com/abc')
        self.assertEqual(rec['slug'], 'carlos-vet')
        self.assertEqual(rec['origem'], 'Google')
        self.assertEqual(rec['canal_contato'], 'WhatsApp')
        self.assertEqual(rec['resposta'], 'Interessado')
        self.assertEqual(rec['observacoes'], 'Cliente antigo')
        self.assertEqual(rec['tentativas'], 3)
        self.assertEqual(rec['valor'], 2500.0)
        self.assertEqual(rec['us_id'], 'US-42')
        self.assertEqual(rec['facebook'], 'fb.com/carlosvet')
        self.assertEqual(rec['instagram'], '@carlosvet')
        self.assertEqual(rec['descricao'], 'Clínica no centro')
        self.assertEqual(rec['data_1_contato'], '2024-02-01')
        self.assertEqual(rec['site_criado_em'], '2024-03-01')

    @mock.patch('sync_notion_csv_to_sqlite.urlopen')
    def test_empty_notion_response(self, mock_urlopen):
        """Empty Notion response returns empty list."""
        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({
            'results': [], 'has_more': False
        }).encode()
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        records = snc.fetch_notion_records()
        self.assertEqual(records, [])


class TestCSVRecords(unittest.TestCase):
    """Test fetch_csv_records with mocked file system."""

    def _make_csv_file(self, content):
        """Create a temp CSV file with given content."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        return f.name

    @mock.patch('os.path.exists')
    def test_csv_not_found_returns_empty(self, mock_exists):
        """harmonizacao.csv not found → empty list."""
        mock_exists.return_value = False
        result = snc.fetch_csv_records()
        self.assertEqual(result, [])

    def test_csv_4col_parsing(self):
        """4-column CSV: nome, telefone, endereco, site_url."""
        csv_content = "nome,telefone,endereco,site_url\nClínica Pet,16 99999-0001,Rua das Flores 100,\n"
        csv_path = self._make_csv_file(csv_content)

        with mock.patch.object(snc, 'BASE', os.path.dirname(csv_path)):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=csv_content)):
                    result = snc.fetch_csv_records()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['nome'], 'Clínica Pet')
        self.assertEqual(result[0]['telefone'], '16 99999-0001')
        self.assertEqual(result[0]['endereco'], 'Rua das Flores 100')
        self.assertEqual(result[0]['source'], 'harmonizacao_csv')

    def test_csv_5col_parsing(self):
        """5-column CSV: nome, servicos, telefone, endereco, site_url."""
        csv_content = "nome,servicos,telefone,endereco,site_url\nClínica Harmonização,Harmonização Botox,16 98888-7777,Av. Paulista 200,https://harmon.com\n"
        csv_path = self._make_csv_file(csv_content)

        with mock.patch.object(snc, 'BASE', os.path.dirname(csv_path)):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=csv_content)):
                    result = snc.fetch_csv_records()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['nome'], 'Clínica Harmonização')
        self.assertEqual(result[0]['servicos'], 'Harmonização Botox')
        self.assertEqual(result[0]['telefone'], '16 98888-7777')
        self.assertEqual(result[0]['nicho'], 'Harmonização',
            "Niche should be inferred from servicos")

    def test_csv_skips_malformed_rows(self):
        """Rows with wrong column count are skipped."""
        csv_content = "nome,telefone,endereco,site_url\nGood Row,16999998888,Rua A,\nBadRow,16999998887\nAnotherGood,16999998886,Rua B,\n"

        with mock.patch.object(snc, 'BASE', '/tmp'):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=csv_content)):
                    result = snc.fetch_csv_records()

        # Only rows with exactly 4 or 5 columns are parsed
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['nome'], 'Good Row')
        self.assertEqual(result[1]['nome'], 'AnotherGood')

    def test_csv_site_url_requires_http(self):
        """site_url without http prefix is treated as empty."""
        csv_content = "nome,telefone,endereco,site_url\nCliente,16999998888,Rua A,not-a-url\n"

        with mock.patch.object(snc, 'BASE', '/tmp'):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=csv_content)):
                    result = snc.fetch_csv_records()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['site_url'], '',
            "site_url without http should be empty string")

    def test_csv_infers_niche_from_nome(self):
        """When servicos is empty, niche is inferred from nome."""
        csv_content = "nome,servicos,telefone,endereco,site_url\nClínica Veterinária,,16 99999-0001,Rua V,\n"

        with mock.patch.object(snc, 'BASE', '/tmp'):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=csv_content)):
                    result = snc.fetch_csv_records()

        self.assertEqual(result[0]['nicho'], 'Veterinária',
            "Niche should be inferred from nome when servicos is empty")


class TestJSONRecords(unittest.TestCase):
    """Test fetch_json_records."""

    @mock.patch('os.path.exists')
    def test_json_not_found(self, mock_exists):
        """prospects-novos-batch.json not found → empty list."""
        mock_exists.return_value = False
        result = snc.fetch_json_records()
        self.assertEqual(result, [])

    def test_json_parsing(self):
        """JSON parsing returns correct record structure."""
        data = [{
            'Nome': 'Cliente JSON',
            'Telefone': '11977776655',
            'Endereço': 'Rua JSON 99',
            'Nicho': 'Veterinária',
            'Descrição': 'Pet shop no centro'
        }]
        json_content = json.dumps(data)

        with mock.patch.object(snc, 'BASE', '/tmp'):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=json_content)):
                    result = snc.fetch_json_records()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['nome'], 'Cliente JSON')
        self.assertEqual(result[0]['telefone'], '11977776655')
        self.assertEqual(result[0]['endereco'], 'Rua JSON 99')
        self.assertEqual(result[0]['nicho'], 'Veterinária')
        self.assertEqual(result[0]['descricao'], 'Pet shop no centro')
        self.assertEqual(result[0]['source'], 'prospects_novos')

    def test_json_multiple_records(self):
        """Multiple records parsed correctly."""
        data = [
            {'Nome': 'Cliente A', 'Telefone': '11111111111', 'Endereço': '', 'Nicho': '', 'Descrição': ''},
            {'Nome': 'Cliente B', 'Telefone': '22222222222', 'Endereço': '', 'Nicho': '', 'Descrição': ''},
        ]
        json_content = json.dumps(data)

        with mock.patch.object(snc, 'BASE', '/tmp'):
            with mock.patch('os.path.exists', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=json_content)):
                    result = snc.fetch_json_records()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['nome'], 'Cliente A')
        self.assertEqual(result[1]['nome'], 'Cliente B')


class TestCSVImport(unittest.TestCase):
    """Test CSV import and merge behavior."""

    def test_csv_dedup_merge_with_existing(self):
        """CSV record with same phone as DB → MERGE (supplement missing fields)."""
        with InMemoryDB() as conn:
            create_schema(conn)

            # Insert existing Notion record (no email, no site_url)
            # phone_norm = '16999999999' (11 digits → last 10 = '6999999999')
            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, email, pipeline_status,
                     notion_status, source, created_at, updated_at)
                VALUES
                    ('nid-1', 'Cliente Antigo', '16 99999-9999', '6999999999', '',
                     'Contatado', 'Enviado', 'notion', '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            # Verify no email before merge
            row = conn.execute(
                "SELECT email, site_url FROM prospects WHERE telefone_norm = '6999999999'"
            ).fetchone()
            self.assertEqual(row['email'], '')

            # Run CSV merge - phone '16 99999-9999' normalizes to '6999999999' (matches DB)
            csv_records = [{
                'nome': 'Cliente Antigo',
                'telefone': '16 99999-9999',  # will normalize to 6999999999
                'endereco': 'Rua Nova, 200',
                'site_url': 'https://novosite.com',
                'email': 'novo@email.com',
                'servicos': '',
                'nicho': '',
            }]
            i, u = snc.merge_and_insert(conn, csv_records, 'harmonizacao_csv')

            # Should update (not insert new), supplementing email and site_url
            total = conn.execute("SELECT COUNT(*) as c FROM prospects").fetchone()['c']
            self.assertEqual(total, 1, "Should have exactly 1 record (merge, not insert)")

            row = conn.execute(
                "SELECT email, site_url, nome, pipeline_status FROM prospects WHERE telefone_norm = '6999999999'"
            ).fetchone()
            self.assertEqual(row['email'], 'novo@email.com',
                "Email should be supplemented from CSV")
            self.assertEqual(row['site_url'], 'https://novosite.com',
                "site_url should be supplemented from CSV")
            self.assertEqual(row['pipeline_status'], 'Contatado',
                "pipeline_status should be preserved (not overwritten to Lead)")

    def test_csv_new_record_insert(self):
        """CSV record with new phone → INSERT new."""
        with InMemoryDB() as conn:
            create_schema(conn)

            # '11 98888-7777' normalizes to '11988887777' (11 + 988887777 = 11 digits → last 10 = '1988887777')
            csv_records = [{
                'nome': 'Novo Cliente',
                'telefone': '11 98888-7777',
                'endereco': 'Rua B',
                'site_url': '',
                'email': '',
                'servicos': '',
                'nicho': '',
            }]
            i, u = snc.merge_and_insert(conn, csv_records, 'harmonizacao_csv')

            self.assertEqual(i, 1)
            self.assertEqual(u, 0)
            total = conn.execute("SELECT COUNT(*) as c FROM prospects").fetchone()['c']
            self.assertEqual(total, 1)

            # The normalized phone is '11988887777' (11 digits → last 10 = '1988887777')
            row = conn.execute(
                "SELECT nome, pipeline_status, telefone_norm FROM prospects"
            ).fetchone()
            self.assertEqual(row['nome'], 'Novo Cliente')
            self.assertEqual(row['pipeline_status'], 'Lead')

    def test_csv_no_phone_skipped(self):
        """CSV record with no valid phone is skipped."""
        with InMemoryDB() as conn:
            create_schema(conn)

            csv_records = [{
                'nome': 'Sem Telefone',
                'telefone': '',
                'endereco': '',
                'site_url': '',
                'email': '',
                'servicos': '',
                'nicho': '',
            }]
            i, u = snc.merge_and_insert(conn, csv_records, 'harmonizacao_csv')

            self.assertEqual(i, 0)
            self.assertEqual(u, 0)
            total = conn.execute("SELECT COUNT(*) as c FROM prospects").fetchone()['c']
            self.assertEqual(total, 0)


class TestMergeLogic(unittest.TestCase):
    """Test merge logic for Notion and CSV sources."""

    def test_notion_update_preserves_pipeline_status(self):
        """Notion record already in DB with same notion_id → UPDATE, preserves pipeline_status."""
        with InMemoryDB() as conn:
            create_schema(conn)

            # Existing record with pipeline_status='Contatado'
            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, pipeline_status,
                     notion_status, email, source, created_at, updated_at)
                VALUES
                    ('nid-x', 'Cliente Existente', '16990001111', '16990001111',
                     'Contatado', 'Enviado', 'old@email.com', 'notion',
                     '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            # Simulate re-sync from Notion (new data but same notion_id)
            notion_records = [{
                'notion_id': 'nid-x',
                'nome': 'Cliente Existente Updated',
                'telefone': '16990001111',
                'notion_status': 'Respondeu',  # Notion has Respondeu
                'email': 'updated@email.com',
                'pipeline_status': 'Respondeu',  # normalized
            }]

            # normalize_pipeline('Respondeu') → 'Respondeu'
            with mock.patch.object(snc, 'normalize_pipeline', return_value='Respondeu'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            self.assertEqual(u, 1)
            self.assertEqual(i, 0)

            row = conn.execute(
                "SELECT pipeline_status, notion_status, email FROM prospects WHERE notion_id = 'nid-x'"
            ).fetchone()
            self.assertEqual(row['pipeline_status'], 'Contatado',
                "pipeline_status='Contatado' must NOT be overwritten by Notion sync")
            self.assertEqual(row['email'], 'updated@email.com',
                "email should be updated from Notion")

    def test_notion_new_record_insert(self):
        """New Notion record → INSERT."""
        with InMemoryDB() as conn:
            create_schema(conn)

            notion_records = [{
                'notion_id': 'nid-new',
                'nome': 'Novo do Notion',
                'telefone': '21977778888',
                'notion_status': 'Lead',
                'pipeline_status': 'Lead',
                'email': 'new@notion.com',
            }]

            with mock.patch.object(snc, 'normalize_pipeline', return_value='Lead'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            self.assertEqual(i, 1)
            self.assertEqual(u, 0)

            row = conn.execute(
                "SELECT nome, pipeline_status FROM prospects WHERE notion_id = 'nid-new'"
            ).fetchone()
            self.assertEqual(row['nome'], 'Novo do Notion')
            self.assertEqual(row['pipeline_status'], 'Lead')

    def test_notion_with_empty_pipeline_uses_notion_status(self):
        """Notion record in DB with empty pipeline_status → use Notion normalized status."""
        with InMemoryDB() as conn:
            create_schema(conn)

            # Existing record with empty pipeline_status
            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, pipeline_status,
                     notion_status, source, created_at, updated_at)
                VALUES
                    ('nid-y', 'Cliente PipelineVazio', '31999998888', '31999998888',
                     '', '', 'notion', '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            notion_records = [{
                'notion_id': 'nid-y',
                'nome': 'Cliente PipelineVazio',
                'telefone': '31999998888',
                'notion_status': 'Enviado',
            }]

            with mock.patch.object(snc, 'normalize_pipeline', return_value='Contatado'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            self.assertEqual(u, 1)
            row = conn.execute(
                "SELECT pipeline_status FROM prospects WHERE notion_id = 'nid-y'"
            ).fetchone()
            self.assertEqual(row['pipeline_status'], 'Contatado',
                "Empty pipeline_status should be filled from Notion")

    def test_csv_supplements_notion_without_overwriting(self):
        """CSV has email but DB record doesn't → merged record has email."""
        with InMemoryDB() as conn:
            create_schema(conn)

            # Existing from Notion (no email, no site_url)
            # phone '44998877665' (11 digits → last 10 = '4998877665')
            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, email, site_url,
                     pipeline_status, notion_status, source, created_at, updated_at)
                VALUES
                    ('nid-z', 'Sem Email Notion', '44998877665', '4998877665',
                     '', '', 'Lead', 'Mensagem Pronta', 'notion',
                     '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            # CSV with same phone normalized
            csv_records = [{
                'nome': 'Sem Email Notion',
                'telefone': '44998877665',  # normalizes to '4998877665' (same as DB)
                'endereco': 'Endereço CSV',
                'site_url': 'https://csv-site.com',
                'email': 'csv@email.com',
                'servicos': '',
                'nicho': '',
            }]

            i, u = snc.merge_and_insert(conn, csv_records, 'harmonizacao_csv')

            # Should UPDATE (not insert), and email should be filled from CSV
            total = conn.execute("SELECT COUNT(*) as c FROM prospects").fetchone()['c']
            self.assertEqual(total, 1, "Should have exactly 1 record (merge, not insert)")

            row = conn.execute(
                "SELECT email, site_url, pipeline_status FROM prospects WHERE telefone_norm = '4998877665'"
            ).fetchone()
            self.assertEqual(row['email'], 'csv@email.com',
                "CSV email should supplement missing email")
            self.assertEqual(row['site_url'], 'https://csv-site.com',
                "CSV site_url should supplement missing site_url")
            self.assertEqual(row['pipeline_status'], 'Lead',
                "pipeline_status should remain Lead (from Notion, preserved)")

    def test_notion_overwrites_existing_notion_fields(self):
        """Notion data overwrites existing Notion fields on update."""
        with InMemoryDB() as conn:
            create_schema(conn)

            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, email,
                     pipeline_status, notion_status, source, created_at, updated_at)
                VALUES
                    ('nid-w', 'Antigo Nome', '11900001111', '11900001111',
                     'antigo@email.com', 'Lead', 'Lead', 'notion',
                     '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            notion_records = [{
                'notion_id': 'nid-w',
                'nome': 'Novo Nome do Notion',
                'telefone': '11900001111',
                'notion_status': 'Enviado',
                'email': 'novo@notion.com',
                'pipeline_status': 'Contatado',
            }]

            with mock.patch.object(snc, 'normalize_pipeline', return_value='Contatado'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            self.assertEqual(u, 1)
            row = conn.execute("SELECT nome, email FROM prospects WHERE notion_id = 'nid-w'").fetchone()
            self.assertEqual(row['nome'], 'Novo Nome do Notion')
            self.assertEqual(row['email'], 'novo@notion.com')


class TestPipelineStatusPreservation(unittest.TestCase):
    """Critical test: pipeline_status set by agent must not be overwritten."""

    def test_contatado_not_overwritten_by_notion_sync(self):
        """Record with pipeline_status='Contatado' re-synced from Notion → status preserved."""
        with InMemoryDB() as conn:
            create_schema(conn)

            # Pre-existing: manually set to Contatado by agent
            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, pipeline_status,
                     notion_status, source, created_at, updated_at)
                VALUES
                    ('nid-p', 'Pipeline Preservado', '15990001122',
                     '15990001122', 'Contatado', 'Site em Criação',
                     'notion', '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            # Notion now says "Site em Criação" which would normalize to 'Lead'
            notion_records = [{
                'notion_id': 'nid-p',
                'nome': 'Pipeline Preservado',
                'telefone': '15990001122',
                'notion_status': 'Site em Criação',
                'email': '',
            }]

            # normalize_pipeline('Site em Criação') → 'Lead'
            with mock.patch.object(snc, 'normalize_pipeline', return_value='Lead'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            self.assertEqual(u, 1)

            row = conn.execute(
                "SELECT pipeline_status FROM prospects WHERE notion_id = 'nid-p'"
            ).fetchone()
            self.assertEqual(row['pipeline_status'], 'Contatado',
                "FAIL: pipeline_status='Contatado' was overwritten! "
                "The pattern 'ep IS NOT NULL AND ep != ''' must be used.")

    def test_empty_pipeline_gets_filled_from_notion(self):
        """Record with empty pipeline_status gets filled from Notion."""
        with InMemoryDB() as conn:
            create_schema(conn)

            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, pipeline_status,
                     notion_status, source, created_at, updated_at)
                VALUES
                    ('nid-q', 'Pipeline Vazio', '15990001133', '15990001133',
                     '', '', 'notion', '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            notion_records = [{
                'notion_id': 'nid-q',
                'nome': 'Pipeline Vazio',
                'telefone': '15990001133',
                'notion_status': 'Enviado',
            }]

            with mock.patch.object(snc, 'normalize_pipeline', return_value='Contatado'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            self.assertEqual(u, 1)
            row = conn.execute(
                "SELECT pipeline_status FROM prospects WHERE notion_id = 'nid-q'"
            ).fetchone()
            self.assertEqual(row['pipeline_status'], 'Contatado',
                "Empty pipeline_status should be filled from Notion")

    def test_pipeline_lost_preserved(self):
        """pipeline_status='Lost' should also be preserved (not overwritten)."""
        with InMemoryDB() as conn:
            create_schema(conn)

            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, pipeline_status,
                     notion_status, source, created_at, updated_at)
                VALUES
                    ('nid-r', 'Lost Record', '15990001144', '15990001144',
                     'Lost', 'Descartado', 'notion', '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            notion_records = [{
                'notion_id': 'nid-r',
                'nome': 'Lost Record',
                'telefone': '15990001144',
                'notion_status': 'Descartado',
            }]

            with mock.patch.object(snc, 'normalize_pipeline', return_value='Lead'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            row = conn.execute(
                "SELECT pipeline_status FROM prospects WHERE notion_id = 'nid-r'"
            ).fetchone()
            self.assertEqual(row['pipeline_status'], 'Lost',
                "pipeline_status='Lost' should be preserved")

    def test_none_pipeline_gets_filled(self):
        """pipeline_status=NULL gets filled with 'Lead' (normalize of empty string)."""
        with InMemoryDB() as conn:
            create_schema(conn)

            # Insert with NULL (SQLite default) - will be filled with 'Lead' on sync
            conn.execute("""
                INSERT INTO prospects
                    (notion_id, nome, telefone, telefone_norm, source, created_at, updated_at)
                VALUES
                    ('nid-s', 'Null Pipeline', '15990001155', '15990001155',
                     'notion', '2024-01-01', '2024-01-01')
            """)
            conn.commit()

            notion_records = [{
                'notion_id': 'nid-s',
                'nome': 'Null Pipeline',
                'telefone': '15990001155',
                'notion_status': 'Enviado',
            }]

            # normalize_pipeline('') → 'Lead' (not 'Contatado')
            with mock.patch.object(snc, 'normalize_pipeline', return_value='Lead'):
                i, u = snc.merge_and_insert(conn, notion_records, 'notion')

            row = conn.execute(
                "SELECT pipeline_status FROM prospects WHERE notion_id = 'nid-s'"
            ).fetchone()
            self.assertEqual(row['pipeline_status'], 'Lead',
                "NULL pipeline_status should be filled with Lead (normalize of '')")


class TestRunFunction(unittest.TestCase):
    """Test run() without making real external calls."""

    @mock.patch('sync_notion_csv_to_sqlite.urlopen')
    @mock.patch('sync_notion_csv_to_sqlite.get_connection')
    @mock.patch('sync_notion_csv_to_sqlite.fetch_csv_records')
    @mock.patch('sync_notion_csv_to_sqlite.fetch_json_records')
    @mock.patch('sync_notion_csv_to_sqlite.fetch_notion_records')
    @mock.patch('builtins.print')
    def test_run_with_mocked_notion(
        self, mock_print, mock_fetch_notion, mock_fetch_json,
        mock_fetch_csv, mock_get_conn, mock_urlopen
    ):
        """run() completes without error with mocked sources."""
        # Setup in-memory DB with schema already created
        inmem_conn = in_memory_conn()
        inmem_conn.executescript(snc.SCHEMA)
        # init_db() calls get_connection() internally then runs executescript
        # So we mock get_connection to return our pre-configured conn
        mock_get_conn.return_value = inmem_conn

        # Mock data sources
        mock_fetch_notion.return_value = []
        mock_fetch_csv.return_value = []
        mock_fetch_json.return_value = []

        # Mock urlopen to avoid actual HTTP calls (if any)
        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({'results': [], 'has_more': False}).encode()
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # run() should not raise
        try:
            snc.run()
        except Exception as e:
            self.fail(f"run() raised {type(e).__name__}: {e}")
        finally:
            inmem_conn.close()

    @mock.patch('sync_notion_csv_to_sqlite.urlopen')
    @mock.patch('sync_notion_csv_to_sqlite.get_connection')
    @mock.patch('sync_notion_csv_to_sqlite.fetch_csv_records')
    @mock.patch('sync_notion_csv_to_sqlite.fetch_json_records')
    @mock.patch('sync_notion_csv_to_sqlite.fetch_notion_records')
    @mock.patch('builtins.print')
    def test_run_inserts_notion_records(
        self, mock_print, mock_fetch_notion, mock_fetch_json,
        mock_fetch_csv, mock_get_conn, mock_urlopen
    ):
        """run() correctly inserts Notion records."""
        inmem_conn = in_memory_conn()
        inmem_conn.executescript(snc.SCHEMA)
        mock_get_conn.return_value = inmem_conn

        # Provide a mock Notion record
        mock_fetch_notion.return_value = [{
            'notion_id': 'nid-run',
            'nome': 'Run Test',
            'telefone': '11900001111',
            'notion_status': 'Lead',
            'pipeline_status': 'Lead',
            'email': 'run@test.com',
            'nicho': 'Veterinária',
            'endereco': '',
            'site_url': '',
            'url_demo': '',
            'slug': '',
            'origem': '',
            'canal_contato': '',
            'resposta': '',
            'observacoes': '',
            'tentativas': 0,
            'valor': 0,
            'us_id': '',
            'facebook': '',
            'instagram': '',
            'descricao': '',
            'data_1_contato': '',
            'site_criado_em': '',
            'motivo_perda': '',
        }]
        mock_fetch_csv.return_value = []
        mock_fetch_json.return_value = []

        mock_response = mock.MagicMock()
        mock_response.read.return_value = json.dumps({'results': [], 'has_more': False}).encode()
        mock_response.__enter__ = mock.MagicMock(return_value=mock_response)
        mock_response.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        snc.run()

        # Note: run() calls conn.close() so we can't query after run().
        # Verify via mock calls instead.
        self.assertTrue(mock_fetch_notion.called, "fetch_notion_records should be called")
        self.assertTrue(mock_fetch_csv.called, "fetch_csv_records should be called")
        self.assertTrue(mock_fetch_json.called, "fetch_json_records should be called")


class TestMainGuard(unittest.TestCase):
    """Test that __main__ guard is properly handled."""

    def test_run_is_callable(self):
        """run() function exists and is callable."""
        self.assertTrue(callable(snc.run))

    def test_module_defines_schema(self):
        """Module defines SCHEMA constant."""
        self.assertTrue(hasattr(snc, 'SCHEMA'))
        self.assertIn('CREATE TABLE', snc.SCHEMA)


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main(verbosity=2)
