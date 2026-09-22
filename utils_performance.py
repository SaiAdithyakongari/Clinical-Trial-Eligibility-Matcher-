"""
Performance & Error Handling Utilities
Provides retry logic, caching, and graceful fallbacks for LLM operations.

Performance improvements (now wired up):
- retry_with_backoff is applied to LLM generate_text calls via LLMClient internals.
- cache_with_ttl is applied here and exported for use by embeddings and matcher.
- split_into_chunks is used by pdf_processing.py for overlapping chunking.
"""

import time
import functools
from typing import Callable, Any, Optional, Dict, List, Tuple
import json
import re


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> Callable:
    """
    Decorator for retrying failed functions with exponential backoff.
    Applied directly to functions that make external API calls.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception: Optional[Exception] = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        print(f"[retry_with_backoff] Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                              f"Retrying in {delay:.1f}s…")
                        time.sleep(delay)
                        delay *= backoff_factor

            raise last_exception or Exception(f"Failed after {max_attempts} attempts")

        return wrapper
    return decorator


def safe_json_extraction(text: str, default: Optional[Dict] = None) -> Dict:
    """
    Safely extracts JSON from text, with fallback to empty dict.
    Handles common JSON formatting issues.
    """
    if not text:
        return default or {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        pass

    return default or {}


def cache_with_ttl(ttl_seconds: int = 3600) -> Callable:
    """
    In-process TTL-based caching decorator.
    Now actively used by EmbeddingsEngine._local_dense_embed and matcher helpers.

    Usage:
        @cache_with_ttl(ttl_seconds=1800)
        def expensive_call(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        _cache: Dict[str, Tuple[Any, float]] = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_time = time.time()
            # Build a cache key from positional + keyword args
            try:
                cache_key = str(args) + str(sorted(kwargs.items()))
            except Exception:
                cache_key = str(id(args))

            if cache_key in _cache:
                value, timestamp = _cache[cache_key]
                if current_time - timestamp < ttl_seconds:
                    return value
                del _cache[cache_key]

            result = func(*args, **kwargs)
            _cache[cache_key] = (result, current_time)
            return result

        # Expose cache invalidation
        def clear_cache() -> None:
            _cache.clear()

        wrapper.clear_cache = clear_cache  # type: ignore[attr-defined]
        return wrapper
    return decorator


def split_into_chunks(text: str, max_chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Splits text into overlapping chunks for better embeddings coverage.
    Used by pdf_processing.py chunker.
    """
    if not text:
        return []

    chunks: List[str] = []
    sentences = re.split(r'(?<=[.!?])\s+', text)

    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk = (current_chunk + " " + sentence).lstrip()
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    if overlap > 0 and len(chunks) > 1:
        overlapped: List[str] = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                prev_tail = chunks[i - 1][-overlap:] if len(chunks[i - 1]) >= overlap else chunks[i - 1]
                overlapped.append((prev_tail + " " + chunk).strip())
            else:
                overlapped.append(chunk)
        return overlapped

    return chunks


def get_structured_default_patient() -> Dict:
    """Returns a default structured patient object for initialisation."""
    return {
        "demographics": {"age": None, "gender": "Unknown", "ecog_ps": None, "patient_id": None},
        "condition": {"primary_diagnosis": "Unknown", "stage": "Unknown", "histology": "Unknown", "progression_status": "Unknown"},
        "biomarkers": [],
        "prior_treatments": [],
        "organ_function_and_labs": {"anc": "Unknown", "platelets": "Unknown", "creatinine": "Unknown", "alt_ast": "Unknown", "lvef": "Unknown"},
        "comorbidities": [],
        "cns_metastases": "Unknown",
        "summary_paragraph": ""
    }


def merge_patient_profiles(profile1: Dict, profile2: Dict) -> Dict:
    """
    Merges two patient profile dictionaries, preferring non-null values from profile2.
    """
    merged = json.loads(json.dumps(profile1))  # deep copy

    for key, value in profile2.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_patient_profiles(merged[key], value)
        elif value is not None and value != "Unknown":
            merged[key] = value

    return merged
