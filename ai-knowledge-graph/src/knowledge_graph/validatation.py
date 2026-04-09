"""Validation utilities for checking text/triple alignment."""
from __future__ import annotations

import re
from typing import Iterable

# Small bilingual stopword set for predicate keyword matching.
_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "with", "by", "is", "are",
    "was", "were", "be", "from", "at", "as", "that", "this", "it", "its", "their", "his", "her",
    "的", "了", "和", "与", "是", "在", "由", "及", "或", "被", "对", "将", "把",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _split_sentences(text: str) -> list[str]:
    # Supports both English and Chinese punctuation.
    chunks = re.split(r"(?<=[.!?。！？；;])\s+|\n+", text)
    return [c.strip() for c in chunks if c and c.strip()]


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[\w\u4e00-\u9fff]+", _normalize_text(text)) if t]


def _predicate_keywords(predicate: str) -> set[str]:
    keywords = set(_tokenize(predicate))
    return {kw for kw in keywords if kw not in _STOPWORDS and len(kw) > 1}


def _token_overlap_ratio(tokens: Iterable[str], text: str) -> float:
    token_set = {t for t in tokens if t}
    if not token_set:
        return 0.0
    hit = sum(1 for t in token_set if t in text)
    return hit / len(token_set)


def _sentence_support_score(sentence: str, subject: str, predicate: str, object_: str) -> float:
    sentence_norm = _normalize_text(sentence)
    subject_norm = _normalize_text(subject)
    object_norm = _normalize_text(object_)

    subject_score = 1.0 if subject_norm and subject_norm in sentence_norm else _token_overlap_ratio(_tokenize(subject_norm), sentence_norm)
    object_score = 1.0 if object_norm and object_norm in sentence_norm else _token_overlap_ratio(_tokenize(object_norm), sentence_norm)

    predicate_terms = _predicate_keywords(predicate)
    predicate_score = _token_overlap_ratio(predicate_terms, sentence_norm)

    # Encourage evidence that includes both entities, while still allowing predicate paraphrases.
    return 0.4 * subject_score + 0.4 * object_score + 0.2 * predicate_score


def flatten_blocks_to_text(blocks) -> str:
    """Flatten parsed .docx blocks into a plain-text string for validation."""
    lines = []
    for _, block_type, content in blocks:
        if not content:
            continue
        if block_type == "table":
            lines.append(str(content))
        else:
            lines.append(str(content))
    return "\n".join(lines)


def validate_triples_against_text(
    triples: list[dict],
    source_text: str,
    threshold: float = 0.6,
    min_sentence_length: int = 20,
) -> dict:
    """Score every triple against source text and return validation report."""
    sentences = [s for s in _split_sentences(source_text) if len(s) >= min_sentence_length]
    if not sentences:
        sentences = [source_text]

    report_items = []
    for index, triple in enumerate(triples):
        subject = str(triple.get("subject", ""))
        predicate = str(triple.get("predicate", ""))
        object_ = str(triple.get("object", ""))

        best_sentence = ""
        best_score = 0.0

        for sentence in sentences:
            score = _sentence_support_score(sentence, subject, predicate, object_)
            if score > best_score:
                best_score = score
                best_sentence = sentence

        triple["validation_score"] = round(best_score, 4)
        triple["validation_supported"] = best_score >= threshold
        if best_sentence:
            triple["validation_evidence"] = best_sentence[:220]

        report_items.append(
            {
                "index": index,
                "subject": subject,
                "predicate": predicate,
                "object": object_,
                "score": round(best_score, 4),
                "supported": best_score >= threshold,
                "evidence": best_sentence,
            }
        )

    supported = sum(1 for item in report_items if item["supported"])
    total = len(report_items)
    avg_score = sum(item["score"] for item in report_items) / total if total else 0.0

    return {
        "threshold": threshold,
        "total_triples": total,
        "supported_triples": supported,
        "unsupported_triples": total - supported,
        "support_ratio": round((supported / total), 4) if total else 0.0,
        "avg_score": round(avg_score, 4),
        "items": report_items,
    }