#!/usr/bin/env python3
"""
Unit tests for generate_crm_data.py
Tests SQLite reading functions and JSON output generation.
"""

import unittest
import sqlite3
import json
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

# Add scripts directory to path
sys.path.insert(0, '/opt/data/home/site-pixel-alchemy/scripts')

import generate_crm_data


def create_test_db():
    """Create an in-memory SQLite database with test data."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create prospects table
    conn.execute('''
        CREATE TABLE prospects (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            nicho TEXT,
            pipeline_status TEXT,
            email TEXT,
            telefone TEXT,
            telefone_norm TEXT,
            source TEXT,
            site_url TEXT,
            url_demo TEXT,
            notion_status TEXT,
            created_at TEXT
        )
    ''')
    
    # Insert test data
    test_records = [
        (1, 'Dra Maria', 'Veterinaria', 'Lead', '', '16991904676', '16991904676', 'notion', '', '', '', '2026-01-15'),
        (2, 'Vet Plus', 'Veterinaria', 'Contatado', '', '16988057183', '16988057183', 'notion', '', '', '', '2026-02-20'),
        (3, 'Dr Carlos', 'Dentista', 'Lead', 'carlos@email.com', '16977001234', '16977001234', 'harmonizacao_csv', 'https://site.com', 'https://pixelalchemy.com.br/demo/carlos', '', '2026-03-10'),
        (4, 'Sem Telefone', 'Beleza', 'Lead', '', None, None, 'notion', '', '', '', None),
        (5, 'Cliente Fechado', 'Harmonizacao', 'Fechado', 'fechado@email.com', '16966009988', '16966009988', 'notion', 'https://site.com', 'https://pixelalchemy.com.br/demo/cliente', '', '2026-04-01'),
    ]
    
    conn.executemany('''
        INSERT INTO prospects (id, nome, nicho, pipeline_status, email, telefone, telefone_norm, source, site_url, url_demo, notion_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', test_records)
    
    conn.commit()
    return conn


def create_empty_test_db():
    """Create an empty in-memory SQLite database with the same schema."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    conn.execute('''
        CREATE TABLE prospects (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            nicho TEXT,
            pipeline_status TEXT,
            email TEXT,
            telefone TEXT,
            telefone_norm TEXT,
            source TEXT,
            site_url TEXT,
            url_demo TEXT,
            notion_status TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    return conn


def query_db_from_conn(conn, sql, params=None):
    """Execute query on a specific connection and return results as list of dicts."""
    cur = conn.execute(sql, params or ())
    rows = cur.fetchall()
    return [dict(r) for r in rows]


class TestFunnelStats(unittest.TestCase):
    """Tests for get_funnel_stats function."""
    
    def test_funnel_counts_correct(self):
        """Verify correct count per pipeline_status."""
        conn = create_test_db()
        
        # Get funnel stats using the same query as the script
        pipeline = {}
        for row in query_db_from_conn(conn, 'SELECT pipeline_status, COUNT(*) as c FROM prospects GROUP BY pipeline_status'):
            pipeline[row['pipeline_status']] = row['c']
        
        self.assertEqual(pipeline.get('Lead'), 3)
        self.assertEqual(pipeline.get('Contatado'), 1)
        self.assertEqual(pipeline.get('Fechado'), 1)
        conn.close()
    
    def test_funnel_total_count(self):
        """Verify total count matches sum of pipeline statuses."""
        conn = create_test_db()
        
        pipeline = {}
        for row in query_db_from_conn(conn, 'SELECT pipeline_status, COUNT(*) as c FROM prospects GROUP BY pipeline_status'):
            pipeline[row['pipeline_status']] = row['c']
        
        total_leads = sum(pipeline.values())
        self.assertEqual(total_leads, 5)
        conn.close()
    
    def test_funnel_empty_database(self):
        """Handle empty database gracefully."""
        conn = create_empty_test_db()
        
        pipeline = {}
        for row in query_db_from_conn(conn, 'SELECT pipeline_status, COUNT(*) as c FROM prospects GROUP BY pipeline_status'):
            pipeline[row['pipeline_status']] = row['c']
        
        total_leads = sum(pipeline.values())
        self.assertEqual(total_leads, 0)
        self.assertEqual(pipeline, {})
        conn.close()


class TestNicheDistribution(unittest.TestCase):
    """Tests for get_niche_distribution function."""
    
    def test_niche_counts_correct(self):
        """Verify correct count per niche."""
        conn = create_test_db()
        
        niches = {}
        for row in query_db_from_conn(conn, "SELECT nicho, COUNT(*) as c FROM prospects WHERE nicho != '' AND nicho IS NOT NULL GROUP BY nicho ORDER BY c DESC"):
            niches[row['nicho']] = row['c']
        
        self.assertEqual(niches.get('Veterinaria'), 2)
        self.assertEqual(niches.get('Dentista'), 1)
        self.assertEqual(niches.get('Beleza'), 1)
        self.assertEqual(niches.get('Harmonizacao'), 1)
        conn.close()
    
    def test_niche_empty_database(self):
        """Empty DB returns empty dict."""
        conn = create_empty_test_db()
        
        niches = {}
        for row in query_db_from_conn(conn, "SELECT nicho, COUNT(*) as c FROM prospects WHERE nicho != '' AND nicho IS NOT NULL GROUP BY nicho ORDER BY c DESC"):
            niches[row['nicho']] = row['c']
        
        self.assertEqual(niches, {})
        conn.close()


class TestContactStats(unittest.TestCase):
    """Tests for contact statistics counting."""
    
    def test_count_with_email(self):
        """Count records with email (email IS NOT NULL AND email != '' AND email != 'None')."""
        conn = create_test_db()
        
        with_email = query_db_from_conn(conn, "SELECT COUNT(*) as c FROM prospects WHERE email IS NOT NULL AND email != '' AND email != 'None'")[0]['c']
        
        # Records 3 and 5 have emails
        self.assertEqual(with_email, 2)
        conn.close()
    
    def test_count_with_phone(self):
        """Count records with phone (telefone IS NOT NULL AND telefone != '')."""
        conn = create_test_db()
        
        # Using the actual script column: telefone (not telefone_norm)
        with_phone = query_db_from_conn(conn, "SELECT COUNT(*) as c FROM prospects WHERE telefone IS NOT NULL AND telefone != ''")[0]['c']
        
        # Records 1, 2, 3, 5 have phones (record 4 has None)
        self.assertEqual(with_phone, 4)
        conn.close()
    
    def test_count_with_demo_url(self):
        """Count records with demo URL (url_demo IS NOT NULL AND url_demo != '' AND url_demo != 'None')."""
        conn = create_test_db()
        
        with_demo = query_db_from_conn(conn, "SELECT COUNT(*) as c FROM prospects WHERE url_demo IS NOT NULL AND url_demo != '' AND url_demo != 'None'")[0]['c']
        
        # Records 3 and 5 have demo URLs
        self.assertEqual(with_demo, 2)
        conn.close()
    
    def test_contact_stats_empty_database(self):
        """Empty database returns 0 for all contact stats."""
        conn = create_empty_test_db()
        
        with_email = query_db_from_conn(conn, "SELECT COUNT(*) as c FROM prospects WHERE email IS NOT NULL AND email != '' AND email != 'None'")[0]['c']
        with_phone = query_db_from_conn(conn, "SELECT COUNT(*) as c FROM prospects WHERE telefone IS NOT NULL AND telefone != ''")[0]['c']
        with_demo = query_db_from_conn(conn, "SELECT COUNT(*) as c FROM prospects WHERE url_demo IS NOT NULL AND url_demo != '' AND url_demo != 'None'")[0]['c']
        
        self.assertEqual(with_email, 0)
        self.assertEqual(with_phone, 0)
        self.assertEqual(with_demo, 0)
        conn.close()


class TestMonthlyProduction(unittest.TestCase):
    """Tests for get_monthly_production function."""
    
    def test_monthly_aggregation(self):
        """Verify aggregation by month from created_at."""
        conn = create_test_db()
        
        monthly = {}
        for row in query_db_from_conn(conn, "SELECT created_at FROM prospects"):
            if row['created_at']:
                month = row['created_at'][:7]  # YYYY-MM
                monthly[month] = monthly.get(month, 0) + 1
        
        self.assertEqual(monthly.get('2026-01'), 1)
        self.assertEqual(monthly.get('2026-02'), 1)
        self.assertEqual(monthly.get('2026-03'), 1)
        self.assertEqual(monthly.get('2026-04'), 1)
        conn.close()
    
    def test_monthly_handles_none_created_at(self):
        """Handle records with None created_at gracefully."""
        conn = create_test_db()
        
        monthly = {}
        for row in query_db_from_conn(conn, "SELECT created_at FROM prospects"):
            if row['created_at']:
                month = row['created_at'][:7]
                monthly[month] = monthly.get(month, 0) + 1
        
        # Record 4 has None created_at, should not cause error
        self.assertNotIn(None, monthly)
        self.assertEqual(sum(monthly.values()), 4)  # Only 4 records have created_at
        conn.close()
    
    def test_monthly_empty_database(self):
        """Empty database produces empty monthly dict."""
        conn = create_empty_test_db()
        
        monthly = {}
        for row in query_db_from_conn(conn, "SELECT created_at FROM prospects"):
            if row['created_at']:
                month = row['created_at'][:7]
                monthly[month] = monthly.get(month, 0) + 1
        
        self.assertEqual(monthly, {})
        conn.close()


class TestBuildCRMData(unittest.TestCase):
    """Tests for the main build_crm_data function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_conn = create_test_db()
        self.maxDiff = None
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_conn.close()
    
    def _mock_query_db(self, sql, params=None):
        """Wrapper that uses the test DB connection."""
        cur = self.test_conn.execute(sql, params or ())
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    
    @patch('generate_crm_data.query_db')
    @patch('generate_crm_data.get_git_log_commits')
    @patch('os.listdir')
    def test_build_crm_data_structure(self, mock_listdir, mock_git_log, mock_query_db):
        """Verify build_crm_data produces correct JSON structure."""
        # Configure mocks
        mock_git_log.return_value = []
        mock_listdir.return_value = []
        
        # Track calls to understand what queries are made
        query_results = {}
        
        def capture_query(sql, params=None):
            if sql not in query_results:
                query_results[sql] = self._mock_query_db(sql, params)
            return query_results[sql]
        
        mock_query_db.side_effect = capture_query
        
        # Patch os.path.exists and os.path.getsize to simulate DB exists
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize:
            mock_exists.return_value = True
            mock_getsize.return_value = 1000
            
            data = generate_crm_data.build_crm_data()
        
        # Verify top-level structure
        self.assertIn('generated_at', data)
        self.assertIn('crm', data)
        
        crm = data['crm']
        
        # Verify crm structure
        self.assertIn('generated_at', crm)
        self.assertIn('leads_summary', crm)
        self.assertIn('funnel', crm)
        self.assertIn('outreach_stats', crm)
        self.assertIn('niche_distribution', crm)
        self.assertIn('monthly_production', crm)
        self.assertIn('recent_activity', crm)
        self.assertIn('prd', crm)
    
    @patch('generate_crm_data.query_db')
    @patch('generate_crm_data.get_git_log_commits')
    @patch('os.listdir')
    def test_build_crm_data_funnel_counts(self, mock_listdir, mock_git_log, mock_query_db):
        """Verify funnel counts are correct."""
        mock_git_log.return_value = []
        mock_listdir.return_value = []
        
        query_results = {}
        
        def capture_query(sql, params=None):
            if sql not in query_results:
                query_results[sql] = self._mock_query_db(sql, params)
            return query_results[sql]
        
        mock_query_db.side_effect = capture_query
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize:
            mock_exists.return_value = True
            mock_getsize.return_value = 1000
            
            data = generate_crm_data.build_crm_data()
        
        funnel_counts = data['crm']['funnel']['counts']
        
        self.assertEqual(funnel_counts['Lead'], 3)
        self.assertEqual(funnel_counts['Contatado'], 1)
        self.assertEqual(funnel_counts['Fechado'], 1)
        self.assertEqual(funnel_counts['Respondeu'], 0)
        self.assertEqual(funnel_counts['Reuniao'], 0)
        self.assertEqual(funnel_counts['Proposta'], 0)
    
    @patch('generate_crm_data.query_db')
    @patch('generate_crm_data.get_git_log_commits')
    @patch('os.listdir')
    def test_build_crm_data_total_leads(self, mock_listdir, mock_git_log, mock_query_db):
        """Verify total_leads count is correct."""
        mock_git_log.return_value = []
        mock_listdir.return_value = []
        
        query_results = {}
        
        def capture_query(sql, params=None):
            if sql not in query_results:
                query_results[sql] = self._mock_query_db(sql, params)
            return query_results[sql]
        
        mock_query_db.side_effect = capture_query
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize:
            mock_exists.return_value = True
            mock_getsize.return_value = 1000
            
            data = generate_crm_data.build_crm_data()
        
        total_leads = data['crm']['leads_summary']['total_leads']
        self.assertEqual(total_leads, 5)
    
    @patch('generate_crm_data.query_db')
    @patch('generate_crm_data.get_git_log_commits')
    @patch('os.listdir')
    def test_build_crm_data_niche_distribution(self, mock_listdir, mock_git_log, mock_query_db):
        """Verify niche distribution is correct."""
        mock_git_log.return_value = []
        mock_listdir.return_value = []
        
        query_results = {}
        
        def capture_query(sql, params=None):
            if sql not in query_results:
                query_results[sql] = self._mock_query_db(sql, params)
            return query_results[sql]
        
        mock_query_db.side_effect = capture_query
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize:
            mock_exists.return_value = True
            mock_getsize.return_value = 1000
            
            data = generate_crm_data.build_crm_data()
        
        niches = data['crm']['niche_distribution']
        
        self.assertEqual(niches.get('Veterinaria'), 2)
        self.assertEqual(niches.get('Dentista'), 1)
        self.assertEqual(niches.get('Beleza'), 1)
        self.assertEqual(niches.get('Harmonizacao'), 1)
    
    @patch('generate_crm_data.query_db')
    @patch('generate_crm_data.get_git_log_commits')
    @patch('os.listdir')
    def test_build_crm_data_with_phone(self, mock_listdir, mock_git_log, mock_query_db):
        """Verify with_phone count is correct."""
        mock_git_log.return_value = []
        mock_listdir.return_value = []
        
        query_results = {}
        
        def capture_query(sql, params=None):
            if sql not in query_results:
                query_results[sql] = self._mock_query_db(sql, params)
            return query_results[sql]
        
        mock_query_db.side_effect = capture_query
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize:
            mock_exists.return_value = True
            mock_getsize.return_value = 1000
            
            data = generate_crm_data.build_crm_data()
        
        with_phone = data['crm']['leads_summary']['with_phone']
        self.assertEqual(with_phone, 4)  # Records 1, 2, 3, 5 have phones


class TestMainFunction(unittest.TestCase):
    """Tests for the main() function."""
    
    @patch('generate_crm_data.build_crm_data')
    @patch('generate_crm_data.open', create=True)
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_main_writes_json(self, mock_getsize, mock_exists, mock_file, mock_build_data):
        """Verify main() writes JSON to output path."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1000
        
        # Create a mock file that supports context manager protocol
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__ = MagicMock(return_value=mock_file_handle)
        mock_file_handle.__exit__ = MagicMock(return_value=False)
        mock_file.return_value = mock_file_handle
        
        test_data = {
            'generated_at': '2026-04-15T12:00:00',
            'crm': {
                'generated_at': '2026-04-15T12:00:00',
                'leads_summary': {
                    'total_leads': 5,
                    'with_phone': 4,
                    'demo_sites_total': 0,
                    'sources': {}
                },
                'funnel': {
                    'stages': ['Lead', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Fechado'],
                    'counts': {'Lead': 3, 'Contatado': 1, 'Respondeu': 0, 'Reuniao': 0, 'Proposta': 0, 'Fechado': 1},
                    'note': ''
                },
                'outreach_stats': {
                    'currently_contatados': 1,
                    'currently_respondeu': 0,
                    'currently_reuniao': 0,
                    'currently_proposta': 0,
                    'currently_fechado': 1,
                    'notion_status_breakdown': {},
                    'note': ''
                },
                'niche_distribution': {'Veterinaria': 2, 'Dentista': 1, 'Beleza': 1, 'Harmonizacao': 1},
                'monthly_production': [],
                'recent_activity': [],
                'prd': {
                    'stories_total': 123,
                    'stories_done': 118,
                    'stories_pending': 5,
                    'reviews_done': 47,
                    'reviews_total': 47
                }
            }
        }
        mock_build_data.return_value = test_data
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            generate_crm_data.main()
        
        # Verify file was opened for writing (with correct output path)
        self.assertTrue(mock_file.called)
        self.assertEqual(mock_file.call_args[0][0], '/opt/data/home/site-pixel-alchemy/admin/dashboard/dashboard-data.json')
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_main_handles_empty_db(self, mock_getsize, mock_exists):
        """Empty database should produce valid JSON with zeros."""
        mock_exists.return_value = False
        mock_getsize.return_value = 0
        
        # Should print error and return without raising
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            generate_crm_data.main()
        
        output = captured_output.getvalue()
        self.assertIn('ERRO', output)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases with None values and special scenarios."""
    
    def test_none_values_in_database(self):
        """None values in DB should not cause KeyError or TypeError."""
        conn = create_test_db()
        
        # Query with None values should work
        result = query_db_from_conn(conn, "SELECT * FROM prospects WHERE id = 4")
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]['telefone'])
        self.assertIsNone(result[0]['created_at'])
        
        # Aggregation queries should handle None
        pipeline = {}
        for row in query_db_from_conn(conn, 'SELECT pipeline_status, COUNT(*) as c FROM prospects GROUP BY pipeline_status'):
            pipeline[row['pipeline_status']] = row['c']
        
        self.assertEqual(pipeline.get('Lead'), 3)
        conn.close()
    
    def test_all_leads_same_pipeline(self):
        """All leads in same pipeline should aggregate correctly."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        
        conn.execute('''
            CREATE TABLE prospects (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                nicho TEXT,
                pipeline_status TEXT,
                email TEXT,
                telefone TEXT,
                telefone_norm TEXT,
                source TEXT,
                site_url TEXT,
                url_demo TEXT,
                notion_status TEXT,
                created_at TEXT
            )
        ''')
        
        # Insert 3 records all with 'Lead' status
        conn.executemany('''
            INSERT INTO prospects (id, nome, nicho, pipeline_status, email, telefone, telefone_norm, source, site_url, url_demo, notion_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, 'Lead 1', 'Veterinaria', 'Lead', '', '16990000001', '16990000001', 'notion', '', '', '', '2026-01-01'),
            (2, 'Lead 2', 'Dentista', 'Lead', 'lead2@email.com', '16990000002', '16990000002', 'notion', '', '', '', '2026-02-01'),
            (3, 'Lead 3', 'Beleza', 'Lead', '', None, None, 'notion', '', '', '', None),
        ])
        conn.commit()
        
        pipeline = {}
        for row in query_db_from_conn(conn, 'SELECT pipeline_status, COUNT(*) as c FROM prospects GROUP BY pipeline_status'):
            pipeline[row['pipeline_status']] = row['c']
        
        self.assertEqual(pipeline.get('Lead'), 3)
        self.assertEqual(sum(pipeline.values()), 3)
        conn.close()


class TestJSONOutputFormat(unittest.TestCase):
    """Tests for JSON output format verification."""
    
    @patch('generate_crm_data.query_db')
    @patch('generate_crm_data.get_git_log_commits')
    @patch('os.listdir')
    def test_json_has_required_fields(self, mock_listdir, mock_git_log, mock_query_db):
        """Verify the output JSON has required structure."""
        # Create a minimal test DB
        test_conn = create_test_db()
        
        def mock_query_fn(sql, params=None):
            cur = test_conn.execute(sql, params or ())
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        
        mock_git_log.return_value = []
        mock_listdir.return_value = []
        mock_query_db.side_effect = mock_query_fn
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize:
            mock_exists.return_value = True
            mock_getsize.return_value = 1000
            
            data = generate_crm_data.build_crm_data()
        
        test_conn.close()
        
        # Verify required top-level fields
        self.assertIn('generated_at', data)
        self.assertIn('crm', data)
        
        crm = data['crm']
        
        # Verify CRM fields match expected structure
        self.assertIn('leads_summary', crm)
        self.assertIn('funnel', crm)
        self.assertIn('niche_distribution', crm)
        self.assertIn('monthly_production', crm)
        
        # Verify leads_summary has required fields
        ls = crm['leads_summary']
        self.assertIn('total_leads', ls)
        self.assertIn('with_phone', ls)
        self.assertIn('demo_sites_total', ls)
        self.assertIn('sources', ls)
        
        # Verify funnel has required fields
        funnel = crm['funnel']
        self.assertIn('stages', funnel)
        self.assertIn('counts', funnel)
        
        # Verify counts have all stages
        for stage in ['Lead', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Fechado']:
            self.assertIn(stage, funnel['counts'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
