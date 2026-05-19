"""spaCy-assisted filters for bare `como` experiment candidates."""

from __future__ import annotations

import re
from typing import Any

ROLE_HEAD_LEMMAS = frozenset(
    {
        "administrador",
        "advogado",
        "aluno",
        "autor",
        "candidato",
        "chefe",
        "componente",
        "criminoso",
        "dirigente",
        "empresário",
        "estratégia",
        "estudante",
        "exemplo",
        "ferramenta",
        "fornecedor",
        "função",
        "gerente",
        "guerrilheiro",
        "jogador",
        "mandante",
        "operador",
        "parceiro",
        "polícia",
        "produtor",
        "professor",
        "representante",
        "refém",
        "suspeito",
        "tendência",
    }
)

VISUAL_HEAD_LEMMAS = frozenset(
    {
        "água",
        "breu",
        "chumbo",
        "cristal",
        "dia",
        "fogo",
        "luz",
        "mel",
        "mercúrio",
        "montanha",
        "ouro",
        "pedra",
        "pluma",
        "raio",
        "sol",
        "vento",
        "vidro",
    }
)

ROLE_CONTEXT_RE = re.compile(
    r"\b(?:atu(?:a|ou|ar|ando)|trabalh(?:a|ou|ar|ando)|serv(?:e|iu|ir|indo)|"
    r"usad\w*|utilizad\w*|considerad\w*|definid\w*|classificad\w*|"
    r"pres[ao]s?|condenad\w*|contratad\w*)\b",
    re.IGNORECASE,
)

ROLE_SUFFIX_RE = re.compile(r"(?:dor|dora|ista|nte|ário|ária|eiro|eira|or|ora|ante|ente|ólogo|óloga)$", re.IGNORECASE)


def classify_bare_como_candidate(candidate: dict[str, Any], doc: Any | None = None) -> dict[str, str | bool]:
    """Return transparent NLP filter labels for one bare-como candidate."""

    head = str(candidate.get("vehicle_head_clean") or "").strip().lower()
    raw = str(candidate.get("vehicle_text_raw") or "")
    full_text = str(candidate.get("candidate_full_text") or "")
    lemma = _vehicle_head_lemma(head, doc)
    pos = _vehicle_head_pos(head, doc)

    if not head:
        return _result("reject", "missing_vehicle_head", lemma, pos, True)
    if lemma in VISUAL_HEAD_LEMMAS or head in VISUAL_HEAD_LEMMAS:
        return _result("keep", "visual_head_whitelist", lemma, pos, False)
    if lemma in ROLE_HEAD_LEMMAS or head in ROLE_HEAD_LEMMAS:
        return _result("reject", "role_head_lexicon", lemma, pos, True)
    if ROLE_CONTEXT_RE.search(full_text):
        return _result("review", "role_context", lemma, pos, True)
    if pos in {"VERB", "AUX", "SCONJ", "ADP", "ADV", "PRON", "DET"}:
        return _result("reject", f"bad_spacy_pos_{pos.lower()}", lemma, pos, True)
    if ROLE_SUFFIX_RE.search(lemma) and pos in {"NOUN", "PROPN"}:
        return _result("review", "role_like_suffix", lemma, pos, True)
    if len(raw.split()) > 3:
        return _result("review", "long_vehicle_phrase", lemma, pos, True)
    return _result("keep", "spacy_short_nominal_vehicle", lemma, pos, False)


def _vehicle_head_lemma(head: str, doc: Any | None) -> str:
    token = _find_token(head, doc)
    if token is None:
        return head
    return str(getattr(token, "lemma_", "") or head).lower()


def _vehicle_head_pos(head: str, doc: Any | None) -> str:
    token = _find_token(head, doc)
    if token is None:
        return ""
    return str(getattr(token, "pos_", "") or "")


def _find_token(head: str, doc: Any | None) -> Any | None:
    if doc is None:
        return None
    for token in doc:
        if str(getattr(token, "text", "")).lower() == head:
            return token
    return None


def _result(label: str, reason: str, lemma: str, pos: str, needs_review: bool) -> dict[str, str | bool]:
    return {
        "nlp_quality_label": label,
        "nlp_quality_reason": reason,
        "spacy_vehicle_head_lemma": lemma,
        "spacy_vehicle_head_pos": pos,
        "nlp_needs_review": needs_review,
    }
