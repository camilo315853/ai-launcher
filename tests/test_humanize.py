"""Tests for humanize utility functions."""

from datetime import datetime, timedelta

from ai_launcher.utils.humanize import format_time_ago, humanize_count, humanize_size


# ============================================================================
# format_time_ago() tests
# ============================================================================


def test_format_time_ago_just_now():
    """Test that recent times show 'just now'."""
    result = format_time_ago(datetime.now() - timedelta(seconds=30))
    assert result == "just now"


def test_format_time_ago_one_minute():
    """Test singular minute."""
    result = format_time_ago(datetime.now() - timedelta(minutes=1))
    assert result == "1 minute ago"


def test_format_time_ago_multiple_minutes():
    """Test plural minutes."""
    result = format_time_ago(datetime.now() - timedelta(minutes=45))
    assert result == "45 minutes ago"


def test_format_time_ago_one_hour():
    """Test singular hour."""
    result = format_time_ago(datetime.now() - timedelta(hours=1))
    assert result == "1 hour ago"


def test_format_time_ago_multiple_hours():
    """Test plural hours."""
    result = format_time_ago(datetime.now() - timedelta(hours=5))
    assert result == "5 hours ago"


def test_format_time_ago_one_day():
    """Test singular day."""
    result = format_time_ago(datetime.now() - timedelta(days=1))
    assert result == "1 day ago"


def test_format_time_ago_multiple_days():
    """Test plural days."""
    result = format_time_ago(datetime.now() - timedelta(days=3))
    assert result == "3 days ago"


def test_format_time_ago_one_week():
    """Test singular week."""
    result = format_time_ago(datetime.now() - timedelta(weeks=1))
    assert result == "1 week ago"


def test_format_time_ago_multiple_weeks():
    """Test plural weeks."""
    result = format_time_ago(datetime.now() - timedelta(weeks=4))
    assert result == "4 weeks ago"


def test_format_time_ago_boundary_59_seconds():
    """Test boundary: 59 seconds is still 'just now'."""
    result = format_time_ago(datetime.now() - timedelta(seconds=59))
    assert result == "just now"


def test_format_time_ago_boundary_60_seconds():
    """Test boundary: exactly 60 seconds becomes 1 minute."""
    result = format_time_ago(datetime.now() - timedelta(seconds=60))
    assert result == "1 minute ago"


# ============================================================================
# humanize_size() tests
# ============================================================================


def test_humanize_size_zero():
    """Test zero bytes."""
    assert humanize_size(0) == "0 B"


def test_humanize_size_bytes():
    """Test small byte values stay in bytes."""
    assert humanize_size(500) == "500 B"


def test_humanize_size_one_kb():
    """Test exact 1 KB."""
    assert humanize_size(1024) == "1 KB"


def test_humanize_size_fractional_kb():
    """Test fractional KB."""
    assert humanize_size(1536) == "1.5 KB"


def test_humanize_size_one_mb():
    """Test exact 1 MB."""
    assert humanize_size(1024 * 1024) == "1 MB"


def test_humanize_size_fractional_mb():
    """Test fractional MB."""
    assert humanize_size(int(2.5 * 1024 * 1024)) == "2.5 MB"


def test_humanize_size_one_gb():
    """Test exact 1 GB."""
    assert humanize_size(1024 * 1024 * 1024) == "1 GB"


def test_humanize_size_one_tb():
    """Test exact 1 TB."""
    assert humanize_size(1024 * 1024 * 1024 * 1024) == "1 TB"


def test_humanize_size_large_tb():
    """Test values larger than 1 TB stay in TB."""
    assert humanize_size(5 * 1024 * 1024 * 1024 * 1024) == "5 TB"


def test_humanize_size_strips_trailing_zero():
    """Test that .0 is stripped from whole numbers."""
    result = humanize_size(1024)
    assert result == "1 KB"
    assert ".0" not in result


def test_humanize_size_keeps_decimal():
    """Test that non-.0 decimals are kept."""
    result = humanize_size(1536)
    assert result == "1.5 KB"


# ============================================================================
# humanize_count() tests
# ============================================================================


def test_humanize_count_zero():
    """Test zero uses plural."""
    assert humanize_count(0, "file") == "0 files"


def test_humanize_count_one():
    """Test singular form."""
    assert humanize_count(1, "file") == "1 file"


def test_humanize_count_many():
    """Test plural form."""
    assert humanize_count(5, "file") == "5 files"


def test_humanize_count_custom_plural():
    """Test custom plural form."""
    assert humanize_count(1, "directory", "directories") == "1 directory"
    assert humanize_count(3, "directory", "directories") == "3 directories"


def test_humanize_count_default_plural_adds_s():
    """Test that default plural just adds 's'."""
    assert humanize_count(2, "item") == "2 items"
