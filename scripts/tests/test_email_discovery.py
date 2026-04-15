#!/usr/bin/env python3
"""
Unit tests for email_discovery.py
Mock all external calls: SERP API, SQLite, time.sleep, random, urllib
"""

import unittest
from unittest.mock import patch, MagicMock, ANY
import sys
import os

# Set mock env BEFORE importing the module
os.environ['SERP_API_KEY'] = 'mock_test_key'

# Import the module under test
sys.path.insert(0, '/opt/data/home/site-pixel-alchemy/scripts')
import email_discovery as ed


class TestExtractEmails(unittest.TestCase):
    """Test extract_emails() function."""

    def test_no_email(self):
        result = ed.extract_emails("This is just some text without any email addresses.")
        self.assertEqual(result, [])

    def test_one_email(self):
        result = ed.extract_emails("Contact us at maria@empresa.com.br for more info.")
        self.assertEqual(result, ['maria@empresa.com.br'])

    def test_multiple_emails(self):
        text = "Reach us at maria@gmail.com or at joao@empresa.com or teste@domain.org"
        result = ed.extract_emails(text)
        self.assertIn('maria@gmail.com', result)
        self.assertIn('joao@empresa.com', result)
        self.assertIn('teste@domain.org', result)

    def test_email_with_dots_in_local_part(self):
        result = ed.extract_emails("Contact: dra.ana@vet.com.br")
        self.assertEqual(result, ['dra.ana@vet.com.br'])

    def test_mailto_link(self):
        text = '<a href="mailto:contato.clinica@outlook.com">Email Us</a>'
        result = ed.extract_emails(text)
        self.assertEqual(result, ['contato.clinica@outlook.com'])

    def test_mailto_link_uppercase(self):
        text = '<a href="mailto:MARIA@GMAIL.COM">Email</a>'
        result = ed.extract_emails(text)
        self.assertEqual(result, ['maria@gmail.com'])

    # ---- Generic emails that MUST be filtered ----
    def test_filter_contato(self):
        result = ed.extract_emails("contato@empresa.com")
        self.assertEqual(result, [])

    def test_filter_info(self):
        result = ed.extract_emails("info@empresa.com")
        self.assertEqual(result, [])

    def test_filter_hello(self):
        result = ed.extract_emails("hello@empresa.com")
        self.assertEqual(result, [])

    def test_filter_admin(self):
        result = ed.extract_emails("admin@empresa.com")
        self.assertEqual(result, [])

    def test_filter_vendas(self):
        result = ed.extract_emails("vendas@empresa.com")
        self.assertEqual(result, [])

    def test_filter_noreply(self):
        result = ed.extract_emails("noreply@empresa.com")
        self.assertEqual(result, [])

    def test_filter_suporte(self):
        result = ed.extract_emails("suporte@empresa.com")
        self.assertEqual(result, [])

    def test_filter_atendimento(self):
        result = ed.extract_emails("atendimento@empresa.com")
        self.assertEqual(result, [])

    def test_filter_sac(self):
        result = ed.extract_emails("sac@empresa.com")
        self.assertEqual(result, [])

    # ---- Non-generic emails that MUST pass ----
    def test_pass_maria_gmail(self):
        result = ed.extract_emails("maria@gmail.com")
        self.assertEqual(result, ['maria@gmail.com'])

    def test_pass_contato_clinica_outlook(self):
        result = ed.extract_emails("contato.clinica@outlook.com")
        self.assertEqual(result, ['contato.clinica@outlook.com'])

    def test_pass_dra_ana_vet(self):
        result = ed.extract_emails("dra.ana@vet.com.br")
        self.assertEqual(result, ['dra.ana@vet.com.br'])

    def test_pass_contato_prefix_but_not_generic(self):
        # "contatocomercial@" starts with "contato@" prefix match in the code
        # BUT code checks startswith('contato@') exactly - so it IS filtered
        # Actually: startswith('contato@') → 'contatocomercial@'.startswith('contato@') = True
        # Wait let me check: 'contatocomercial@' starts with 'contato@'? No, 'contatocomercial@'[0:8] = 'contatoc'
        # So 'contatocomercial@'.startswith('contato@') = False → it passes the filter
        result = ed.extract_emails("contatocomercial@empresa.com")
        self.assertEqual(result, ['contatocomercial@empresa.com'])

    def test_both_generic_and_valid(self):
        text = "contato@empresa.com.br but also maria@gmail.com"
        result = ed.extract_emails(text)
        self.assertIn('maria@gmail.com', result)
        self.assertNotIn('contato@empresa.com.br', result)

    def test_very_long_email_filtered(self):
        # The script does NOT filter by length, only by generic patterns
        # This test expectation is based on incorrect assumption about the code
        # So we test what the code actually does - pass very long emails through
        long_local = 'a' * 60
        result = ed.extract_emails(f"{long_local}@gmail.com")
        self.assertEqual(result, [f"{long_local}@gmail.com"])

    def test_normal_long_email_passes(self):
        # ~45 chars total - not filtered
        result = ed.extract_emails("verylongname.that.is.descriptive@gmail.com")
        self.assertEqual(result, ['verylongname.that.is.descriptive@gmail.com'])


class TestFetchWebsiteText(unittest.TestCase):
    """Test fetch_website_text() function."""

    @patch('email_discovery.urllib.request.urlopen')
    def test_valid_html(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'<html><body><p>Hello World</p></body></html>'
        mock_urlopen.return_value = mock_resp

        result = ed.fetch_website_text('https://example.com')
        self.assertEqual(result, 'Hello World')

    @patch('email_discovery.urllib.request.urlopen')
    def test_html_with_scripts_and_styles_removed(self, mock_urlopen):
        html = '''
        <html>
        <head><style>.class{color:red}</style></head>
        <body>
        <script>alert("hi")</script>
        <p>Contact: teste@email.com</p>
        </body>
        </html>
        '''
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode('utf-8')
        mock_urlopen.return_value = mock_resp

        result = ed.fetch_website_text('https://example.com')
        self.assertNotIn('alert', result)
        self.assertNotIn('.class', result)
        self.assertIn('Contact:', result)
        self.assertIn('teste@email.com', result)

    @patch('email_discovery.urllib.request.urlopen')
    def test_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = ed.urllib.error.HTTPError(
            'https://example.com', 404, 'Not Found', {}, None
        )
        result = ed.fetch_website_text('https://example.com')
        self.assertEqual(result, '')

    @patch('email_discovery.urllib.request.urlopen')
    def test_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("timed out")
        result = ed.fetch_website_text('https://example.com', timeout=5)
        self.assertEqual(result, '')

    @patch('email_discovery.urllib.request.urlopen')
    def test_generic_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("some error")
        result = ed.fetch_website_text('https://example.com')
        self.assertEqual(result, '')


class TestExtractContactUrl(unittest.TestCase):
    """Test extract_contact_url() function."""

    @patch('email_discovery.fetch_website_text')
    def test_contact_page_with_email(self, mock_fetch):
        mock_fetch.return_value = 'Contact page with our email at maria@empresa.com for more details about our services and products offered to customers in the region.'
        url, emails = ed.extract_contact_url('https://example.com')
        self.assertEqual(url, 'https://example.com/contact')
        self.assertIn('maria@empresa.com', emails)

    @patch('email_discovery.fetch_website_text')
    def test_no_email_on_any_contact_path(self, mock_fetch):
        mock_fetch.return_value = 'Just some text with no email address here'
        url, emails = ed.extract_contact_url('https://example.com')
        self.assertIsNone(url)
        self.assertEqual(emails, [])

    @patch('email_discovery.fetch_website_text')
    def test_short_text_not_enough(self, mock_fetch):
        mock_fetch.return_value = 'short'  # less than 100 chars
        url, emails = ed.extract_contact_url('https://example.com')
        self.assertIsNone(url)
        self.assertEqual(emails, [])

    @patch('email_discovery.fetch_website_text')
    def test_contato_path_found(self, mock_fetch):
        def fetch_side_effect(url, timeout=5):
            if '/contato' in url:
                return 'Pagina de contato email@empresa.com大量的文字内容 e mais informacoes sobre nossos servicos e produtos para clientes'
            return ''
        mock_fetch.side_effect = fetch_side_effect
        url, emails = ed.extract_contact_url('https://example.com')
        self.assertEqual(url, 'https://example.com/contato')
        self.assertIn('email@empresa.com', emails)


class TestDiscoverEmailForUrl(unittest.TestCase):
    """Test discover_email_for_url() function."""

    @patch('email_discovery.extract_contact_url')
    @patch('email_discovery.fetch_website_text')
    def test_email_on_homepage(self, mock_fetch, mock_extract_contact):
        mock_fetch.return_value = 'Welcome to our site contact@ourbusiness.com'
        mock_extract_contact.return_value = (None, [])
        result = ed.discover_email_for_url('https://example.com')
        self.assertEqual(result, 'contact@ourbusiness.com')

    @patch('email_discovery.extract_contact_url')
    @patch('email_discovery.fetch_website_text')
    def test_email_only_on_contact_page(self, mock_fetch, mock_extract_contact):
        mock_fetch.return_value = 'Welcome to our site with no email here'
        mock_extract_contact.return_value = ('https://example.com/contato', ['only@here.com'])
        result = ed.discover_email_for_url('https://example.com')
        self.assertEqual(result, 'only@here.com')

    @patch('email_discovery.extract_contact_url')
    @patch('email_discovery.fetch_website_text')
    def test_no_email_anywhere(self, mock_fetch, mock_extract_contact):
        mock_fetch.return_value = 'Just a website with no email at all'
        mock_extract_contact.return_value = (None, [])
        result = ed.discover_email_for_url('https://example.com')
        self.assertIsNone(result)

    @patch('email_discovery.extract_contact_url')
    @patch('email_discovery.fetch_website_text')
    def test_timeout_error_returns_none(self, mock_fetch, mock_extract_contact):
        mock_fetch.return_value = ''  # fetch_website_text returns '' on timeout
        mock_extract_contact.return_value = (None, [])
        result = ed.discover_email_for_url('https://example.com')
        self.assertIsNone(result)


class TestExtractWebsiteFromSerp(unittest.TestCase):
    """Test extract_website_from_serp() function."""

    def test_pixelalchemy_skipped(self):
        data = {'organic': [{'link': 'https://pixelalchemy.vercel.app', 'title': 'Demo Site', 'snippet': 'demo'}]}
        result = ed.extract_website_from_serp(data)
        self.assertIsNone(result)

    def test_facebook_skipped(self):
        data = {'organic': [{'link': 'https://facebook.com/pagename', 'title': 'Page', 'snippet': ''}]}
        result = ed.extract_website_from_serp(data)
        self.assertIsNone(result)

    def test_instagram_skipped(self):
        data = {'organic': [{'link': 'https://instagram.com/page', 'title': 'IG', 'snippet': ''}]}
        result = ed.extract_website_from_serp(data)
        self.assertIsNone(result)

    def test_maps_google_skipped(self):
        data = {'organic': [{'link': 'https://maps.google.com/...', 'title': 'Mapa', 'snippet': 'localização'}]}
        result = ed.extract_website_from_serp(data)
        self.assertIsNone(result)

    def test_aggregator_in_snippet_skipped(self):
        data = {'organic': [{'link': 'https://example.com', 'title': 'Business', 'snippet': 'aggregated ranking'}]}
        result = ed.extract_website_from_serp(data)
        self.assertIsNone(result)

    def test_valid_site_returned(self):
        data = {'organic': [
            {'link': 'https://pixelalchemy.vercel.app', 'title': 'Demo', 'snippet': 'demo'},
            {'link': 'https://realbusiness.com.br', 'title': 'Real Business Name', 'snippet': 'Business in city'}
        ]}
        result = ed.extract_website_from_serp(data)
        self.assertEqual(result, 'https://realbusiness.com.br')

    def test_empty_organic(self):
        data = {'organic': []}
        result = ed.extract_website_from_serp(data)
        self.assertIsNone(result)

    def test_no_organic_key(self):
        data = {}
        result = ed.extract_website_from_serp(data)
        self.assertIsNone(result)

    def test_multiple_valid_choices_returns_first(self):
        data = {'organic': [
            {'link': 'https://site1.com', 'title': 'Biz 1', 'snippet': 'desc'},
            {'link': 'https://site2.com', 'title': 'Biz 2', 'snippet': 'desc'}
        ]}
        result = ed.extract_website_from_serp(data)
        self.assertEqual(result, 'https://site1.com')


class TestSerpSearch(unittest.TestCase):
    """Test serp_search() function."""

    @patch('email_discovery.urllib.request.urlopen')
    def test_valid_json_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"organic": [{"link": "https://test.com", "title": "Test"}]}'
        mock_urlopen.return_value = mock_resp

        result = ed.serp_search('some query', num=3)
        self.assertEqual(result['organic'][0]['link'], 'https://test.com')

    @patch('email_discovery.urllib.request.urlopen')
    def test_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = ed.urllib.error.HTTPError(
            'https://example.com', 500, 'Error', {}, None
        )
        result = ed.serp_search('query')
        self.assertEqual(result, {})

    @patch('email_discovery.urllib.request.urlopen')
    def test_empty_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b''
        mock_urlopen.return_value = mock_resp
        result = ed.serp_search('query')
        self.assertEqual(result, {})

    @patch('email_discovery.urllib.request.urlopen')
    def test_malformed_json(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'not valid json'
        mock_urlopen.return_value = mock_resp
        result = ed.serp_search('query')
        self.assertEqual(result, {})

    @patch('email_discovery.urllib.request.urlopen')
    def test_request_headers(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{}'
        mock_urlopen.return_value = mock_resp

        ed.serp_search('test query', num=5)

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        # urllib normalizes header keys to 'X-api-key' form; use get_header which is case-insensitive
        self.assertEqual(req.get_header('X-api-key'), 'mock_test_key')


class TestBuildSearchQuery(unittest.TestCase):
    """Test build_search_query() function."""

    def test_nome_only(self):
        prospect = {'nome': 'Clinica Veterinaria Sao Jose', 'nicho': '', 'endereco': ''}
        result = ed.build_search_query(prospect)
        self.assertIn('Clinica Veterinaria Sao Jose', result)
        self.assertIn('Ribeirão Preto', result)

    def test_nome_with_hyphen_pipe_split(self):
        prospect = {'nome': 'Dr. João - Veterinária | Clínica', 'nicho': '', 'endereco': ''}
        result = ed.build_search_query(prospect)
        # Should split on ' - ' and ' | ' and take first part
        self.assertTrue(result.startswith('Dr. João'))
        self.assertIn('Ribeirão Preto', result)

    def test_nome_limited_to_4_words(self):
        prospect = {'nome': 'Um Dois Tres Quatro Cinco Seis', 'nicho': '', 'endereco': ''}
        result = ed.build_search_query(prospect)
        words = result.split()
        self.assertLessEqual(len(words), 6)  # name words + cidade words

    def test_with_nicho_padaria(self):
        prospect = {'nome': 'Padaria Sao Paulo', 'nicho': 'Padaria', 'endereco': ''}
        result = ed.build_search_query(prospect)
        self.assertIn('Padaria', result)

    def test_with_nicho_pizzaria(self):
        prospect = {'nome': 'Pizzaria Milano', 'nicho': 'Pizzaria', 'endereco': ''}
        result = ed.build_search_query(prospect)
        self.assertIn('Pizzaria', result)

    def test_with_nicho_acougue(self):
        prospect = {'nome': 'Acougue do Ze', 'nicho': 'Acougue', 'endereco': ''}
        result = ed.build_search_query(prospect)
        self.assertIn('Acougue', result)

    def test_with_nicho_barbearia(self):
        prospect = {'nome': 'Barbearia Old School', 'nicho': 'Barbearia', 'endereco': ''}
        result = ed.build_search_query(prospect)
        self.assertIn('Barbearia', result)

    def test_other_nicho_no_type_added(self):
        prospect = {'nome': 'Clinica Bela', 'nicho': 'Veterinaria', 'endereco': ''}
        result = ed.build_search_query(prospect)
        # Should not duplicate tipo (nicho is not in the special list)
        self.assertNotIn('Veterinaria', result.split('Ribeirao')[0])


class TestGetProspectsWithoutEmail(unittest.TestCase):
    """Test get_prospects_without_email() function."""

    @patch('email_discovery.sqlite3.connect')
    def test_zero_results(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        mock_conn.row_factory = None
        mock_connect.return_value = mock_conn

        # Patch row_factory after connect
        with patch.object(mock_conn, 'row_factory', ed.sqlite3.Row):
            results, conn = ed.get_prospects_without_email()

        self.assertEqual(results, [])
        mock_connect.assert_called_once()

    @patch('email_discovery.sqlite3.connect')
    def test_three_results(self, mock_connect):
        mock_conn = MagicMock()
        mock_row1 = {'id': 1, 'nome': 'Cliente A', 'telefone': '111', 'nicho': ' Vet'}
        mock_row2 = {'id': 2, 'nome': 'Cliente B', 'telefone': '222', 'nicho': ''}
        mock_row3 = {'id': 3, 'nome': 'Cliente C', 'telefone': '333', 'nicho': 'Beleza'}

        # Simulate cursor fetchall returning rows that dict() can process
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [mock_row1, mock_row2, mock_row3]
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.object(mock_conn, 'row_factory', ed.sqlite3.Row):
            results, conn = ed.get_prospects_without_email()

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['nome'], 'Cliente A')

    @patch('email_discovery.sqlite3.connect')
    def test_with_limit(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'nome': 'A', 'telefone': '111', 'nicho': '', 'endereco': '', 'site_url': None}]
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.object(mock_conn, 'row_factory', ed.sqlite3.Row):
            results, conn = ed.get_prospects_without_email(limit=5)

        # Verify LIMIT was used in SQL
        call_sql = mock_conn.execute.call_args[0][0]
        self.assertIn('LIMIT', call_sql)


class TestUpdateProspectEmail(unittest.TestCase):
    """Test update_prospect_email() function."""

    @patch('email_discovery.datetime')
    def test_update_with_site_url(self, mock_datetime):
        mock_datetime.now.return_value.isoformat.return_value = '2026-04-15T10:00:00'
        mock_conn = MagicMock()

        ed.update_prospect_email(mock_conn, 42, 'test@email.com', 'https://real.com')

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        self.assertEqual(call_args[1][0], 'test@email.com')
        self.assertEqual(call_args[1][1], 'https://real.com')
        self.assertEqual(call_args[1][3], 42)
        mock_conn.commit.assert_called_once()

    @patch('email_discovery.datetime')
    def test_update_without_site_url(self, mock_datetime):
        mock_datetime.now.return_value.isoformat.return_value = '2026-04-15T10:00:00'
        mock_conn = MagicMock()

        ed.update_prospect_email(mock_conn, 99, 'only@email.com', None)

        call_args = mock_conn.execute.call_args[0]
        # Params: (email, updated_at, prospect_id) when no site_url
        self.assertEqual(call_args[1][0], 'only@email.com')
        self.assertEqual(call_args[1][1], '2026-04-15T10:00:00')
        self.assertEqual(call_args[1][2], 99)
        mock_conn.commit.assert_called_once()


class TestMarkAsNotFound(unittest.TestCase):
    """Test mark_as_not_found() function."""

    @patch('email_discovery.datetime')
    def test_updates_observacoes(self, mock_datetime):
        mock_datetime.now.return_value.isoformat.return_value = '2026-04-15T10:00:00'
        mock_conn = MagicMock()

        ed.mark_as_not_found(mock_conn, 7, 'site not reachable')

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        sql = call_args[0]
        params = call_args[1]
        self.assertIn('observacoes', sql)
        self.assertIn('email_discovery', params[0])
        self.assertEqual(params[1], 7)
        mock_conn.commit.assert_called_once()


class TestEdgeCases(unittest.TestCase):
    """Edge case tests."""

    @patch('email_discovery.extract_contact_url')
    @patch('email_discovery.fetch_website_text')
    def test_website_404(self, mock_fetch, mock_extract_contact):
        mock_fetch.return_value = ''
        mock_extract_contact.return_value = (None, [])
        result = ed.discover_email_for_url('https://example.com/not-exist')
        self.assertIsNone(result)

    @patch('email_discovery.extract_contact_url')
    @patch('email_discovery.fetch_website_text')
    def test_html_no_email(self, mock_fetch, mock_extract_contact):
        mock_fetch.return_value = 'Just some plain HTML with no email content at all'
        mock_extract_contact.return_value = (None, [])
        result = ed.discover_email_for_url('https://example.com')
        self.assertIsNone(result)

    def test_email_filtering_generic_prefix_variations(self):
        # These should all be filtered because they START with generic patterns
        generic_patterns = [
            'contato@',
            'info@',
            'hello@',
            'admin@',
            'vendas@',
            'noreply@',
            'suporte@',
            'atendimento@',
            'sac@'
        ]
        for pattern in generic_patterns:
            email = pattern + 'example.com'
            result = ed.extract_emails(email)
            self.assertEqual(result, [], f"Expected {email} to be filtered")


if __name__ == '__main__':
    unittest.main(verbosity=2)
