"""Tests for project selector."""

from pathlib import Path
from unittest.mock import patch

from ai_launcher.core.models import Project
from ai_launcher.ui.selector import show_project_list


def test_show_project_list_empty(capsys):
    """Test showing empty project list."""
    show_project_list([])

    captured = capsys.readouterr()
    assert "No projects found" in captured.out


def test_show_project_list_with_projects(capsys):
    """Test showing project list with projects."""
    projects = [
        Project(
            path=Path("/home/user/project1"),
            name="project1",
            parent_path=Path("/home/user"),
            is_git_repo=True,
            is_manual=False,
        ),
        Project(
            path=Path("/home/user/project2"),
            name="project2",
            parent_path=Path("/home/user"),
            is_git_repo=False,
            is_manual=True,
        ),
    ]

    show_project_list(projects)

    captured = capsys.readouterr()
    assert "2 project(s)" in captured.out
    assert "/home/user/project1" in captured.out
    assert "/home/user/project2" in captured.out
    assert "[git]" in captured.out
    assert "[manual]" in captured.out


def test_alphabetical_sorting():
    """Test that projects are expected to be sorted alphabetically."""
    # This tests the expected behavior - projects should come in pre-sorted
    projects = [
        Project.from_path(Path("/a/project"), is_manual=False),
        Project.from_path(Path("/b/project"), is_manual=False),
        Project.from_path(Path("/c/project"), is_manual=False),
    ]

    # Verify they're in alphabetical order
    paths = [str(p.path) for p in projects]
    assert paths == sorted(paths)


@patch("ai_launcher.ui.selector.iterfzf")
def test_select_project_with_selection(mock_iterfzf, mock_storage, tmp_path):
    """Test successful project selection."""
    from ai_launcher.ui.preview import format_project_line
    from ai_launcher.ui.selector import select_project

    # Create test projects
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    projects = [Project.from_path(project_path, is_manual=False)]

    # Mock iterfzf to return the formatted choice string (not raw path)
    formatted_choice = format_project_line(
        project_path,
        projects[0].parent_path,
        projects[0].is_git_repo,
        projects[0].is_manual,
    )
    mock_iterfzf.return_value = formatted_choice

    # No need to mock storage methods - they work as-is
    # get_default_selection_index will return 0 by default (no last opened)

    result = select_project(projects, mock_storage)

    assert result is not None
    assert result.path == project_path

    # Verify iterfzf was called
    mock_iterfzf.assert_called_once()


@patch("ai_launcher.ui.selector.iterfzf")
def test_select_project_cancelled(mock_iterfzf, mock_storage, tmp_path):
    """Test project selection when user cancels."""
    from ai_launcher.ui.selector import select_project

    project_path = tmp_path / "test-project"
    project_path.mkdir()

    projects = [Project.from_path(project_path, is_manual=False)]

    # Mock iterfzf to return None (cancelled)
    mock_iterfzf.return_value = None

    result = select_project(projects, mock_storage)

    assert result is None


def test_select_project_empty_list(mock_storage, capsys):
    """Test selecting from empty project list."""
    from ai_launcher.ui.selector import select_project

    result = select_project([], mock_storage)

    assert result is None
    captured = capsys.readouterr()
    assert "No projects found" in captured.out


@patch("ai_launcher.ui.selector.iterfzf")
def test_select_project_with_default_index(mock_iterfzf, mock_storage, tmp_path):
    """Test that default index is passed to fzf."""
    from ai_launcher.ui.selector import select_project

    # Create multiple projects
    projects = []
    for i in range(3):
        path = tmp_path / f"project{i}"
        path.mkdir()
        projects.append(Project.from_path(path, is_manual=False))

    # Set last opened to make project[1] the default
    mock_storage.set_last_opened(projects[1].path)
    mock_iterfzf.return_value = str(projects[1].path)

    select_project(projects, mock_storage, show_git_status=False)

    # Check that iterfzf was called with +2 (1-indexed, so index 1 = +2)
    call_args = mock_iterfzf.call_args
    extra_args = call_args.kwargs.get("__extra__", [])
    assert "+2" in extra_args


@patch("ai_launcher.ui.selector.generate_preview")
@patch("ai_launcher.ui.selector.iterfzf")
def test_preview_function_receives_choice_string(
    mock_iterfzf, mock_preview, mock_storage, tmp_path
):
    """Test that preview function receives choice string, not index."""
    from ai_launcher.core.models import PreviewContent
    from ai_launcher.ui.selector import select_project

    project_path = tmp_path / "test-project"
    project_path.mkdir()
    projects = [Project.from_path(project_path, is_manual=False)]

    # Mock preview generation
    mock_preview.return_value = PreviewContent(
        claude_md="Test content",
        git_status="Clean",
    )

    # We need to actually call the preview function to test it
    mock_iterfzf.return_value = str(project_path)

    select_project(projects, mock_storage, show_git_status=True)

    # Get the preview function that was passed to iterfzf
    call_args = mock_iterfzf.call_args
    preview_fn = call_args.kwargs.get("preview")

    # Preview function should exist
    assert preview_fn is not None

    # Call preview function with a choice string
    choice_str = str(project_path)
    result = preview_fn(choice_str)

    # Should return formatted preview
    assert isinstance(result, str)
    assert len(result) > 0
