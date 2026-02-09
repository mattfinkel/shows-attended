"""
Comprehensive tests for Shows Attended app
Tests database operations, authentication, and core functionality
"""
import pytest
import hashlib
from unittest.mock import Mock, patch, MagicMock
from libsql_client import create_client_sync
import os

# Test configuration
TEST_DB_URL = os.getenv("TURSO_TEST_DB_URL", "https://shows-attended-mattfinkel.aws-us-east-2.turso.io")
TEST_DB_TOKEN = os.getenv("TURSO_TEST_DB_TOKEN", "")

class TestAuthentication:
    """Test password authentication functionality"""

    def test_hash_password(self):
        """Test password hashing"""
        from auth import hash_password

        password = "test123"
        hashed = hash_password(password)

        # Should be SHA-256 hash (64 characters)
        assert len(hashed) == 64
        assert hashed == hashlib.sha256(password.encode()).hexdigest()

    def test_hash_consistency(self):
        """Test that same password always produces same hash"""
        from auth import hash_password

        password = "mypassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 == hash2

    @patch('streamlit.secrets')
    @patch('streamlit.session_state', {})
    def test_check_password_no_password_set(self, mock_secrets):
        """Test that app is accessible when no password is set"""
        from auth import check_password

        mock_secrets.get.return_value = None
        result = check_password()

        assert result == True

    def test_check_password_already_authenticated(self):
        """Test that authenticated users pass through"""
        import streamlit as st
        from auth import check_password

        # Mock session state with authenticated=True
        mock_state = MagicMock()
        mock_state.authenticated = True
        mock_state.__contains__ = lambda self, key: key == 'authenticated'
        mock_state.__getitem__ = lambda self, key: True if key == 'authenticated' else None

        with patch('streamlit.session_state', mock_state):
            with patch.object(st, 'secrets', {'app_password_hash': 'somehash'}):
                result = check_password()
                assert result == True


class TestDatabaseConnection:
    """Test database connectivity and basic queries"""

    @pytest.fixture
    def db_client(self):
        """Create a database client for testing"""
        if not TEST_DB_TOKEN:
            pytest.skip("No database token provided")

        return create_client_sync(
            url=TEST_DB_URL,
            auth_token=TEST_DB_TOKEN
        )

    def test_connection(self, db_client):
        """Test basic database connection"""
        result = db_client.execute("SELECT 1 as test")
        assert result.rows[0][0] == 1

    def test_shows_table_exists(self, db_client):
        """Test that shows table exists and has data"""
        result = db_client.execute("SELECT COUNT(*) FROM shows")
        count = result.rows[0][0]
        assert count > 0

    def test_bands_table_exists(self, db_client):
        """Test that bands table exists and has data"""
        result = db_client.execute("SELECT COUNT(*) FROM bands")
        count = result.rows[0][0]
        assert count > 0

    def test_venues_table_exists(self, db_client):
        """Test that venues table exists and has data"""
        result = db_client.execute("SELECT COUNT(*) FROM venues")
        count = result.rows[0][0]
        assert count > 0

    def test_primary_band_id_column_exists(self, db_client):
        """Test that primary_band_id column exists for grouping"""
        result = db_client.execute("""
            SELECT COUNT(*)
            FROM pragma_table_info('bands')
            WHERE name = 'primary_band_id'
        """)
        assert result.rows[0][0] == 1


class TestBandGrouping:
    """Test band grouping functionality"""

    @pytest.fixture
    def db_client(self):
        """Create a database client for testing"""
        if not TEST_DB_TOKEN:
            pytest.skip("No database token provided")

        return create_client_sync(
            url=TEST_DB_URL,
            auth_token=TEST_DB_TOKEN
        )

    def test_primary_bands_query(self, db_client):
        """Test query that gets only primary bands (not aliases)"""
        result = db_client.execute("""
            SELECT COUNT(*)
            FROM bands
            WHERE primary_band_id IS NULL
        """)
        primary_count = result.rows[0][0]
        assert primary_count > 0

    def test_grouped_band_stats(self, db_client):
        """Test that band stats roll up correctly"""
        result = db_client.execute("""
            SELECT
                COALESCE(b_primary.name, b.name) as name,
                COUNT(sb.id) as times_seen
            FROM bands b
            LEFT JOIN bands b_primary ON b.primary_band_id = b_primary.id
            LEFT JOIN show_bands sb ON (sb.band_id = b.id OR sb.band_id IN (
                SELECT id FROM bands WHERE primary_band_id = COALESCE(b_primary.id, b.id)
            ))
            WHERE b.primary_band_id IS NULL
            GROUP BY COALESCE(b_primary.id, b.id)
            HAVING times_seen > 0
            ORDER BY times_seen DESC
            LIMIT 1
        """)

        # Should return at least one band with shows
        assert len(result.rows) > 0
        top_band_name, show_count = result.rows[0]
        assert show_count > 0

    def test_band_aliases_query(self, db_client):
        """Test query to find band aliases"""
        result = db_client.execute("""
            SELECT
                b_alias.name,
                b_primary.name as primary_name
            FROM bands b_alias
            JOIN bands b_primary ON b_alias.primary_band_id = b_primary.id
            LIMIT 5
        """)

        # If there are any aliases, verify structure
        if len(result.rows) > 0:
            alias_name, primary_name = result.rows[0]
            assert alias_name is not None
            assert primary_name is not None


class TestVenueOperations:
    """Test venue-related functionality"""

    @pytest.fixture
    def db_client(self):
        """Create a database client for testing"""
        if not TEST_DB_TOKEN:
            pytest.skip("No database token provided")

        return create_client_sync(
            url=TEST_DB_URL,
            auth_token=TEST_DB_TOKEN
        )

    def test_closed_venue_field(self, db_client):
        """Test that closed field exists on venues"""
        result = db_client.execute("""
            SELECT COUNT(*)
            FROM pragma_table_info('venues')
            WHERE name = 'closed'
        """)
        assert result.rows[0][0] == 1

    def test_venue_stats_query(self, db_client):
        """Test venue statistics query"""
        result = db_client.execute("""
            SELECT
                v.id,
                v.name,
                v.location,
                v.closed,
                COUNT(s.id) as show_count
            FROM venues v
            LEFT JOIN shows s ON v.id = s.venue_id
            GROUP BY v.id
            ORDER BY show_count DESC
            LIMIT 10
        """)

        # Should return top venues
        assert len(result.rows) > 0

        # Verify structure
        for row in result.rows:
            venue_id, name, location, closed, show_count = row
            assert venue_id is not None
            assert name is not None
            assert isinstance(closed, (int, bool, type(None)))
            assert show_count >= 0


class TestStatsQueries:
    """Test statistics page queries"""

    @pytest.fixture
    def db_client(self):
        """Create a database client for testing"""
        if not TEST_DB_TOKEN:
            pytest.skip("No database token provided")

        return create_client_sync(
            url=TEST_DB_URL,
            auth_token=TEST_DB_TOKEN
        )

    def test_shows_by_year(self, db_client):
        """Test shows by year query"""
        result = db_client.execute("""
            SELECT
                strftime('%Y', date) as year,
                COUNT(*) as show_count
            FROM shows
            GROUP BY year
            ORDER BY year DESC
            LIMIT 5
        """)

        assert len(result.rows) > 0

        for row in result.rows:
            year, count = row
            assert year is not None
            assert count > 0

    def test_top_bands_with_grouping(self, db_client):
        """Test top bands query with grouping"""
        result = db_client.execute("""
            SELECT
                COALESCE(b_primary.name, b.name) as name,
                COUNT(sb.id) as times_seen
            FROM bands b
            LEFT JOIN bands b_primary ON b.primary_band_id = b_primary.id
            LEFT JOIN show_bands sb ON (sb.band_id = b.id OR sb.band_id IN (
                SELECT id FROM bands WHERE primary_band_id = COALESCE(b_primary.id, b.id)
            ))
            WHERE b.primary_band_id IS NULL
            GROUP BY COALESCE(b_primary.id, b.id)
            HAVING times_seen > 0
            ORDER BY times_seen DESC
            LIMIT 20
        """)

        assert len(result.rows) > 0

        # Verify descending order
        prev_count = float('inf')
        for row in result.rows:
            name, count = row
            assert count <= prev_count
            prev_count = count

    def test_total_counts(self, db_client):
        """Test overall statistics"""
        # Total shows
        result = db_client.execute("SELECT COUNT(*) FROM shows")
        total_shows = result.rows[0][0]
        assert total_shows > 0

        # Total primary bands
        result = db_client.execute("SELECT COUNT(*) FROM bands WHERE primary_band_id IS NULL")
        total_bands = result.rows[0][0]
        assert total_bands > 0

        # Total venues
        result = db_client.execute("SELECT COUNT(*) FROM venues")
        total_venues = result.rows[0][0]
        assert total_venues > 0


class TestSortingQueries:
    """Test sorting functionality for bands and venues"""

    @pytest.fixture
    def db_client(self):
        """Create a database client for testing"""
        if not TEST_DB_TOKEN:
            pytest.skip("No database token provided")

        return create_client_sync(
            url=TEST_DB_URL,
            auth_token=TEST_DB_TOKEN
        )

    def test_bands_sort_by_count(self, db_client):
        """Test bands sorted by show count"""
        result = db_client.execute("""
            SELECT
                COALESCE(b_primary.name, b.name) as name,
                COUNT(sb.id) as times_seen
            FROM bands b
            LEFT JOIN bands b_primary ON b.primary_band_id = b_primary.id
            LEFT JOIN show_bands sb ON (sb.band_id = b.id OR sb.band_id IN (
                SELECT id FROM bands WHERE primary_band_id = COALESCE(b_primary.id, b.id)
            ))
            WHERE b.primary_band_id IS NULL
            GROUP BY COALESCE(b_primary.id, b.id)
            HAVING times_seen >= 1
            ORDER BY times_seen DESC, COALESCE(b_primary.name, b.name)
            LIMIT 10
        """)

        # Verify descending order by count
        prev_count = float('inf')
        for row in result.rows:
            name, count = row
            assert count <= prev_count
            prev_count = count

    def test_bands_sort_by_name(self, db_client):
        """Test bands sorted alphabetically"""
        result = db_client.execute("""
            SELECT
                COALESCE(b_primary.name, b.name) as name,
                COUNT(sb.id) as times_seen
            FROM bands b
            LEFT JOIN bands b_primary ON b.primary_band_id = b_primary.id
            LEFT JOIN show_bands sb ON (sb.band_id = b.id OR sb.band_id IN (
                SELECT id FROM bands WHERE primary_band_id = COALESCE(b_primary.id, b.id)
            ))
            WHERE b.primary_band_id IS NULL
            GROUP BY COALESCE(b_primary.id, b.id)
            HAVING times_seen >= 1
            ORDER BY COALESCE(b_primary.name, b.name)
            LIMIT 10
        """)

        # Verify alphabetical order
        names = [row[0] for row in result.rows]
        assert names == sorted(names)

    def test_venues_sort_by_count(self, db_client):
        """Test venues sorted by show count"""
        result = db_client.execute("""
            SELECT
                v.name,
                COUNT(s.id) as show_count
            FROM venues v
            LEFT JOIN shows s ON v.id = s.venue_id
            GROUP BY v.id
            HAVING show_count >= 1
            ORDER BY show_count DESC, v.name
            LIMIT 10
        """)

        # Verify descending order by count
        prev_count = float('inf')
        for row in result.rows:
            name, count = row
            assert count <= prev_count
            prev_count = count

    def test_venues_sort_by_name(self, db_client):
        """Test venues sorted alphabetically"""
        result = db_client.execute("""
            SELECT
                v.name,
                COUNT(s.id) as show_count
            FROM venues v
            LEFT JOIN shows s ON v.id = s.venue_id
            GROUP BY v.id
            HAVING show_count >= 1
            ORDER BY v.name
            LIMIT 10
        """)

        # Verify alphabetical order
        names = [row[0] for row in result.rows]
        assert names == sorted(names)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
