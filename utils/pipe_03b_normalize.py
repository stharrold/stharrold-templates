# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Pipeline stage 03b: Normalize entity types and filter noise.

Maps LLM's non-canonical types to 5 schema types (Person, Organization,
Project, Topic, Date), removes blocklisted noise, deduplicates.
"""

import logging
import re

logger = logging.getLogger(__name__)

CANONICAL_TYPES = {"Person", "Organization", "Project", "Topic", "Date"}

TYPE_MAP = {
    "company": "Organization",
    "location": "Organization",
    "department": "Organization",
    "team": "Organization",
    "group": "Organization",
    "institution": "Organization",
    "facility": "Organization",
    "hospital": "Organization",
    "vendor": "Organization",
    "system": "Project",
    "application": "Project",
    "platform": "Project",
    "database": "Project",
    "product": "Project",
    "service": "Project",
    "time": "Date",
    "datetime": "Date",
    "deadline": "Date",
    "schedule": "Date",
}

ENTITY_BLOCKLIST = [
    re.compile(r"^(email|message|attachment|subject|body|none|n/a|null|undefined|error|true|false)$", re.IGNORECASE),
    re.compile(r"^(the|this|that|here|there|please|thank|thanks|hi|hello|dear|fyi|re:|fw:)$", re.IGNORECASE),
    re.compile(r"^\[URL\]$"),
    re.compile(r"^\[EMAIL\]$"),
]

MIN_NAME_LENGTH = 2


def normalize_entity_type(entity_type: str) -> str:
    if not entity_type:
        return "Topic"
    for canonical in CANONICAL_TYPES:
        if entity_type.lower() == canonical.lower():
            return canonical
    mapped = TYPE_MAP.get(entity_type.lower())
    if mapped:
        return mapped
    return "Topic"


def _is_blocklisted(name: str) -> bool:
    for pattern in ENTITY_BLOCKLIST:
        if pattern.match(name.strip()):
            return True
    return False


def normalize_entities(entities: list[dict]) -> list[dict]:
    seen = {}
    for ent in entities:
        name = (ent.get("name") or "").strip()
        if not name or len(name) < MIN_NAME_LENGTH:
            continue
        if _is_blocklisted(name):
            continue
        etype = normalize_entity_type(ent.get("type", "Topic"))
        confidence = ent.get("confidence", 0.5)
        key = (name.lower(), etype)
        existing = seen.get(key)
        if existing is None or confidence > existing.get("confidence", 0):
            seen[key] = {"name": name, "type": etype, "confidence": confidence}
    return list(seen.values())
