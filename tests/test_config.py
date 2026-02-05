"""Tests for configuration management."""

from pathlib import Path

from ai_launcher.core.config import ConfigManager
from ai_launcher.core.models import ConfigData


def test_config_defaults(tmp_path):
    """Test default configuration values."""
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    config = manager.load()

    assert isinstance(config, ConfigData)
    assert config.scan.max_depth == 5
    assert config.ui.preview_width == 70
    assert config.ui.show_git_status is True
    assert config.history.max_entries == 50


def test_config_save_and_load(tmp_path):
    """Test saving and loading configuration."""
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    # Create config with custom values
    config = manager._get_defaults()
    config.scan.paths = [Path("/home/user/projects")]
    config.scan.max_depth = 3
    config.ui.preview_width = 80

    # Save
    manager.save(config)
    assert config_path.exists()

    # Load
    loaded_config = manager.load()

    assert loaded_config.scan.max_depth == 3
    assert loaded_config.ui.preview_width == 80
    assert len(loaded_config.scan.paths) == 1


def test_config_path_expansion(tmp_path):
    """Test that paths are expanded correctly."""
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    # Test tilde expansion
    expanded = manager._expand_path("~/projects")
    assert "~" not in str(expanded)
    assert expanded.is_absolute()


def test_config_handles_invalid_file(tmp_path):
    """Test that invalid config falls back to defaults."""
    config_path = tmp_path / "config.toml"

    # Create invalid TOML
    with open(config_path, "w") as f:
        f.write("invalid toml {]}")

    manager = ConfigManager(config_path)
    config = manager.load()

    # Should fall back to defaults
    assert config.scan.max_depth == 5


def test_config_missing_keys_use_defaults(tmp_path):
    """Test that missing config keys use defaults."""
    config_path = tmp_path / "config.toml"

    # Create minimal config
    with open(config_path, "w") as f:
        f.write("[scan]\npaths = []")

    manager = ConfigManager(config_path)
    config = manager.load()

    # Should have defaults for missing keys
    assert config.scan.max_depth == 5
    assert config.ui.preview_width == 70


def test_get_data_dir():
    """Test getting data directory."""
    from ai_launcher.core.config import get_data_dir

    data_dir = get_data_dir()

    assert data_dir.exists()
    assert data_dir.is_dir()
    assert "claude-launcher" in str(data_dir)


def test_get_database_path():
    """Test getting database path."""
    from ai_launcher.core.config import get_database_path

    db_path = get_database_path()

    assert db_path.name == "projects.db"
    assert "claude-launcher" in str(db_path.parent)


def test_config_multiple_paths(tmp_path):
    """Test configuration with multiple scan paths."""
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    # Create config with multiple paths
    config = manager._get_defaults()
    config.scan.paths = [
        Path("/home/user/projects"),
        Path("/home/user/work"),
        Path("/home/user/code"),
    ]

    # Save and reload
    manager.save(config)
    loaded = manager.load()

    assert len(loaded.scan.paths) == 3


def test_config_custom_prune_dirs(tmp_path):
    """Test configuration with custom prune directories."""
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    # Create config with custom prune dirs
    config = manager._get_defaults()
    config.scan.prune_dirs = ["node_modules", ".git", "venv", "build"]

    # Save and reload
    manager.save(config)
    loaded = manager.load()

    assert len(loaded.scan.prune_dirs) == 4
    assert "venv" in loaded.scan.prune_dirs
