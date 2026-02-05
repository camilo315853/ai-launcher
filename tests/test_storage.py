"""Tests for storage."""

from ai_launcher.core.models import Project
from ai_launcher.core.storage import Storage


def test_storage_initialization(tmp_path):
    """Test that storage initializes correctly."""
    db_path = tmp_path / "test.db"
    Storage(db_path)

    assert db_path.exists()


def test_add_and_get_manual_paths(mock_storage, tmp_path):
    """Test adding and retrieving manual paths."""
    path1 = tmp_path / "project1"
    path2 = tmp_path / "project2"

    path1.mkdir()
    path2.mkdir()

    mock_storage.add_manual_path(path1)
    mock_storage.add_manual_path(path2)

    paths = mock_storage.get_manual_paths()

    assert len(paths) == 2
    assert str(path1) in paths
    assert str(path2) in paths


def test_remove_manual_path(mock_storage, tmp_path):
    """Test removing a manual path."""
    path = tmp_path / "project"
    path.mkdir()

    mock_storage.add_manual_path(path)
    assert len(mock_storage.get_manual_paths()) == 1

    mock_storage.remove_manual_path(str(path))
    assert len(mock_storage.get_manual_paths()) == 0


def test_get_manual_projects_removes_nonexistent(mock_storage, tmp_path):
    """Test that non-existent manual paths are auto-removed."""
    existing_path = tmp_path / "existing"
    missing_path = tmp_path / "missing"

    existing_path.mkdir()

    mock_storage.add_manual_path(existing_path)
    mock_storage.add_manual_path(missing_path)

    # Should have 2 paths initially
    assert len(mock_storage.get_manual_paths()) == 2

    # get_manual_projects should remove the missing one
    projects = mock_storage.get_manual_projects()

    assert len(projects) == 1
    assert projects[0].path == existing_path

    # Missing path should be removed from database
    assert len(mock_storage.get_manual_paths()) == 1


def test_last_opened_tracking(mock_storage, tmp_path):
    """Test last opened project tracking."""
    path1 = tmp_path / "project1"
    path2 = tmp_path / "project2"

    # Initially no last opened
    assert mock_storage.get_last_opened() is None

    # Set last opened
    mock_storage.set_last_opened(path1)
    assert mock_storage.get_last_opened() == str(path1)

    # Update to different project
    mock_storage.set_last_opened(path2)
    assert mock_storage.get_last_opened() == str(path2)


def test_default_selection_index(mock_storage, tmp_path):
    """Test getting default selection index."""
    path1 = tmp_path / "a_project"
    path2 = tmp_path / "b_project"
    path3 = tmp_path / "c_project"

    projects = [
        Project.from_path(path1),
        Project.from_path(path2),
        Project.from_path(path3),
    ]

    # No last opened, should return 0
    assert mock_storage.get_default_selection_index(projects) == 0

    # Set last opened to middle project
    mock_storage.set_last_opened(path2)
    assert mock_storage.get_default_selection_index(projects) == 1

    # Last opened not in list, should return 0
    mock_storage.set_last_opened(tmp_path / "other")
    assert mock_storage.get_default_selection_index(projects) == 0


def test_storage_corruption_recovery(tmp_path):
    """Test that corrupted database is recovered."""
    db_path = tmp_path / "test.db"

    # Create corrupted database
    with open(db_path, "w") as f:
        f.write("corrupted data")

    # Storage should recover and create new database
    storage = Storage(db_path)

    # Should have backed up old database
    backup_files = list(tmp_path.glob("test.db.backup.*"))
    assert len(backup_files) == 1

    # New database should work
    storage.add_manual_path(tmp_path / "test")
    assert len(storage.get_manual_paths()) == 1
