from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set


SEVERITY_ORDER = {
    "contraindicacao": 4,
    "grave": 3,
    "moderada": 2,
    "leve": 1,
}


@dataclass
class Finding:
    category: str
    supplement: str
    text: str
    severity: str
    matched_externals: List[str]


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", value).strip()


def classify_severity(text: str, category: str) -> str:
    if category == "contraindicacoes":
        return "contraindicacao"
    normalized = _normalize(text)
    if any(term in normalized for term in ["contraindicado", "severo", "grave", "arritmia", "hemorrag", "sangramento", "hemorragico"]):
        return "grave"
    if any(term in normalized for term in ["precauc", "risco", "toxic", "suspender"]):
        return "moderada"
    return "leve"


def _parse_free_text(text: str) -> List[str]:
    if not text:
        return []
    text = text.replace(";", ",")
    return [part.strip() for part in text.split(",") if part.strip()]


def _matches_any(text: str, terms: Iterable[str]) -> List[str]:
    hay = _normalize(text)
    matched = []
    for term in terms:
        needle = _normalize(term)
        if needle and needle in hay:
            matched.append(term)
    return matched


def analyze(
    dataset: Dict[str, Any],
    selected_supplements: List[str],
    selected_externals: List[str],
    free_text_externals: str,
) -> Dict[str, Any]:
    items = dataset.get("items", [])
    index = {item.get("name"): item for item in items}
    chosen = [index[name] for name in selected_supplements if name in index]

    extra_terms = list(selected_externals)
    extra_terms.extend(_parse_free_text(free_text_externals))
    external_terms: List[str] = []
    seen: Set[str] = set()
    for term in extra_terms:
        key = _normalize(term)
        if not key or key in seen:
            continue
        seen.add(key)
        external_terms.append(term)

    findings: List[Finding] = []

    for item in chosen:
        contraindications = item.get("contraindications_text", "")
        if contraindications:
            findings.append(
                Finding(
                    category="contraindicacoes",
                    supplement=item.get("name", ""),
                    text=contraindications,
                    severity=classify_severity(contraindications, "contraindicacoes"),
                    matched_externals=[],
                )
            )

        interactions = item.get("interactions_text", "")
        if interactions:
            matches = _matches_any(interactions, external_terms)
            if external_terms and not matches:
                pass
            else:
                findings.append(
                    Finding(
                        category="interacoes",
                        supplement=item.get("name", ""),
                        text=interactions,
                        severity=classify_severity(interactions, "interacoes"),
                        matched_externals=matches,
                    )
                )

        adverse = item.get("adverse_text", "")
        if adverse:
            findings.append(
                Finding(
                    category="efeitos_adversos",
                    supplement=item.get("name", ""),
                    text=adverse,
                    severity=classify_severity(adverse, "efeitos_adversos"),
                    matched_externals=[],
                )
            )

    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 0), reverse=True)

    known_external = {_normalize(term) for term in dataset.get("external_catalog", [])}
    unknown_external = [
        term for term in external_terms if _normalize(term) not in known_external and term not in selected_externals
    ]

    return {
        "selected_supplements": selected_supplements,
        "selected_externals": external_terms,
        "unknown_external_terms": unknown_external,
        "findings": [
            {
                "category": finding.category,
                "supplement": finding.supplement,
                "text": finding.text,
                "severity": finding.severity,
                "matched_externals": finding.matched_externals,
            }
            for finding in findings
        ],
    }
