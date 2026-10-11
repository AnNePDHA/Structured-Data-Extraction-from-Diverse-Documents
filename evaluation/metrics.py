"""Evaluation metrics for structured extraction benchmark."""

import re
import unicodedata
from collections import Counter


def normalize(s: str) -> str:
    """Lowercase, unicode NFC, collapse whitespace, strip."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokenize(s: str) -> list[str]:
    """Split on whitespace and punctuation, filter empty tokens."""
    tokens = re.findall(r"\w+", normalize(s))
    return tokens


def exact_match(pred: dict, gold: dict, fields: list[str]) -> dict[str, bool]:
    """Per-field exact string match after normalization.

    Iterates over the canonical `fields` list (not gold keys) so records
    with missing ground-truth fields are still scored consistently.
    Missing gold = empty string; model hallucinating a value will score False.
    """
    result = {}
    for key in fields:
        pred_val = normalize(pred.get(key) or "")
        gold_val = normalize(gold.get(key) or "")
        result[key] = pred_val == gold_val
    return result


def token_f1(pred: dict, gold: dict, fields: list[str]) -> dict[str, float]:
    """Per-field token-level F1 score.

    F1 = 2 * precision * recall / (precision + recall)
    Tokens are matched by multiset intersection (handles duplicates).
    Returns 1.0 when both pred and gold are empty for a field.
    Iterates over canonical `fields` list for consistency across records.
    """
    result = {}
    for key in fields:
        pred_tokens = Counter(_tokenize(pred.get(key) or ""))
        gold_tokens = Counter(_tokenize(gold.get(key) or ""))

        if not pred_tokens and not gold_tokens:
            result[key] = 1.0
            continue

        common = sum((pred_tokens & gold_tokens).values())

        if common == 0:
            result[key] = 0.0
            continue

        precision = common / sum(pred_tokens.values())
        recall = common / sum(gold_tokens.values())
        result[key] = 2 * precision * recall / (precision + recall)

    return result


def hallucination_flags(pred: dict, gold: dict, fields: list[str]) -> dict:
    """Per-field hallucination indicator (Reliability dimension).

    A field is a "hallucination opportunity" only when the ground truth is empty
    (there is nothing to extract). The model hallucinates if it emits a value
    anyway. Fields whose ground truth has a value are not applicable.

    Returns dict field -> Optional[bool]:
        None  -> not applicable (ground truth has a value to extract)
        True  -> ground truth empty but model emitted a value (invented)
        False -> ground truth empty and model correctly emitted nothing
    """
    result = {}
    for key in fields:
        gold_val = normalize(gold.get(key) or "")
        pred_val = normalize(pred.get(key) or "")
        result[key] = None if gold_val else (pred_val != "")
    return result


def schema_compliant(pred: dict, fields: list[str]) -> bool:
    """Whether predicted output adheres to the requested flat schema (Reliability).

    Compliant means: a dict that contains every required field as a key and whose
    values are scalars (str or None) — no missing keys, no nested objects/lists.
    A model returning malformed JSON (caught upstream as an error and coerced to
    an all-None dict) still has the keys, so callers should combine this with the
    record's `error` field for a full schema-compliance signal.
    """
    if not isinstance(pred, dict):
        return False
    for key in fields:
        if key not in pred:
            return False
        val = pred[key]
        if val is not None and not isinstance(val, str):
            return False
    return True


def aggregate(results: list[dict], fields: list[str]) -> dict:
    """Compute mean exact_match and token_f1 across all records.

    Args:
        results: list of result dicts, each with 'exact_match' and 'token_f1' sub-dicts.
        fields: canonical list of field names to aggregate over.

    Returns:
        dict with 'exact_match' and 'token_f1' mean per field, plus 'overall' means.
    """
    if not results:
        return {}

    em_sums = {f: 0.0 for f in fields}
    f1_sums = {f: 0.0 for f in fields}
    n = len(results)

    for r in results:
        for f in fields:
            em_sums[f] += float(r["exact_match"].get(f, False))
            f1_sums[f] += r["token_f1"].get(f, 0.0)

    em_per_field = {f: em_sums[f] / n for f in fields}
    f1_per_field = {f: f1_sums[f] / n for f in fields}

    return {
        "n": n,
        "exact_match": em_per_field,
        "token_f1": f1_per_field,
        "overall_exact_match": sum(em_per_field.values()) / len(fields),
        "overall_token_f1": sum(f1_per_field.values()) / len(fields),
    }
