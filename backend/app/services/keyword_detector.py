from __future__ import annotations

import re


def normalize_keyword(keyword: str) -> str:
    return keyword.strip().lower()


def detect_keywords(text: str, keywords: list[str]) -> list[str]:
    haystack = text.lower()
    matches: list[str] = []
    for keyword in keywords:
        normalized = normalize_keyword(keyword)
        if not normalized:
            continue
        pattern = rf"(?<!\w){re.escape(normalized)}(?!\w)"
        if re.search(pattern, haystack, flags=re.IGNORECASE):
            matches.append(normalized)
    return sorted(set(matches))
