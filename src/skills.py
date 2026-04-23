"""
Discover SKILL.md files and build the agent system prompt from their metadata.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import yaml

from src.constants import PROJECT_ROOT
from src.logger import get_logger

logger = get_logger(__name__)

_SKILLS_ROOT = os.path.join(PROJECT_ROOT, "skills")


def _parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """
    Split YAML front matter from markdown body.

    Args:
        text: Full file contents.

    Returns:
        Tuple of (metadata dict, body string). Empty metadata if no front matter.
    """
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        logger.warning("Invalid YAML front matter: %s", exc)
        meta = {}
    body = parts[2].lstrip("\n")
    return meta, body


def _discover_skill_files() -> List[str]:
    """Return absolute paths to all SKILL.md files under skills/."""
    found: List[str] = []
    if not os.path.isdir(_SKILLS_ROOT):
        logger.warning("Skills directory missing: %s", _SKILLS_ROOT)
        return found
    for dirpath, _dirnames, filenames in os.walk(_SKILLS_ROOT):
        if "SKILL.md" in filenames:
            found.append(os.path.join(dirpath, "SKILL.md"))
    return sorted(found)


def _load_registry() -> Dict[str, dict[str, Any]]:
    """
    Build the skill registry from disk.

    Returns:
        Map skill_name -> {description, path, body}
    """
    registry: Dict[str, dict[str, Any]] = {}
    for path in _discover_skill_files():
        with open(path, encoding="utf-8") as f:
            text = f.read()
        meta, body = _parse_front_matter(text)
        name = meta.get("name")
        description = meta.get("description", "")
        if not name:
            logger.warning("Skipping skill without name: %s", path)
            continue
        registry[str(name)] = {
            "name": str(name),
            "description": str(description).strip(),
            "path": path,
            "body": body.strip(),
        }
    return registry


# Populated at import time for reuse across workflows.
SKILL_REGISTRY: Dict[str, dict[str, Any]] = _load_registry()
