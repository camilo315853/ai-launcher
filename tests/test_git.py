"""Tests for git utilities."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ai_launcher.utils.git import clone_repository, interactive_clone

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


# ============================================================================
# interactive_clone() tests
# ============================================================================


@patch("builtins.input")
def test_interactive_clone_empty_url(mock_input):
    """Test that empty URL cancels the operation."""
    mock_input.return_value = ""

    storage = Mock()
    result = interactive_clone(storage)

    assert result is None
    storage.add_manual_path.assert_not_called()


@patch("builtins.input")
def test_interactive_clone_invalid_url(mock_input):
    """Test that invalid URL shows error and returns None."""
    mock_input.return_value = "invalid-url"

    storage = Mock()
    result = interactive_clone(storage)

    assert result is None
    storage.add_manual_path.assert_not_called()


@patch("builtins.input")
def test_interactive_clone_ftp_url_rejected(mock_input):
    """Test that FTP URLs are rejected."""
    mock_input.return_value = "ftp://example.com/repo"

    storage = Mock()
    result = interactive_clone(storage)

    assert result is None


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_choice1_home_directory(mock_input, mock_run, tmp_path):
    """Test cloning to home directory (choice 1)."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "1",  # Home directory
        "n",  # Don't add to manual paths
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is None  # Because we said no to launch
    storage.add_manual_path.assert_not_called()


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_choice2_projects_directory(mock_input, mock_run, tmp_path):
    """Test cloning to ~/projects directory (choice 2)."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "2",  # ~/projects
        "n",  # Don't add to manual paths
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is None
    # Verify git was called with projects subfolder
    args = mock_run.call_args[0][0]
    assert "projects" in args[3]


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_choice3_work_directory(mock_input, mock_run, tmp_path):
    """Test cloning to ~/work directory (choice 3)."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "3",  # ~/work
        "n",  # Don't add to manual paths
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is None
    # Verify git was called with work subfolder
    args = mock_run.call_args[0][0]
    assert "work" in args[3]


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_choice4_custom_path(mock_input, mock_run, tmp_path):
    """Test cloning to custom path (choice 4)."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    custom_path = str(tmp_path / "custom")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "4",  # Custom path
        custom_path,  # Custom path value
        "n",  # Don't add to manual paths
        "n",  # Don't launch
    ]

    storage = Mock()
    result = interactive_clone(storage)

    assert result is None
    # Verify git was called with custom path
    args = mock_run.call_args[0][0]
    assert custom_path in args[3]


@patch("builtins.input")
def test_interactive_clone_custom_path_empty_cancels(mock_input):
    """Test that empty custom path cancels the operation."""
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "4",  # Custom path
        "",  # Empty custom path
    ]

    storage = Mock()
    result = interactive_clone(storage)

    assert result is None
    storage.add_manual_path.assert_not_called()


@patch("builtins.input")
def test_interactive_clone_invalid_choice(mock_input):
    """Test that invalid choice shows error and returns None."""
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "5",  # Invalid choice
    ]

    storage = Mock()
    result = interactive_clone(storage)

    assert result is None


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_add_to_manual_paths(mock_input, mock_run, tmp_path):
    """Test adding cloned repo to manual paths."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "1",  # Home directory
        "y",  # Add to manual paths
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is None
    # Verify add_manual_path was called
    storage.add_manual_path.assert_called_once()
    called_path = storage.add_manual_path.call_args[0][0]
    assert "repo" in str(called_path)


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_launch_claude(mock_input, mock_run, tmp_path):
    """Test launching Claude after clone."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "1",  # Home directory
        "n",  # Don't add to manual paths
        "y",  # Launch Claude
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is not None
    assert "repo" in str(result)


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_add_and_launch(mock_input, mock_run, tmp_path):
    """Test adding to manual paths and launching Claude."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "1",  # Home directory
        "y",  # Add to manual paths
        "y",  # Launch Claude
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is not None
    storage.add_manual_path.assert_called_once()


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_git_failure(mock_input, mock_run, tmp_path):
    """Test handling of git clone failure in interactive mode."""
    mock_run.side_effect = subprocess.CalledProcessError(
        1, "git", stderr="Authentication failed"
    )
    mock_input.side_effect = [
        "https://github.com/user/private-repo.git",  # URL
        "1",  # Home directory
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is None
    storage.add_manual_path.assert_not_called()


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_existing_directory_error(mock_input, mock_run, tmp_path):
    """Test handling when target directory already exists."""
    # Create the directory that would be cloned to
    existing = tmp_path / "repo"
    existing.mkdir()

    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "1",  # Home directory
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is None
    storage.add_manual_path.assert_not_called()


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_custom_path_with_tilde(mock_input, mock_run, tmp_path):
    """Test that tilde in custom path is expanded."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "4",  # Custom path
        "~/test",  # Path with tilde
        "n",  # Don't add to manual paths
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    # Verify the path was expanded and resolved
    assert result is None
    args = mock_run.call_args[0][0]
    # The path should be expanded (no tilde in the final path)
    assert "~" not in args[3]


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_ssh_url(mock_input, mock_run, tmp_path):
    """Test cloning with SSH URL format."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "git@github.com:user/repo.git",  # SSH URL
        "1",  # Home directory
        "n",  # Don't add to manual paths
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        result = interactive_clone(storage)

    assert result is None
    # Verify git was called with SSH URL
    args = mock_run.call_args[0][0]
    assert args[2] == "git@github.com:user/repo.git"


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_no_manual_path_lowercase_n(mock_input, mock_run, tmp_path):
    """Test that lowercase 'n' is recognized for not adding to manual paths."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "1",  # Home directory
        "n",  # Don't add to manual paths (lowercase)
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        interactive_clone(storage)

    storage.add_manual_path.assert_not_called()


@patch("subprocess.run")
@patch("builtins.input")
def test_interactive_clone_manual_path_uppercase_y(mock_input, mock_run, tmp_path):
    """Test that uppercase 'Y' is recognized (case insensitive due to .lower())."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    mock_input.side_effect = [
        "https://github.com/user/repo.git",  # URL
        "1",  # Home directory
        "Y",  # Uppercase Y (should work due to .lower())
        "n",  # Don't launch
    ]

    storage = Mock()
    with patch("pathlib.Path.home", return_value=tmp_path):
        interactive_clone(storage)

    # The code uses .lower(), so "Y" should be recognized and add to manual paths
    storage.add_manual_path.assert_called_once()
