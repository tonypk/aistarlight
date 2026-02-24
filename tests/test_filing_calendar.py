"""Unit tests for the filing calendar service."""

from datetime import date
from unittest.mock import patch

from backend.services.filing_calendar import generate_filing_calendar


class TestFilingCalendar:
    """Filing calendar generation tests."""

    @patch("backend.services.filing_calendar.date")
    def test_returns_events_sorted_by_deadline(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events = generate_filing_calendar(year=2026, months_ahead=3)

        deadlines = [e["deadline"] for e in events]
        assert deadlines == sorted(deadlines)

    @patch("backend.services.filing_calendar.date")
    def test_includes_monthly_forms(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events = generate_filing_calendar(year=2026, months_ahead=2)
        forms = {e["form"] for e in events}

        assert "BIR 2550M" in forms
        assert "BIR 1601-C" in forms
        assert "BIR 0619-E" in forms

    @patch("backend.services.filing_calendar.date")
    def test_overdue_status(self, mock_date):
        mock_date.today.return_value = date(2026, 2, 25)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events = generate_filing_calendar(year=2026, months_ahead=1)
        overdue = [e for e in events if e["status"] == "overdue"]

        # Deadlines before Feb 25 should be overdue
        for e in overdue:
            assert e["days_remaining"] < 0

    @patch("backend.services.filing_calendar.date")
    def test_upcoming_status_within_7_days(self, mock_date):
        mock_date.today.return_value = date(2026, 2, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events = generate_filing_calendar(year=2026, months_ahead=1)
        upcoming = [e for e in events if e["status"] == "upcoming"]

        for e in upcoming:
            assert 0 <= e["days_remaining"] <= 7

    @patch("backend.services.filing_calendar.date")
    def test_scheduled_status_beyond_7_days(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events = generate_filing_calendar(year=2026, months_ahead=3)
        scheduled = [e for e in events if e["status"] == "scheduled"]

        for e in scheduled:
            assert e["days_remaining"] > 7

    @patch("backend.services.filing_calendar.date")
    def test_annual_forms_included(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events = generate_filing_calendar(year=2026, months_ahead=6)
        forms = {e["form"] for e in events}

        # Annual forms due Jan 31 or Apr 15
        assert "BIR 0605" in forms  # Jan 31
        assert "BIR 1701" in forms  # Apr 15

    @patch("backend.services.filing_calendar.date")
    def test_event_has_required_fields(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events = generate_filing_calendar(year=2026, months_ahead=1)

        assert len(events) > 0
        for e in events:
            assert "form" in e
            assert "name" in e
            assert "period" in e
            assert "deadline" in e
            assert "days_remaining" in e
            assert e["status"] in ("overdue", "upcoming", "scheduled")

    @patch("backend.services.filing_calendar.date")
    def test_months_ahead_limits_range(self, mock_date):
        mock_date.today.return_value = date(2026, 6, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        events_1 = generate_filing_calendar(year=2026, months_ahead=1)
        events_12 = generate_filing_calendar(year=2026, months_ahead=12)

        assert len(events_12) >= len(events_1)
