"""Tests for preview generation."""

from pathlib import Path
from unittest.mock import Mock, patch

from ai_launcher.ui.preview import format_project_line, generate_preview


def test_generate_preview_with_claude_md(tmp_path):
    """Test preview generation with CLAUDE.md file."""
    # Create test directory with CLAUDE.md
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    claude_md = project_path / "CLAUDE.md"
    claude_md.write_text("# Test Project\n\nThis is a test.\n" + "Line\n" * 20)

    preview = generate_preview(project_path, show_git_status=False)

    assert preview.claude_md is not None
    assert "Test Project" in preview.claude_md
    # Should only include first 20 lines
    assert preview.claude_md.count("\n") <= 20


def test_generate_preview_without_claude_md(tmp_path):
    """Test preview generation without CLAUDE.md."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    preview = generate_preview(project_path, show_git_status=False)

    assert preview.claude_md is None


@patch("subprocess.run")
def test_generate_preview_with_git_status(mock_run, tmp_path):
    """Test preview with git status."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / ".git").mkdir()

    # Mock git status output
    mock_run.return_value = Mock(
        returncode=0,
        stdout=" M file.txt\n?? new.txt",
    )

    preview = generate_preview(project_path, show_git_status=True)

    assert preview.git_status is not None
    assert "file.txt" in preview.git_status


@patch("subprocess.run")
def test_generate_preview_git_clean(mock_run, tmp_path):
    """Test preview with clean git status."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / ".git").mkdir()

    # Mock clean git status
    mock_run.return_value = Mock(returncode=0, stdout="")

    preview = generate_preview(project_path, show_git_status=True)

    assert preview.git_status == "Clean working tree"


def test_generate_preview_directory_listing(tmp_path):
    """Test directory listing in preview."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create some files and directories
    (project_path / "file1.txt").touch()
    (project_path / "file2.py").touch()
    (project_path / "subdir").mkdir()

    preview = generate_preview(project_path, show_git_status=False)

    assert preview.directory_listing is not None
    assert "file1.txt" in preview.directory_listing
    assert "file2.py" in preview.directory_listing
    assert "subdir" in preview.directory_listing


def test_generate_preview_error_handling(tmp_path):
    """Test preview generation with non-existent path."""
    non_existent = tmp_path / "does-not-exist"

    preview = generate_preview(non_existent, show_git_status=False)

    # Should handle error gracefully
    assert preview.error is not None or preview.directory_listing is None


def test_preview_format():
    """Test preview content formatting."""
    from ai_launcher.core.models import PreviewContent

    preview = PreviewContent(
        claude_md="# Test\n\nContent here",
        git_status="M file.txt",
        directory_listing="file1.txt\nfile2.py",
    )

    formatted = preview.format()

    assert "=== CLAUDE.md ===" in formatted
    assert "=== Git Status ===" in formatted
    assert "=== Directory ===" in formatted
    assert "Content here" in formatted
    assert "file.txt" in formatted


def test_preview_format_with_error():
    """Test preview formatting with error."""
    from ai_launcher.core.models import PreviewContent

    preview = PreviewContent(error="Something went wrong")

    formatted = preview.format()

    assert "ERROR:" in formatted
    assert "Something went wrong" in formatted


def test_format_project_line_basic():
    """Test basic project line formatting."""
    path = Path("/home/user/projects/my-project")
    parent = Path("/home/user/projects")

    result = format_project_line(path, parent, is_git=True, is_manual=False)

    assert "my-project" in result
    assert "[git]" in result


def test_format_project_line_manual():
    """Test formatting for manual project."""
    path = Path("/home/user/custom/project")
    parent = Path("/home/user/custom")

    result = format_project_line(path, parent, is_git=False, is_manual=True)

    assert "[manual]" in result
    assert "[git]" not in result


def test_format_project_line_git_and_manual():
    """Test formatting for git repo that's also manual."""
    path = Path("/home/user/project")
    parent = Path("/home/user")

    result = format_project_line(path, parent, is_git=True, is_manual=True)

    assert "[git,manual]" in result or "[manual,git]" in result


def test_format_project_line_no_markers():
    """Test formatting with no markers."""
    path = Path("/home/user/project")
    parent = Path("/home/user")

    result = format_project_line(path, parent, is_git=False, is_manual=False)

    assert "[" not in result
    assert "project" in result


@patch("subprocess.run")
def test_generate_preview_git_timeout(mock_run, tmp_path):
    """Test that git timeout is handled gracefully."""
    import subprocess

    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / ".git").mkdir()

    # Mock git command timeout
    mock_run.side_effect = subprocess.TimeoutExpired("git", 2)

    preview = generate_preview(project_path, show_git_status=True)

    # Should not crash, git status should be None or empty
    # Directory listing should still work
    assert preview.directory_listing is not None
