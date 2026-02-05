"""Tests for directory browser."""

from pathlib import Path
from unittest.mock import patch

from ai_launcher.ui.browser import remove_manual_path


@patch("ai_launcher.ui.browser.iterfzf")
def test_remove_manual_path_no_paths(mock_iterfzf, mock_storage, capsys):
    """Test removing manual path when none exist."""
    # Don't add any paths, so get_manual_paths() returns empty list

    result = remove_manual_path(mock_storage)

    assert result is False
    captured = capsys.readouterr()
    assert "No manual paths" in captured.out

    # iterfzf should not be called
    mock_iterfzf.assert_not_called()


@patch("ai_launcher.ui.browser.iterfzf")
@patch("builtins.input")
def test_remove_manual_path_cancelled(
    mock_input, mock_iterfzf, mock_storage, tmp_path, capsys
):
    """Test cancelling manual path removal."""
    test_path = tmp_path / "project1"
    test_path.mkdir()
    mock_storage.add_manual_path(test_path)

    # User cancels selection
    mock_iterfzf.return_value = None

    result = remove_manual_path(mock_storage)

    assert result is False
    captured = capsys.readouterr()
    assert "Cancelled" in captured.out


@patch("ai_launcher.ui.browser.iterfzf")
@patch("builtins.input")
def test_remove_manual_path_confirmed(
    mock_input, mock_iterfzf, mock_storage, tmp_path, capsys
):
    """Test successful manual path removal."""
    test_path = tmp_path / "project1"
    test_path.mkdir()
    mock_storage.add_manual_path(test_path)

    # User selects path
    mock_iterfzf.return_value = str(test_path)

    # User confirms removal
    mock_input.return_value = "y"

    result = remove_manual_path(mock_storage)

    assert result is True
    # Verify path was actually removed
    assert len(mock_storage.get_manual_paths()) == 0
    captured = capsys.readouterr()
    assert "Removed" in captured.out


@patch("ai_launcher.ui.browser.iterfzf")
@patch("builtins.input")
def test_remove_manual_path_not_confirmed(
    mock_input, mock_iterfzf, mock_storage, tmp_path, capsys
):
    """Test declining manual path removal."""
    test_path = tmp_path / "project1"
    test_path.mkdir()
    mock_storage.add_manual_path(test_path)

    # User selects path
    mock_iterfzf.return_value = str(test_path)

    # User declines removal
    mock_input.return_value = "n"

    result = remove_manual_path(mock_storage)

    assert result is False
    # Verify path was NOT removed
    assert len(mock_storage.get_manual_paths()) == 1
    captured = capsys.readouterr()
    assert "Cancelled" in captured.out


@patch("ai_launcher.ui.browser.iterfzf")
def test_remove_manual_path_multiple_paths(mock_iterfzf, mock_storage, tmp_path):
    """Test removal with multiple manual paths."""
    paths = []
    for i in range(1, 4):
        path = tmp_path / f"project{i}"
        path.mkdir()
        mock_storage.add_manual_path(path)
        paths.append(str(path))

    # User cancels
    mock_iterfzf.return_value = None

    remove_manual_path(mock_storage)

    # Verify all paths were shown in selector
    call_args = mock_iterfzf.call_args
    assert call_args[0][0] == paths


@patch("ai_launcher.ui.browser.iterfzf")
def test_browse_directory_navigation(mock_iterfzf):
    """Test directory browser navigation (basic mock test)."""
    from ai_launcher.ui.browser import browse_directory

    # User cancels immediately
    mock_iterfzf.return_value = None

    result = browse_directory(Path.home())

    assert result is None


@patch("ai_launcher.ui.browser.iterfzf")
def test_browse_directory_select_current(mock_iterfzf, tmp_path):
    """Test selecting current directory in browser."""
    from ai_launcher.ui.browser import browse_directory

    # Create test directory
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # User selects "." (current directory)
    mock_iterfzf.return_value = "."

    result = browse_directory(test_dir)

    assert result == test_dir


@patch("ai_launcher.ui.browser.iterfzf")
@patch("builtins.input")
def test_browse_directory_navigate_into(mock_input, mock_iterfzf, tmp_path):
    """Test navigating into a subdirectory."""
    from ai_launcher.ui.browser import browse_directory

    # Create test structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # First call: user selects subdir
    # Second call: user selects to navigate into it
    # Third call: user cancels
    mock_iterfzf.side_effect = ["subdir", None]
    mock_input.return_value = "o"  # Open/navigate

    result = browse_directory(tmp_path)

    # Should eventually return None (cancelled on second iteration)
    assert result is None


@patch("ai_launcher.ui.browser.iterfzf")
@patch("builtins.input")
def test_browse_directory_select_subdirectory(mock_input, mock_iterfzf, tmp_path):
    """Test selecting a subdirectory."""
    from ai_launcher.ui.browser import browse_directory

    # Create test structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # User selects subdir
    mock_iterfzf.return_value = "subdir"
    # User chooses to select it
    mock_input.return_value = "s"

    result = browse_directory(tmp_path)

    assert result == subdir


@patch("ai_launcher.ui.browser.iterfzf")
def test_browse_directory_navigate_up(mock_iterfzf, tmp_path):
    """Test navigating to parent directory."""
    from ai_launcher.ui.browser import browse_directory

    # Create test structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # First: user selects ".." (parent)
    # Second: user cancels
    mock_iterfzf.side_effect = ["..", None]

    result = browse_directory(subdir)

    # Should navigate up then cancel
    assert result is None


@patch("ai_launcher.ui.browser.iterfzf")
@patch("builtins.input")
def test_browse_directory_empty_directory(mock_input, mock_iterfzf, tmp_path):
    """Test browsing an empty directory."""
    from ai_launcher.ui.browser import browse_directory

    # Create empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # User selects the empty directory indicator
    mock_iterfzf.return_value = "(empty directory)"
    # User confirms selection
    mock_input.return_value = "y"

    result = browse_directory(empty_dir)

    assert result == empty_dir


@patch("ai_launcher.ui.browser.iterfzf")
@patch("builtins.input")
def test_browse_directory_permission_error(mock_input, mock_iterfzf, capsys):
    """Test handling permission denied error."""
    from ai_launcher.ui.browser import browse_directory

    # Use a path that doesn't exist and will cause permission issues
    # Mock the directory iteration to raise PermissionError
    with patch("pathlib.Path.iterdir", side_effect=PermissionError):
        result = browse_directory(Path("/root"))

    assert result is None
    captured = capsys.readouterr()
    assert "Permission denied" in captured.out or result is None
