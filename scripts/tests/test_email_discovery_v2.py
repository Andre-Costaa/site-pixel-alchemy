#!/usr/bin/env python3
"""
Unit tests for email_discovery_v2.py
"""

import unittest
from unittest.mock import patch, MagicMock
import sys, os

os.environ['SERP_API_KEY'] = 'mock_test_key'
sys.path.insert(0, '/opt/data/home/site-pixel-alchemy/scripts')
import email_discovery_v2 as ed


class TestHasRealWebsite(unittest.TestCase):
    """Test has_real_website()"""

    def test_instagram_rejected(self):
        self.assertFalse(ed.has_real_website('https://instagram.com/somepage'))
        self.assertFalse(ed.has_real_website('https://www.instagram.com/p/ABC123'))

    def test_facebook_rejected(self):
        self.assertFalse(ed.has_real_website('https://facebook.com/somepage'))
        self.assertFalse(ed.has_real_website('https://fb.com/pagename'))

    def test_fresha_rejected(self):
        self.assertFalse(ed.has_real_website('https://fresha.com/lvp/salon'))

    def test_appbarber_rejected(self):
        self.assertFalse(ed.has_real_website('https://sites.appbarber.com.br/somebarber'))

    def test_linktr_rejected(self):
        self.assertFalse(ed.has_real_website('https://linktr.ee/somepage'))

    def test_agendas_link_rejected(self):
        self.assertFalse(ed.has_real_website('https://agendas.link/barber'))

    def test_yelp_rejected(self):
        self.assertFalse(ed.has_real_website('https://m.yelp.com/search?find_desc=Butcher'))

    def test_real_site_accepted(self):
        self.assertTrue(ed.has_real_website('https://www.example.com.br'))
        self.assertTrue(ed.has_real_website('https://clinicaveterinaria.com'))
        self.assertTrue(ed.has_real_website('https://barbeariadonguillermo.com.br'))

    def test_none_url(self):
        self.assertFalse(ed.has_real_website(None))
        self.assertFalse(ed.has_real_website(''))

    def test_whatsapp_wa_me_rejected(self):
        self.assertFalse(ed.has_real_website('https://wa.me/551699999999'))


class TestExtractEmails(unittest.TestCase):
    """Test extract_emails()"""

    def test_no_email(self):
        result = ed.extract_emails("No email here")
        self.assertEqual(result, [])

    def test_one_email(self):
        result = ed.extract_emails("Contact at maria@empresa.com.br please")
        self.assertEqual(result, ['maria@empresa.com.br'])

    def test_generic_filtered(self):
        for prefix in ed.GENERIC_EMAILS:
            result = ed.extract_emails(f"{prefix}empresa.com")
            self.assertEqual(result, [], f"{prefix} should be filtered")

    def test_contato_clinica_passes(self):
        # contato.clinica does NOT start with contato@
        result = ed.extract_emails("contato.clinica@outlook.com")
        self.assertEqual(result, ['contato.clinica@outlook.com'])

    def test_dra_ana_vet_passes(self):
        result = ed.extract_emails("dra.ana@vet.com.br")
        self.assertEqual(result, ['dra.ana@vet.com.br'])

    def test_mailto_extracted(self):
        result = ed.extract_emails('<a href="mailto:maria@gmail.com">Email</a>')
        self.assertEqual(result, ['maria@gmail.com'])

    def test_mixed_generic_and_valid(self):
        text = "contato@empresa.com.br or maria@gmail.com"
        result = ed.extract_emails(text)
        self.assertIn('maria@gmail.com', result)
        self.assertNotIn('contato@empresa.com.br', result)


class TestFetchWebsiteText(unittest.TestCase):
    """Test fetch_website_text()"""

    @patch('email_discovery_v2.urllib.request.urlopen')
    def test_strips_scripts(self, mock_urlopen):
        html = '<html><body><script>alert("x")</script><p>Email: teste@x.com</p></body></html>'
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode('utf-8')
        mock_urlopen.return_value = mock_resp
        result = ed.fetch_website_text('https://example.com')
        self.assertNotIn('alert', result)
        self.assertIn('teste@x.com', result)

    @patch('email_discovery_v2.urllib.request.urlopen')
    def test_strips_styles(self, mock_urlopen):
        html = '<html><head><style>.x{color:red}</style></head><body><p>teste@test.com</p></body></html>'
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode('utf-8')
        mock_urlopen.return_value = mock_resp
        result = ed.fetch_website_text('https://example.com')
        self.assertNotIn('.x{color:red}', result)

    @patch('email_discovery_v2.urllib.request.urlopen')
    def test_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError()
        result = ed.fetch_website_text('https://example.com')
        self.assertEqual(result, '')

    @patch('email_discovery_v2.urllib.request.urlopen')
    def test_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("error")
        result = ed.fetch_website_text('https://example.com')
        self.assertEqual(result, '')


class TestDiscoverEmailFromSite(unittest.TestCase):
    """Test discover_email_from_site()"""

    @patch('email_discovery_v2.extract_contact_urls')
    @patch('email_discovery_v2.fetch_website_text')
    def test_email_on_homepage(self, mock_fetch, mock_contacts):
        mock_fetch.return_value = 'Contact us at maria@business.com'
        mock_contacts.return_value = []
        counter = {'calls': 0}
        email, url = ed.discover_email_from_site('https://example.com', counter)
        self.assertEqual(email, 'maria@business.com')
        self.assertIsNone(url)
        self.assertEqual(counter['calls'], 1)

    @patch('email_discovery_v2.extract_contact_urls')
    @patch('email_discovery_v2.fetch_website_text')
    def test_email_on_contact_page(self, mock_fetch, mock_contacts):
        mock_fetch.return_value = 'No email here'
        mock_contacts.return_value = [('https://example.com/contato', ['only@here.com'])]
        counter = {'calls': 0}
        email, url = ed.discover_email_from_site('https://example.com', counter)
        self.assertEqual(email, 'only@here.com')
        self.assertEqual(url, 'https://example.com/contato')
        # 1 for homepage + 1 for contact page attempt
        self.assertEqual(counter['calls'], 2)

    @patch('email_discovery_v2.extract_contact_urls')
    @patch('email_discovery_v2.fetch_website_text')
    def test_no_email_anywhere(self, mock_fetch, mock_contacts):
        mock_fetch.return_value = 'Just text no email'
        mock_contacts.return_value = []
        counter = {'calls': 0}
        email, url = ed.discover_email_from_site('https://example.com', counter)
        self.assertIsNone(email)
        self.assertIsNone(url)

    @patch('email_discovery_v2.extract_contact_urls')
    @patch('email_discovery_v2.fetch_website_text')
    def test_call_limit_respected(self, mock_fetch, mock_contacts):
        counter = {'calls': 3}
        email, url = ed.discover_email_from_site('https://example.com', counter)
        self.assertIsNone(email)
        mock_fetch.assert_not_called()


class TestMapsDiscovery(unittest.TestCase):
    """Test maps_discovery()"""

    @patch('email_discovery_v2.serp_maps_search')
    def test_returns_phone_and_website(self, mock_maps):
        mock_maps.return_value = {
            'places': [{
                'title': 'Clinic Test',
                'phoneNumber': '+55 16 99999-9999',
                'website': 'https://realsite.com.br'
            }]
        }
        counter = {'calls': 0}
        prospect = {'nome': 'Clinic Test', 'nicho': 'Veterinaria'}
        phone, website, title = ed.maps_discovery(prospect, counter)
        self.assertEqual(phone, '+55 16 99999-9999')
        self.assertEqual(website, 'https://realsite.com.br')
        self.assertEqual(counter['calls'], 1)

    @patch('email_discovery_v2.serp_maps_search')
    def test_skips_social_media_website(self, mock_maps):
        mock_maps.return_value = {
            'places': [{
                'title': 'Salon Test',
                'phoneNumber': '+55 16 99999-9999',
                'website': 'https://instagram.com/salontest'
            }, {
                'title': 'Salon Test',
                'phoneNumber': '+55 16 99999-9999',
                'website': 'https://realsite.com.br'
            }]
        }
        counter = {'calls': 0}
        prospect = {'nome': 'Salon Test', 'nicho': 'Beleza'}
        phone, website, title = ed.maps_discovery(prospect, counter)
        # Should find the real site, not instagram
        self.assertEqual(website, 'https://realsite.com.br')

    @patch('email_discovery_v2.serp_maps_search')
    def test_no_places(self, mock_maps):
        mock_maps.return_value = {'places': []}
        counter = {'calls': 0}
        prospect = {'nome': 'NoExist', 'nicho': 'Beleza'}
        phone, website, title = ed.maps_discovery(prospect, counter)
        self.assertIsNone(phone)
        self.assertIsNone(website)


class TestSearchDiscovery(unittest.TestCase):
    """Test search_discovery()"""

    @patch('email_discovery_v2.serp_search')
    def test_skips_demo_sites(self, mock_search):
        mock_search.return_value = {
            'organic': [
                {'link': 'https://pixelalchemy.vercel.app/demo', 'title': 'Demo', 'snippet': 'demo'},
                {'link': 'https://realsite.com.br', 'title': 'Real Business', 'snippet': 'Business'}
            ]
        }
        counter = {'calls': 0}
        prospect = {'nome': 'Real Business', 'nicho': ''}
        result = ed.search_discovery(prospect, counter)
        self.assertEqual(result, 'https://realsite.com.br')

    @patch('email_discovery_v2.serp_search')
    def test_skips_social_media(self, mock_search):
        mock_search.return_value = {
            'organic': [
                {'link': 'https://instagram.com/page', 'title': 'Page', 'snippet': ''}
            ]
        }
        counter = {'calls': 0}
        prospect = {'nome': 'Page', 'nicho': ''}
        result = ed.search_discovery(prospect, counter)
        self.assertIsNone(result)

    @patch('email_discovery_v2.serp_search')
    def test_kg_email_detected(self, mock_search):
        mock_search.return_value = {
            'organic': [],
            'knowledgeGraph': {
                'title': 'Business Name',
                'website': 'https://business.com',
                # Knowledge Graph doesn't usually have email but let's test
            }
        }
        counter = {'calls': 0}
        prospect = {'nome': 'Business', 'nicho': ''}
        result = ed.search_discovery(prospect, counter)
        # No email in KG here
        self.assertIsNone(result)

    @patch('email_discovery_v2.serp_search')
    def test_call_limit_respected(self, mock_search):
        counter = {'calls': 3}
        prospect = {'nome': 'Test', 'nicho': ''}
        result = ed.search_discovery(prospect, counter)
        self.assertIsNone(result)
        mock_search.assert_not_called()


class TestGetProspectsNeedingEmail(unittest.TestCase):
    """Test get_prospects_needing_email()"""

    @patch('email_discovery_v2.sqlite3.connect')
    def test_filters_correctly(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nome': 'A', 'telefone': '16999999999', 'nicho': 'Vet', 'site_url': '', 'pipeline_status': 'Lead'}
        ]
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.object(mock_conn, 'row_factory', ed.sqlite3.Row):
            results, conn = ed.get_prospects_needing_email(limit=10)

        self.assertEqual(len(results), 1)
        # Verify SQL has the right filters
        call_sql = mock_conn.execute.call_args[0][0]
        self.assertIn('telefone IS NOT NULL', call_sql)
        self.assertIn('Fechado', call_sql)
        self.assertIn('LIMIT', call_sql)


if __name__ == '__main__':
    unittest.main(verbosity=2)
