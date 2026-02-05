"""Integration tests for claude-launcher."""

from ai_launcher.core.config import ConfigManager
from ai_launcher.core.discovery import get_all_projects
from ai_launcher.core.storage import Storage


def test_full_workflow(tmp_path):
    """Test complete workflow from config to project selection."""
    # Setup: Create config
    config_path = tmp_path / "config" / "config.toml"
    config_path.parent.mkdir(parents=True)

    manager = ConfigManager(config_path)
    config = manager._get_defaults()

    # Create project structure
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    (projects_dir / "project-a" / ".git").mkdir(parents=True)
    (projects_dir / "project-b" / ".git").mkdir(parents=True)

    config.scan.paths = [projects_dir]
    manager.save(config)

    # Load config
    loaded_config = manager.load()
    assert len(loaded_config.scan.paths) == 1

    # Initialize storage
    db_path = tmp_path / "data" / "projects.db"
    storage = Storage(db_path)

    # Get projects
    manual_projects = storage.get_manual_projects()
    all_projects = get_all_projects(
        loaded_config.scan.paths,
        loaded_config.scan.max_depth,
        loaded_config.scan.prune_dirs,
        manual_projects,
    )

    # Should find both projects
    assert len(all_projects) == 2

    # Projects should be alphabetically sorted
    assert all_projects[0].name == "project-a"
    assert all_projects[1].name == "project-b"

    # Record last opened
    storage.set_last_opened(all_projects[1].path)

    # Get default selection
    default_index = storage.get_default_selection_index(all_projects)
    assert default_index == 1  # project-b


def test_manual_and_discovered_integration(tmp_path):
    """Test integration of manual and discovered projects."""
    # Setup directories
    discovered_dir = tmp_path / "discovered"
    manual_dir = tmp_path / "manual"

    (discovered_dir / "discovered-repo" / ".git").mkdir(parents=True)
    manual_dir.mkdir(parents=True)

    # Setup storage
    storage = Storage(tmp_path / "test.db")
    storage.add_manual_path(manual_dir)

    # Get all projects
    manual_projects = storage.get_manual_projects()
    all_projects = get_all_projects(
        [discovered_dir],
        5,
        ["node_modules"],
        manual_projects,
    )

    # Should have both projects
    assert len(all_projects) == 2

    # One should be manual, one discovered
    manual_count = sum(1 for p in all_projects if p.is_manual)
    discovered_count = sum(1 for p in all_projects if not p.is_manual)

    assert manual_count == 1
    assert discovered_count == 1


def test_error_recovery_integration(tmp_path):
    """Test that system recovers from errors gracefully."""
    db_path = tmp_path / "test.db"

    # Create corrupted database
    with open(db_path, "w") as f:
        f.write("corrupted")

    # Storage should recover
    storage = Storage(db_path)

    # Should be able to use storage normally
    storage.add_manual_path(tmp_path / "test")
    assert len(storage.get_manual_paths()) == 1

    # Backup should exist
    backups = list(tmp_path.glob("test.db.backup.*"))
    assert len(backups) == 1


def test_empty_config_workflow(tmp_path):
    """Test workflow with empty/new configuration."""
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    # Load non-existent config (should get defaults)
    config = manager.load()

    assert config.scan.paths == []
    assert config.scan.max_depth == 5

    # With empty scan paths, should get empty project list
    Storage(tmp_path / "test.db")
    all_projects = get_all_projects(
        config.scan.paths,
        config.scan.max_depth,
        config.scan.prune_dirs,
        [],
    )

    assert all_projects == []
