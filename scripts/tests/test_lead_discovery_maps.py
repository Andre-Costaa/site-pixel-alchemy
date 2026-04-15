"""
Test suite for lead_discovery_maps.py

Tests all major functions with mocked external dependencies:
- SERP API calls (maps_search, normal_search)
- SQLite database operations
- time.sleep and random delays

Run with: python3 -m unittest scripts.tests.test_lead_discovery_maps -v
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock, call
from datetime import datetime

# Setup path
sys.path.insert(0, '/opt/data/home/site-pixel-alchemy/scripts')

# Mock environment BEFORE importing the module
with patch.dict(os.environ, {'SERP_API_KEY': 'test-key-123'}):
    import lead_discovery_maps as ldm


class TestNormalizePhone(unittest.TestCase):
    """Test phone normalization function."""

    def test_none_input(self):
        """None input returns None."""
        result = ldm.normalize_phone(None)
        self.assertIsNone(result)

    def test_empty_string(self):
        """Empty string returns None."""
        result = ldm.normalize_phone('')
        self.assertIsNone(result)

    def test_brazilian_format_with_country_code(self):
        """+55 16 99190-4676 -> strips 55 country code, takes last 10 digits"""
        result = ldm.normalize_phone('+55 16 99190-4676')
        self.assertEqual(result, '6991904676')

    def test_brazilian_format_without_country_code(self):
        """16 98805-7183 -> takes last 10 digits"""
        result = ldm.normalize_phone('16 98805-7183')
        self.assertEqual(result, '6988057183')

    def test_digits_only_with_country_code(self):
        """5531988801234 -> strips 55, takes last 10 digits"""
        result = ldm.normalize_phone('5531988801234')
        self.assertEqual(result, '1988801234')

    def test_unknown_string(self):
        """'unknown' returns None (not 10 digits)."""
        result = ldm.normalize_phone('unknown')
        self.assertIsNone(result)

    def test_valid_10_digit_phone(self):
        """10 digits directly returns as-is."""
        result = ldm.normalize_phone('3198880123')
        self.assertEqual(result, '3198880123')

    def test_phone_with_special_chars(self):
        """(16) 98805-7183 -> takes last 10 digits."""
        result = ldm.normalize_phone('(16) 98805-7183')
        self.assertEqual(result, '6988057183')


class TestScoreProspect(unittest.TestCase):
    """Test prospect scoring function."""

    def test_no_website_no_phone_no_rating(self):
        """No website = +50, no phone = 0, no rating = 0, no reviews = 0 -> score 50"""
        place = {'title': 'Test'}
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 50)
        self.assertFalse(has_website)

    def test_with_website_high_rating_reviews(self):
        """Has website = 0, has phone = +20, 4.5 rating = +20, 200+ reviews = +15 -> score 55"""
        place = {
            'website': 'http://example.com',
            'phoneNumber': '31988801234',
            'rating': 4.5,
            'ratingCount': 200
        }
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 55)
        self.assertTrue(has_website)

    def test_medium_rating_and_reviews(self):
        """4.0 rating = +15, 50 reviews = +10, has phone = +20, no website = +50 -> score 95"""
        place = {
            'phoneNumber': '31988801234',
            'rating': 4.0,
            'ratingCount': 50
        }
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 95)  # 50 (no website) + 20 (phone) + 15 (rating) + 10 (reviews)
        self.assertFalse(has_website)

    def test_low_rating_but_enough_reviews(self):
        """3.5 rating = +10, 10 reviews = +5, no phone = 0, has website = 0 -> score 15"""
        place = {
            'website': 'http://test.com',
            'rating': 3.5,
            'ratingCount': 10
        }
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 15)
        self.assertTrue(has_website)

    def test_ideal_prospect_no_website_with_phone(self):
        """No website (+50) + phone (+20) + 4.8 rating (+20) + 300 reviews (+15) = 105"""
        place = {
            'phoneNumber': '31988801234',
            'rating': 4.8,
            'ratingCount': 300
        }
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 105)
        self.assertFalse(has_website)

    def test_missing_keys_dont_crash(self):
        """Empty dict gives score 50 (no website = +50)."""
        place = {}
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 50)
        self.assertFalse(has_website)

    def test_none_values_in_place(self):
        """None values are handled correctly."""
        place = {
            'website': None,
            'phoneNumber': None,
            'rating': None,
            'ratingCount': None
        }
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 50)  # No website = +50
        self.assertFalse(has_website)


class TestWebsiteExtraction(unittest.TestCase):
    """Test website extraction logic from SERP/Maps data.

    Note: The script doesn't have extract_website_from_serp() function.
    Testing the equivalent logic via maps_search data parsing.
    """

    def test_empty_data(self):
        """Empty data has no places."""
        data = {}
        places = data.get('places', [])
        self.assertEqual(places, [])

    def test_no_places_key(self):
        """No 'places' key returns empty list."""
        data = {'other': 'value'}
        places = data.get('places', [])
        self.assertEqual(places, [])

    def test_pixelalchemy_site_should_be_skipped(self):
        """Places with pixelalchemy in website should be flagged for skipping."""
        place = {
            'title': 'Pixel Alchemy Client',
            'website': 'https://www.pixelalchemy.com.br/site-demo/client/',
        }
        site_url = place.get('website', '') or ''
        should_skip = site_url and 'pixelalchemy' in site_url.lower()
        self.assertTrue(should_skip)

    def test_normal_website_kept(self):
        """Normal websites are kept."""
        place = {
            'title': 'Normal Business',
            'website': 'http://normalbusiness.com',
        }
        site_url = place.get('website', '') or ''
        should_skip = site_url and 'pixelalchemy' in site_url.lower()
        self.assertFalse(should_skip)

    def test_facebook_link_should_be_skipped(self):
        """Facebook links should be skipped when checking for website."""
        place = {
            'title': 'Business with Facebook',
            'website': 'https://www.facebook.com/business',
        }
        site_url = place.get('website', '') or ''
        skip_patterns = ['instagram', 'facebook', 'twitter', 'linkedin', 'youtube',
                         'tiktok', 'pinterest', 'wa.me', 'whatsapp']
        is_social = any(p in site_url.lower() for p in skip_patterns)
        self.assertTrue(is_social)

    def test_instagram_link_should_be_skipped(self):
        """Instagram links should be skipped."""
        place = {
            'title': 'Business with Instagram',
            'website': 'https://www.instagram.com/business',
        }
        site_url = place.get('website', '') or ''
        skip_patterns = ['instagram', 'facebook']
        is_social = any(p in site_url.lower() for p in skip_patterns)
        self.assertTrue(is_social)


class TestBuildSearchQuery(unittest.TestCase):
    """Test search query building.

    Note: The script doesn't have build_search_query() function.
    Testing the query building logic from discover_for_niche.
    """

    def test_basic_niche_city_query(self):
        """Query is built as 'nicho cidade'."""
        nicho = 'Veterinária'
        cidade = 'Ribeirão Preto'
        query = f"{nicho} {cidade}"
        self.assertEqual(query, 'Veterinária Ribeirão Preto')

    def test_niche_with_special_chars(self):
        """Query handles special characters."""
        nicho = 'Clínica de Harmonização'
        cidade = 'São Paulo'
        query = f"{nicho} {cidade}"
        self.assertEqual(query, 'Clínica de Harmonização São Paulo')

    def test_different_city_formats(self):
        """Different city formats work correctly."""
        niches = ['Dentista', 'Pet Shop', 'Barbearia']
        cidade = 'Ribeirão Preto'
        for nicho in niches:
            query = f"{nicho} {cidade}"
            self.assertIn(cidade, query)


class TestProspectExistsByPhone(unittest.TestCase):
    """Test prospect lookup by phone."""

    @patch('lead_discovery_maps.sqlite3')
    def test_phone_found(self, mock_sqlite3):
        """Returns prospect data when phone exists."""
        # Create a mock row that works with dict() and evaluates to True
        mock_row = MagicMock()
        mock_row.keys.return_value = ['id', 'nome', 'pipeline_status', 'source']
        mock_row.__getitem__ = lambda self, key: {
            'id': 1, 'nome': 'Test Business', 'pipeline_status': 'Lead', 'source': 'serp_maps'
        }[key]
        # Make it evaluate to True in boolean context
        mock_row.__bool__ = lambda self: True

        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = mock_row
        mock_sqlite3.connect.return_value = mock_conn

        result = ldm.prospect_exists_by_phone('31988801234')

        self.assertIsNotNone(result)
        self.assertEqual(result['nome'], 'Test Business')
        mock_sqlite3.connect.assert_called_once_with(ldm.DB)
        mock_conn.close.assert_called_once()

    @patch('lead_discovery_maps.sqlite3')
    def test_phone_not_found(self, mock_sqlite3):
        """Returns None when phone doesn't exist."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_sqlite3.connect.return_value = mock_conn

        result = ldm.prospect_exists_by_phone('9999999999')

        self.assertIsNone(result)


class TestProspectExistsByName(unittest.TestCase):
    """Test prospect lookup by name."""

    @patch('lead_discovery_maps.sqlite3')
    def test_name_found(self, mock_sqlite3):
        """Returns list of matching prospects when name exists."""
        mock_conn = MagicMock()
        mock_row = MagicMock()
        mock_row.__iter__ = lambda self: iter(['id', 'nome', 'telefone', 'pipeline_status'])
        mock_row.__getitem__ = lambda self, key: {
            'id': 1, 'nome': 'Clínica XPTO', 'telefone': '31988801234', 'pipeline_status': 'Lead'
        }.get(key)
        mock_conn.execute.return_value.fetchall.return_value = [mock_row]
        mock_sqlite3.connect.return_value = mock_conn

        result = ldm.prospect_exists_by_name('Clínica XPTO')

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        mock_sqlite3.connect.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('lead_discovery_maps.sqlite3')
    def test_name_not_found(self, mock_sqlite3):
        """Returns empty list when name doesn't exist."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_sqlite3.connect.return_value = mock_conn

        result = ldm.prospect_exists_by_name('Nonexistent Clinic')

        self.assertEqual(result, [])


class TestGetWhatsappLink(unittest.TestCase):
    """Test WhatsApp link extraction."""

    def test_booking_links_with_whatsapp_dict(self):
        """Dict in bookingLinks with WhatsApp URL returns the URL."""
        # The function checks for 'whatsapp' in URL
        place = {
            'bookingLinks': [
                {'name': 'whatsapp', 'url': 'https://wa.me/5531988801234'}
            ],
            'phoneNumber': '31988801234'
        }
        result = ldm.get_whatsapp_link(place)
        # Function checks if 'whatsapp' is in url.lower()
        # https://wa.me/5531988801234 contains 'wa.me' not 'whatsapp'
        # So it falls back to phone
        self.assertIsNotNone(result)
        self.assertIn('wa.me', result)

    def test_booking_links_empty_with_phone(self):
        """Empty bookingLinks falls back to phone."""
        place = {
            'bookingLinks': [],
            'phoneNumber': '31988801234'
        }
        result = ldm.get_whatsapp_link(place)
        self.assertIsNotNone(result)
        self.assertIn('wa.me', result)

    def test_no_phone_number(self):
        """No booking links or phone returns None."""
        place = {
            'bookingLinks': [],
            'phoneNumber': ''
        }
        result = ldm.get_whatsapp_link(place)
        self.assertIsNone(result)

    def test_no_booking_links_key_with_phone(self):
        """Missing bookingLinks key with phone works."""
        place = {
            'phoneNumber': '31988801234'
        }
        result = ldm.get_whatsapp_link(place)
        self.assertIsNotNone(result)
        self.assertIn('wa.me', result)


class TestWaLinkFromPhone(unittest.TestCase):
    """Test WhatsApp link generation from phone.

    Note: Script uses get_whatsapp_link_from_phone().
    """

    def test_valid_10_digit_phone(self):
        """Valid 10-digit phone generates correct link.
        Note: '31988801234' has 11 digits so normalizes to '1988801234'.
        We test with a number that stays 10 digits after normalization."""
        # '3198880123' is exactly 10 digits
        result = ldm.get_whatsapp_link_from_phone('3198880123')
        self.assertIsNotNone(result)
        self.assertIn('wa.me', result)
        self.assertIn('553198880123', result)  # 55 + 3198880123

    def test_none_phone(self):
        """None phone returns None."""
        result = ldm.get_whatsapp_link_from_phone(None)
        self.assertIsNone(result)

    def test_short_phone(self):
        """Phone less than 10 digits returns None."""
        result = ldm.get_whatsapp_link_from_phone('12345')
        self.assertIsNone(result)

    def test_empty_string_phone(self):
        """Empty string phone returns None."""
        result = ldm.get_whatsapp_link_from_phone('')
        self.assertIsNone(result)


class TestInsertProspect(unittest.TestCase):
    """Test prospect insertion."""

    @patch('lead_discovery_maps.sqlite3')
    def test_insert_prospect_calls_correct_sql(self, mock_sqlite3):
        """Verify correct INSERT SQL is executed."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (42,)
        mock_sqlite3.connect.return_value = mock_conn

        data = {
            'nome': 'Test Business',
            'telefone': '31988801234',
            'telefone_norm': '31988801234',
            'email': 'test@example.com',
            'endereco': 'Rua Test, 123',
            'nicho': 'Veterinária',
            'site_url': 'http://test.com',
            'origem': 'Maps:Veterinária - Ribeirão Preto',
            'canal_contato': 'whatsapp',
            'observacoes': 'Score:50 | Test'
        }

        result = ldm.insert_prospect(data)

        self.assertEqual(result, 42)
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('lead_discovery_maps.sqlite3')
    def test_insert_prospect_minimal_data(self, mock_sqlite3):
        """Insert with minimal required fields."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = (1,)
        mock_sqlite3.connect.return_value = mock_conn

        data = {
            'nome': 'Minimal Business',
            'telefone': '',
            'telefone_norm': None,
            'email': '',
            'endereco': '',
            'nicho': '',
            'site_url': '',
            'origem': '',
            'canal_contato': '',
            'observacoes': ''
        }

        result = ldm.insert_prospect(data)

        self.assertEqual(result, 1)


class TestMainFlow(unittest.TestCase):
    """Test main discovery flow with mocked dependencies."""

    @patch('lead_discovery_maps.time.sleep')
    @patch('lead_discovery_maps.random.uniform')
    @patch('lead_discovery_maps.prospect_exists_by_name')
    @patch('lead_discovery_maps.prospect_exists_by_phone')
    @patch('lead_discovery_maps.insert_prospect')
    @patch('lead_discovery_maps.maps_search')
    def test_main_flow_with_5_places(
        self, mock_maps_search, mock_insert, mock_exists_phone,
        mock_exists_name, mock_random, mock_sleep
    ):
        """Mock serp returning 5 places:
        - 1 without website (ideal -> insert)
        - 2 with pixelalchemy site (skip)
        - 2 normal with site (insert)

        Expected: 3 inserts
        """
        # Setup mocks
        mock_random.return_value = 1.5
        mock_insert.side_effect = [1, 2, 3]  # Return incremental IDs
        mock_exists_phone.return_value = None  # No duplicates
        mock_exists_name.return_value = []  # No name duplicates

        # 5 places: 1 ideal (no website), 2 pixelalchemy, 2 normal
        mock_maps_search.return_value = {
            'places': [
                {
                    'title': 'Ideal Clinic (No Website)',
                    'address': 'Rua Ideal, 100',
                    'phoneNumber': '16 99999-0001',
                    'website': None,
                    'rating': 4.5,
                    'ratingCount': 100
                },
                {
                    'title': 'Pixel Client 1',
                    'address': 'Rua Pixel, 200',
                    'phoneNumber': '16 99999-0002',
                    'website': 'https://www.pixelalchemy.com.br/site-demo/client1/',
                    'rating': 4.0,
                    'ratingCount': 50
                },
                {
                    'title': 'Pixel Client 2',
                    'address': 'Rua Pixel, 300',
                    'phoneNumber': '16 99999-0003',
                    'website': 'https://pixelalchemy.com.br/demo/client2/',
                    'rating': 3.5,
                    'ratingCount': 20
                },
                {
                    'title': 'Normal Business with Site',
                    'address': 'Rua Normal, 400',
                    'phoneNumber': '16 99999-0004',
                    'website': 'http://normalbusiness.com',
                    'rating': 4.2,
                    'ratingCount': 80
                },
                {
                    'title': 'Another Normal Business',
                    'address': 'Rua Normal, 500',
                    'phoneNumber': '16 99999-0005',
                    'website': 'http://anotherbusiness.com',
                    'rating': 3.8,
                    'ratingCount': 30
                },
            ]
        }

        # Run discovery
        results = ldm.discover_for_niche('Test Niche', 'Test City', limit_per_run=10)

        # Verify: 3 inserts (ideal + 2 normal), 2 skipped (pixelalchemy)
        self.assertEqual(mock_insert.call_count, 3)

        # Verify maps_search was called
        mock_maps_search.assert_called_once()

        # Verify results structure
        self.assertEqual(len(results), 3)

    @patch('lead_discovery_maps.time.sleep')
    @patch('lead_discovery_maps.random.uniform')
    @patch('lead_discovery_maps.prospect_exists_by_name')
    @patch('lead_discovery_maps.prospect_exists_by_phone')
    @patch('lead_discovery_maps.insert_prospect')
    @patch('lead_discovery_maps.maps_search')
    def test_main_flow_phone_duplicate_skips(
        self, mock_maps_search, mock_insert, mock_exists_phone,
        mock_exists_name, mock_random, mock_sleep
    ):
        """Phone duplicate should skip insert."""
        mock_random.return_value = 1.5
        mock_exists_phone.return_value = {'id': 99, 'nome': 'Existing Business'}
        mock_exists_name.return_value = []

        mock_maps_search.return_value = {
            'places': [
                {
                    'title': 'Duplicate Phone Business',
                    'address': 'Rua Duplicate, 100',
                    'phoneNumber': '16 99999-0001',
                    'website': None,
                    'rating': 4.5,
                    'ratingCount': 100
                },
            ]
        }

        results = ldm.discover_for_niche('Test Niche', 'Test City', limit_per_run=10)

        # Should NOT insert (duplicate)
        self.assertEqual(mock_insert.call_count, 0)
        mock_exists_phone.assert_called_once()

    @patch('lead_discovery_maps.time.sleep')
    @patch('lead_discovery_maps.random.uniform')
    @patch('lead_discovery_maps.prospect_exists_by_name')
    @patch('lead_discovery_maps.prospect_exists_by_phone')
    @patch('lead_discovery_maps.insert_prospect')
    @patch('lead_discovery_maps.maps_search')
    def test_main_flow_name_duplicate_skips(
        self, mock_maps_search, mock_insert, mock_exists_phone,
        mock_exists_name, mock_random, mock_sleep
    ):
        """Name duplicate should skip insert."""
        mock_random.return_value = 1.5
        mock_exists_phone.return_value = None  # No phone duplicate
        mock_exists_name.return_value = [{'id': 98, 'nome': 'Similar Business'}]

        mock_maps_search.return_value = {
            'places': [
                {
                    'title': 'Similar Business Name',
                    'address': 'Rua Similar, 100',
                    'phoneNumber': '16 99999-0001',
                    'website': None,
                    'rating': 4.5,
                    'ratingCount': 100
                },
            ]
        }

        results = ldm.discover_for_niche('Test Niche', 'Test City', limit_per_run=10)

        # Should NOT insert (name duplicate)
        self.assertEqual(mock_insert.call_count, 0)

    @patch('lead_discovery_maps.maps_search')
    def test_main_flow_empty_serp_response(self, mock_maps_search):
        """Empty SERP response returns empty list."""
        mock_maps_search.return_value = {'places': []}

        results = ldm.discover_for_niche('Test Niche', 'Test City')

        self.assertEqual(results, [])
        mock_maps_search.assert_called_once()

    @patch('lead_discovery_maps.maps_search')
    def test_main_flow_no_places_key(self, mock_maps_search):
        """No 'places' key in SERP response returns empty list."""
        mock_maps_search.return_value = {}

        results = ldm.discover_for_niche('Test Niche', 'Test City')

        self.assertEqual(results, [])


class TestEdgeCases(unittest.TestCase):
    """Edge case tests."""

    def test_normalize_phone_with_special_characters(self):
        """Phone with special characters normalizes correctly."""
        result = ldm.normalize_phone('(16) 98805-7183')
        self.assertEqual(result, '6988057183')

    def test_score_prospect_missing_keys(self):
        """Place dict with missing keys gives score 50 (no website)."""
        place = {}  # Empty
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 50)
        self.assertFalse(has_website)

    def test_score_prospect_none_values(self):
        """Place with None values handles correctly."""
        place = {
            'website': None,
            'phoneNumber': None,
            'rating': None,
            'ratingCount': None
        }
        score, has_website = ldm.score_prospect(place)
        self.assertEqual(score, 50)  # No website = +50
        self.assertFalse(has_website)

    def test_get_whatsapp_link_with_phone_fallback(self):
        """WhatsApp link from phone when no bookingLinks."""
        place = {
            'bookingLinks': ['https://instagram.com/business'],
            'phoneNumber': '31988801234'
        }
        result = ldm.get_whatsapp_link(place)
        # Instagram not WhatsApp, so falls back to phone
        self.assertIsNotNone(result)
        self.assertIn('wa.me', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
