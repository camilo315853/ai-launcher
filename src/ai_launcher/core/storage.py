"""SQLite storage for claude-launcher."""

import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ai_launcher.core.models import Project


class Storage:
    """Manages SQLite database for manual paths and history."""

    def __init__(self, db_path: Path):
        """Initialize storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self) -> None:
        """Ensure database exists and has correct schema."""
        try:
            # Try to connect and validate
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            if "manual_projects" not in tables or "last_opened" not in tables:
                # Create schema
                self._create_schema(conn)
            else:
                # Validate we can query
                cursor.execute("SELECT 1 FROM manual_projects LIMIT 1")

            conn.close()

        except sqlite3.DatabaseError as e:
            print(f"Database corruption detected: {e}")
            self._recover_database()

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """Create database schema.

        Args:
            conn: SQLite connection
        """
        cursor = conn.cursor()

        # Manual projects table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_projects (
                path TEXT PRIMARY KEY,
                added_at TEXT NOT NULL
            )
        """
        )

        # Last opened project table (single row)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS last_opened (
                path TEXT PRIMARY KEY
            )
        """
        )

        # Access history (optional, for future analytics)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS access_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                accessed_at TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_access_history_path
            ON access_history(path)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_access_history_time
            ON access_history(accessed_at)
        """
        )

        conn.commit()

    def _recover_database(self) -> None:
        """Recover from corrupted database by backing up and recreating."""
        if self.db_path.exists():
            # Backup corrupted database
            backup_path = self.db_path.with_suffix(f".db.backup.{int(time.time())}")
            shutil.move(str(self.db_path), str(backup_path))
            print(f"Corrupted database backed up to: {backup_path}")

        # Create fresh database
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        self._create_schema(conn)
        conn.close()
        print(f"Fresh database created at: {self.db_path}")

    def add_manual_path(self, path: Path) -> None:
        """Add a manual project path.

        Args:
            path: Path to add
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR REPLACE INTO manual_projects (path, added_at) VALUES (?, ?)",
            (str(path), datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()

    def remove_manual_path(self, path: str) -> None:
        """Remove a manual project path.

        Args:
            path: Path string to remove
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM manual_projects WHERE path = ?", (path,))

        conn.commit()
        conn.close()

    def get_manual_paths(self) -> List[str]:
        """Get all manual project paths.

        Returns:
            List of path strings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT path FROM manual_projects ORDER BY path")
        paths = [row[0] for row in cursor.fetchall()]

        conn.close()
        return paths

    def get_manual_projects(self) -> List[Project]:
        """Get manual projects, auto-removing non-existent paths.

        Returns:
            List of valid Project instances
        """
        paths = self.get_manual_paths()
        valid_projects = []
        invalid_paths = []

        for path_str in paths:
            # Don't resolve symlinks - keep the original path
            # This ensures projects show up in the tree under their symlink location
            path = Path(path_str).expanduser()

            if path.exists() and path.is_dir():
                project = Project.from_path(path, is_manual=True)
                valid_projects.append(project)
            else:
                invalid_paths.append(path_str)
                print(f"Removing non-existent manual path: {path_str}")

        # Clean up invalid paths
        for path_str in invalid_paths:
            self.remove_manual_path(path_str)

        return valid_projects

    def set_last_opened(self, path: Path) -> None:
        """Set the last opened project.

        Args:
            path: Path to the project
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Clear existing and set new (single row table)
        cursor.execute("DELETE FROM last_opened")
        cursor.execute("INSERT INTO last_opened (path) VALUES (?)", (str(path),))

        # Also record in access history
        cursor.execute(
            "INSERT INTO access_history (path, accessed_at) VALUES (?, ?)",
            (str(path), datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()

    def get_last_opened(self) -> Optional[str]:
        """Get the last opened project path.

        Returns:
            Path string or None if no history
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT path FROM last_opened LIMIT 1")
        row = cursor.fetchone()

        conn.close()
        result: Optional[str] = row[0] if row else None
        return result

    def get_default_selection_index(self, projects: List[Project]) -> int:
        """Get the index of the last opened project in the list.

        Args:
            projects: Sorted list of projects

        Returns:
            Index of last opened project, or 0 if not found
        """
        last_opened = self.get_last_opened()
        if not last_opened:
            return 0

        for i, project in enumerate(projects):
            if str(project.path) == last_opened:
                return i

        return 0
