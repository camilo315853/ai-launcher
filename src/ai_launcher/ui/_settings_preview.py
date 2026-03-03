#!/usr/bin/env python3
"""Helper script for settings preview generation.

This script is called by fzf's --preview command to generate the preview
pane content for settings items. It runs in a subprocess and outputs to stdout.

Usage:
    python _settings_preview.py "SETTING_LINE"

Author: Solent Labs™
Created: 2026-02-10
"""

import sys


def generate_preview(line: str) -> str:
    """Generate preview content for a settings line.

    Args:
        line: The full line from fzf including metadata

    Returns:
        Formatted preview text
    """
    # Parse the line format: "__TYPE__:setting_id:DESCRIPTION||text\t\tdisplay"
    parts = line.split("\t\t", 1)
    if len(parts) < 2:
        return "No preview available"

    metadata = parts[0]

    # Handle header items (no preview)
    if metadata.startswith("__HEADER__"):
        return ""

    # Extract description from metadata
    if "::" in metadata:
        # Format: __TYPE__:id:DESC||description text
        try:
            meta_parts = metadata.split(":", 2)
            if len(meta_parts) >= 3:
                desc_part = meta_parts[2]
                if "||" in desc_part:
                    _, description = desc_part.split("||", 1)
                    return format_description(description)
        except Exception:
            pass

    return "No description available"


def format_description(description: str) -> str:
    """Format description with nice borders.

    Args:
        description: Raw description text (with \\n escaped)

    Returns:
        Formatted description with borders
    """
    # Convert escaped newlines back to actual newlines
    description = description.replace("\\n", "\n")
    lines = description.split("\n")

    # Build output with borders
    output = []
    output.append("╭─────────────────────────────────────────╮")
    output.append("│           Setting Details               │")
    output.append("╰─────────────────────────────────────────╯")
    output.append("")

    for line in lines:
        output.append(line)

    return "\n".join(output)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("No preview available")
        return

    line = sys.argv[1]
    preview = generate_preview(line)
    print(preview)


if __name__ == "__main__":
    main()
