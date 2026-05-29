#!/usr/bin/env python3
# Copyright (C) 2026 Robert Derveloy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Sync the AI-usage notice from AI_USAGE.md into every .py file's header.

Reads the canonical per-file inline notice from the fenced code block
under "Per-file inline notice" in AI_USAGE.md, then for each tracked
Python file ensures that notice appears immediately after the existing
AGPL header. Idempotent: files that already match are left untouched.

Run from the repository root::

    python tools/sync_headers.py

Exits non-zero if it had to modify any files (useful as a CI gate).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# AGPL header's last line is stable across every file in the project, so
# we anchor the AI notice's insertion point on it. Anything else is
# fragile.
_AGPL_LAST_LINE = (
    "# along with this program.  "
    "If not, see <https://www.gnu.org/licenses/>."
)

_NOTICE_START_PATTERN = re.compile(
    r"^# AI and code-generation tools:.*$", re.MULTILINE
)


def read_canonical_notice(repo_root: Path) -> str:
    """Return the inline notice text from AI_USAGE.md's canonical block."""
    ai_usage = (repo_root / "AI_USAGE.md").read_text(encoding="utf-8")
    match = re.search(
        r"```\n(# AI and code-generation tools:.*?\n)```",
        ai_usage,
        re.DOTALL,
    )
    if not match:
        raise SystemExit(
            "AI_USAGE.md does not contain a canonical per-file notice "
            "block; expected a fenced code block starting with "
            "'# AI and code-generation tools:'"
        )
    return match.group(1).rstrip("\n")


def updated_header(file_text: str, notice: str) -> str:
    """Return *file_text* with the AI notice present after the AGPL header.

    Replaces an existing notice block if found; otherwise inserts after
    the AGPL header's last line. Returns the unchanged text when the
    file already matches.
    """
    if _AGPL_LAST_LINE not in file_text:
        # Files without the AGPL header are out of scope; leave them.
        return file_text

    notice_block = notice + "\n"
    # If an AI notice already exists, replace the entire block from the
    # first matching line through the trailing blank/comment-end.
    existing_match = _NOTICE_START_PATTERN.search(file_text)
    if existing_match:
        # The notice block runs from the start of the match line through
        # whichever line ends the contiguous run of '#' lines.
        block_start = existing_match.start()
        block_end = block_start
        for line in file_text[block_start:].splitlines(keepends=True):
            if line.startswith("#"):
                block_end += len(line)
            else:
                break
        candidate = file_text[:block_start] + notice_block + file_text[
            block_end:
        ]
        return candidate

    # No notice yet: insert after the AGPL header's last line, separated
    # by a single "#\n" continuation line for visual continuity.
    insertion_marker = _AGPL_LAST_LINE + "\n"
    return file_text.replace(
        insertion_marker,
        insertion_marker + "#\n" + notice_block,
        1,
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    notice = read_canonical_notice(repo_root)

    targets = list((repo_root / "src").rglob("*.py")) + list(
        (repo_root / "tests").rglob("*.py")
    )
    changed: list[Path] = []
    for path in sorted(targets):
        original = path.read_text(encoding="utf-8")
        updated = updated_header(original, notice)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)

    if changed:
        for path in changed:
            print(f"updated {path.relative_to(repo_root)}")
        return 1
    print("All files already in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
