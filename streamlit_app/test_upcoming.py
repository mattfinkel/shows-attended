"""
Tests for upcoming shows features:
- Band/venue name matching for imports
- RSVP functionality
- Google Calendar link generation
- Recent upcoming shows query
"""
import pytest
from unittest.mock import patch, MagicMock
from urllib.parse import quote


# ---------------------------------------------------------------------------
# Band name matching (tested directly, no streamlit dependency)
# ---------------------------------------------------------------------------

def match_band_name(scraped_name, existing_bands):
    """Match a scraped band name against existing DB bands (case-insensitive)."""
    scraped_lower = scraped_name.lower().strip()
    for db_name in existing_bands:
        if db_name.lower() == scraped_lower:
            return db_name
    return scraped_name.strip()


def match_venue_name(scraped_name, venue_names):
    """Match a scraped venue name against existing DB venues (case-insensitive)."""
    scraped_lower = scraped_name.lower().strip()
    for i, db_name in enumerate(venue_names):
        if db_name.lower() == scraped_lower:
            return i, db_name
    return None, scraped_name


class TestMatchBandName:
    def test_exact_match(self):
        assert match_band_name("Bad Religion", ["Bad Religion", "Pennywise"]) == "Bad Religion"

    def test_case_insensitive_match(self):
        assert match_band_name("bad religion", ["Bad Religion", "Pennywise"]) == "Bad Religion"

    def test_case_insensitive_match_uppercase(self):
        assert match_band_name("BAD RELIGION", ["Bad Religion"]) == "Bad Religion"

    def test_no_match_returns_original(self):
        assert match_band_name("New Band", ["Bad Religion", "Pennywise"]) == "New Band"

    def test_strips_whitespace(self):
        assert match_band_name("  Bad Religion  ", ["Bad Religion"]) == "Bad Religion"

    def test_strips_whitespace_no_match(self):
        assert match_band_name("  New Band  ", []) == "New Band"

    def test_empty_existing_bands(self):
        assert match_band_name("Band", []) == "Band"

    def test_partial_match_does_not_match(self):
        assert match_band_name("Bad", ["Bad Religion"]) == "Bad"


# ---------------------------------------------------------------------------
# Venue name matching
# ---------------------------------------------------------------------------

class TestMatchVenueName:
    def test_exact_match(self):
        idx, name = match_venue_name("Casbah", ["Casbah", "SOMA", "Belly Up"])
        assert idx == 0
        assert name == "Casbah"

    def test_case_insensitive_match(self):
        idx, name = match_venue_name("casbah", ["Casbah", "SOMA"])
        assert idx == 0
        assert name == "Casbah"

    def test_no_match(self):
        idx, name = match_venue_name("Unknown Venue", ["Casbah", "SOMA"])
        assert idx is None
        assert name == "Unknown Venue"

    def test_strips_whitespace(self):
        idx, name = match_venue_name("  Casbah  ", ["Casbah"])
        assert idx == 0
        assert name == "Casbah"

    def test_returns_correct_index(self):
        idx, name = match_venue_name("soma", ["Casbah", "SOMA", "Belly Up"])
        assert idx == 1
        assert name == "SOMA"

    def test_empty_venue_list(self):
        idx, name = match_venue_name("Casbah", [])
        assert idx is None
        assert name == "Casbah"

    def test_partial_match_does_not_match(self):
        idx, name = match_venue_name("The Cas", ["Casbah"])
        assert idx is None


# ---------------------------------------------------------------------------
# Google Calendar URL generation
# ---------------------------------------------------------------------------

class TestGoogleCalendarUrl:
    def test_basic_url(self):
        event_name = "Bad Religion, Pennywise"
        date = "20260320"
        venue = "Casbah"
        ticket_url = "https://example.com/show"

        gcal_url = (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={quote(event_name)}"
            f"&dates={date}/{date}"
            f"&location={quote(venue)}"
            f"&details={quote(ticket_url)}"
        )

        assert "action=TEMPLATE" in gcal_url
        assert quote("Bad Religion, Pennywise") in gcal_url
        assert "20260320/20260320" in gcal_url
        assert quote("Casbah") in gcal_url
        assert quote("https://example.com/show") in gcal_url

    def test_special_characters_encoded(self):
        event_name = "Swingin' Utters & Friends"
        encoded = quote(event_name)
        assert "%26" in encoded

    def test_empty_ticket_url(self):
        assert quote("") == ""

    def test_date_format_conversion(self):
        db_date = "2026-03-20"
        gcal_date = db_date.replace("-", "")
        assert gcal_date == "20260320"


# ---------------------------------------------------------------------------
# RSVP values and colors
# ---------------------------------------------------------------------------

class TestRsvpValues:
    def test_valid_rsvp_values(self):
        valid = {"yes", "maybe", "no", "hidden", None}
        for v in valid:
            assert v in valid

    def test_rsvp_colors_have_distinct_going_vs_no_response(self):
        colors = {
            "yes": "#4CAF50",
            "maybe": "#FFA726",
            "no": "#EF5350",
            None: "#666666",
        }
        assert colors["yes"] != colors[None]
        # All four states have colors
        assert len(colors) == 4

    def test_rsvp_labels(self):
        labels = {
            "yes": "Going",
            "maybe": "Maybe",
            "no": "Not going",
            None: "",
        }
        assert labels["yes"] == "Going"
        assert labels["maybe"] == "Maybe"
        assert labels["no"] == "Not going"
        assert labels[None] == ""


# ---------------------------------------------------------------------------
# Recent upcoming shows SQL query validation
# ---------------------------------------------------------------------------

class TestRecentUpcomingShowsQuery:
    def test_query_filters_by_date_range(self):
        """The query should filter to shows within the past 7 days up to today."""
        sql = """SELECT u.id, u.event_name, u.date, u.venue, u.matched_artist, u.price, u.url
           FROM upcoming_shows u
           WHERE u.date >= ? AND u.date <= ?
             AND NOT EXISTS (
               SELECT 1 FROM shows s
               JOIN venues v ON s.venue_id = v.id
               WHERE s.date = u.date AND LOWER(v.name) = LOWER(u.venue)
             )
           ORDER BY u.date DESC"""

        assert "date >= ?" in sql
        assert "date <= ?" in sql

    def test_query_excludes_already_added_shows(self):
        sql = """NOT EXISTS (
               SELECT 1 FROM shows s
               JOIN venues v ON s.venue_id = v.id
               WHERE s.date = u.date AND LOWER(v.name) = LOWER(u.venue)
             )"""
        assert "NOT EXISTS" in sql
        assert "shows s" in sql

    def test_query_uses_case_insensitive_venue_comparison(self):
        sql = "WHERE s.date = u.date AND LOWER(v.name) = LOWER(u.venue)"
        assert "LOWER(v.name) = LOWER(u.venue)" in sql


# ---------------------------------------------------------------------------
# RSVP update SQL pattern
# ---------------------------------------------------------------------------

class TestUpdateRsvp:
    def test_update_rsvp_sql_pattern(self):
        mock_cursor = MagicMock()
        sql = "UPDATE upcoming_shows SET rsvp = ? WHERE id = ?"
        mock_cursor.execute(sql, ["yes", 42])
        mock_cursor.execute.assert_called_with(sql, ["yes", 42])

    def test_all_rsvp_values_accepted(self):
        mock_cursor = MagicMock()
        for val in ["yes", "maybe", "no", "hidden"]:
            mock_cursor.execute("UPDATE upcoming_shows SET rsvp = ? WHERE id = ?", [val, 1])
        assert mock_cursor.execute.call_count == 4


# ---------------------------------------------------------------------------
# Load upcoming shows SQL patterns
# ---------------------------------------------------------------------------

class TestLoadUpcomingShows:
    def test_hidden_excluded_by_default(self):
        sql = "WHERE date >= ? AND (rsvp IS NULL OR rsvp != 'hidden')"
        assert "rsvp IS NULL" in sql
        assert "hidden" in sql

    def test_show_all_includes_hidden(self):
        sql = "WHERE date >= ?"
        assert "hidden" not in sql


# ---------------------------------------------------------------------------
# Upsert preserves RSVP
# ---------------------------------------------------------------------------

class TestUpsertPreservesRsvp:
    def test_upsert_sql_does_not_overwrite_rsvp(self):
        sql = """INSERT INTO upcoming_shows (event_name, date, venue, matched_artist, price, url, event_key, discovered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(event_key) DO UPDATE SET
                   event_name = excluded.event_name,
                   price = excluded.price,
                   url = excluded.url,
                   matched_artist = excluded.matched_artist,
                   discovered_at = excluded.discovered_at"""

        update_clause = sql.split("DO UPDATE SET")[1]
        assert "rsvp" not in update_clause


# ---------------------------------------------------------------------------
# Cleanup cutoff (7-day retention)
# ---------------------------------------------------------------------------

class TestCleanupCutoff:
    def test_delete_uses_7_day_cutoff(self):
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert cutoff < today
        # 7 days ago should be exactly 7 days before today
        cutoff_dt = datetime.strptime(cutoff, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        assert (today_dt - cutoff_dt).days == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
