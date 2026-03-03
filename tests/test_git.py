"""Tests for git utilities."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ai_launcher.utils.git import clone_repository

# ============================================================================
# clone_repository() tests
# ============================================================================


def test_clone_repository_url_validation():
    """Test that invalid URLs are rejected."""
    with pytest.raises(ValueError, match="Invalid git URL"):
        clone_repository("invalid-url", Path("/tmp"), None)

    with pytest.raises(ValueError, match="Invalid git URL"):
        clone_repository("ftp://example.com/repo", Path("/tmp"), None)


def test_clone_repository_https_url_accepted(tmp_path):
    """Test that HTTPS URLs are accepted."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        result = clone_repository("https://github.com/user/repo.git", tmp_path, None)
        assert result == tmp_path / "repo"


def test_clone_repository_ssh_url_accepted(tmp_path):
    """Test that SSH URLs (git@) are accepted."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        result = clone_repository("git@github.com:user/repo.git", tmp_path, None)
        assert result == tmp_path / "repo"


def test_clone_repository_existing_directory(tmp_path):
    """Test that cloning to existing directory is rejected."""
    # Create existing directory with the same name as the repo in the URL
    existing = tmp_path / "repo"
    existing.mkdir()

    with pytest.raises(ValueError, match="already exists"):
        clone_repository("https://github.com/user/repo.git", tmp_path, None)


def test_clone_repository_existing_directory_with_subfolder(tmp_path):
    """Test that cloning to existing directory in subfolder is rejected."""
    # Create existing directory
    subfolder = tmp_path / "projects"
    subfolder.mkdir()
    existing = subfolder / "repo"
    existing.mkdir()

    with pytest.raises(ValueError, match="already exists"):
        clone_repository("https://github.com/user/repo.git", tmp_path, "projects")


@patch("subprocess.run")
def test_clone_repository_success(mock_run, tmp_path):
    """Test successful repository cloning."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    result = clone_repository(
        "https://github.com/user/my-repo.git",
        tmp_path,
        "projects",
    )

    expected_path = tmp_path / "projects" / "my-repo"
    assert result == expected_path

    # Check that git clone was called correctly
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "git"
    assert args[1] == "clone"
    assert args[2] == "https://github.com/user/my-repo.git"
    assert args[3] == str(expected_path)


@patch("subprocess.run")
def test_clone_repository_success_no_subfolder(mock_run, tmp_path):
    """Test successful repository cloning without subfolder."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    result = clone_repository(
        "https://github.com/user/my-repo.git",
        tmp_path,
        None,
    )

    expected_path = tmp_path / "my-repo"
    assert result == expected_path

    # Verify the target path
    args = mock_run.call_args[0][0]
    assert args[3] == str(expected_path)


@patch("subprocess.run")
def test_clone_repository_git_failure(mock_run, tmp_path):
    """Test handling of git clone failure."""
    mock_run.side_effect = subprocess.CalledProcessError(
        1, "git", stderr="Authentication failed"
    )

    with pytest.raises(RuntimeError, match="Git clone failed"):
        clone_repository("https://github.com/user/repo.git", tmp_path, None)


@patch("subprocess.run")
def test_clone_repository_git_failure_with_stderr(mock_run, tmp_path):
    """Test handling of git clone failure with stderr message."""
    error = subprocess.CalledProcessError(128, "git")
    error.stderr = "fatal: repository not found"
    mock_run.side_effect = error

    with pytest.raises(RuntimeError, match="fatal: repository not found"):
        clone_repository("https://github.com/user/repo.git", tmp_path, None)


@patch("subprocess.run")
def test_clone_repository_git_failure_without_stderr(mock_run, tmp_path):
    """Test handling of git clone failure without stderr message."""
    error = subprocess.CalledProcessError(128, "git")
    error.stderr = ""
    mock_run.side_effect = error

    with pytest.raises(RuntimeError, match="Git clone failed"):
        clone_repository("https://github.com/user/repo.git", tmp_path, None)


@patch("subprocess.run")
def test_clone_repository_git_not_found(mock_run, tmp_path):
    """Test handling when git command is not found."""
    mock_run.side_effect = FileNotFoundError("git not found")

    with pytest.raises(RuntimeError, match="Git command not found"):
        clone_repository("https://github.com/user/repo.git", tmp_path, None)


@patch("subprocess.run")
def test_clone_repository_creates_parent_directory(mock_run, tmp_path):
    """Test that parent directories are created if they don't exist."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    # Use a subfolder that doesn't exist yet
    result = clone_repository(
        "https://github.com/user/repo.git",
        tmp_path,
        "deep/nested/path",
    )

    expected_path = tmp_path / "deep" / "nested" / "path" / "repo"
    assert result == expected_path

    # Verify parent was created
    assert expected_path.parent.exists()


def test_clone_extracts_repo_name():
    """Test that repository name is correctly extracted from URL."""
    test_cases = [
        ("https://github.com/user/repo.git", "repo"),
        ("https://github.com/user/repo", "repo"),
        ("git@github.com:user/repo.git", "repo"),
        ("https://gitlab.com/user/my-project.git", "my-project"),
        ("https://github.com/user/repo/", "repo"),
        ("git@bitbucket.org:user/my-app.git", "my-app"),
    ]

    for url, expected_name in test_cases:
        extracted = url.rstrip("/").split("/")[-1].replace(".git", "")
        assert extracted == expected_name


@patch("subprocess.run")
def test_clone_repository_strips_dotgit(mock_run, tmp_path):
    """Test that .git suffix is properly removed from repo name."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    result = clone_repository("https://github.com/user/repo.git", tmp_path, None)
    assert result == tmp_path / "repo"
    assert ".git" not in str(result)


@patch("subprocess.run")
def test_clone_repository_handles_trailing_slash(mock_run, tmp_path):
    """Test that URLs with trailing slashes are handled correctly."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    result = clone_repository("https://github.com/user/repo.git/", tmp_path, None)
    assert result == tmp_path / "repo"
