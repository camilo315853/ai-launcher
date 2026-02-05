"""Tests for project discovery."""

from pathlib import Path

from ai_launcher.core.discovery import get_all_projects, scan_for_git_repos


def test_scan_for_git_repos(tmp_project_dir):
    """Test git repository scanning."""
    projects = scan_for_git_repos(
        [tmp_project_dir],
        max_depth=5,
        prune_dirs=["node_modules", ".cache"],
    )

    # Should find project1, project2, and work/project3
    assert len(projects) == 3

    # All should be git repos
    assert all(p.is_git_repo for p in projects)

    # None should be manual
    assert all(not p.is_manual for p in projects)

    # Should not include node_modules or .cache
    paths = {str(p.path) for p in projects}
    assert not any("node_modules" in p for p in paths)
    assert not any(".cache" in p for p in paths)


def test_scan_respects_max_depth(tmp_path):
    """Test that max_depth is respected."""
    # Create deep directory structure
    deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
    (deep_path / ".git").mkdir(parents=True)

    # Scan with max_depth=3
    projects = scan_for_git_repos([tmp_path], max_depth=3, prune_dirs=[])

    # Should not find the deep repo
    assert len(projects) == 0

    # Scan with max_depth=5
    projects = scan_for_git_repos([tmp_path], max_depth=5, prune_dirs=[])

    # Should find it now
    assert len(projects) == 1


def test_get_all_projects_removes_duplicates(tmp_project_dir, mock_storage):
    """Test that manual and discovered projects are deduplicated."""
    # Add manual project that overlaps with discovered
    manual_path = tmp_project_dir / "project1"
    mock_storage.add_manual_path(manual_path)

    manual_projects = mock_storage.get_manual_projects()

    all_projects = get_all_projects(
        [tmp_project_dir],
        max_depth=5,
        prune_dirs=["node_modules", ".cache"],
        manual_projects=manual_projects,
    )

    # Should have 3 unique projects (project1 appears in both but deduplicated)
    assert len(all_projects) == 3

    # The project1 entry should be marked as manual (manual takes precedence)
    project1 = next(p for p in all_projects if p.path == manual_path)
    assert project1.is_manual


def test_get_all_projects_alphabetical_sort(tmp_project_dir):
    """Test that projects are sorted alphabetically."""
    projects = get_all_projects(
        [tmp_project_dir],
        max_depth=5,
        prune_dirs=["node_modules", ".cache"],
        manual_projects=[],
    )

    # Check that projects are sorted by path
    paths = [str(p.path) for p in projects]
    assert paths == sorted(paths)


def test_scan_handles_missing_directory():
    """Test that scanning handles non-existent directories gracefully."""
    projects = scan_for_git_repos(
        [Path("/nonexistent/path")],
        max_depth=5,
        prune_dirs=[],
    )

    # Should return empty list, not crash
    assert projects == []
