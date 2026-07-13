#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pure text helpers for the Streamlit app.

No Streamlit or network imports here — this module is unit-tested directly
(see tests/), so it must stay importable without an API key or a browser.
"""

import re
import unicodedata

# Free-tier friendly limits for AI enhancement. Gemini's free tier is what
# keeps this tool zero-cost, so long inputs are chunked and capped rather
# than sent as one oversized request.
LLM_CHUNK_CHARS = 4000
LLM_MAX_CHUNKS = 3
LLM_MAX_CHARS = LLM_CHUNK_CHARS * LLM_MAX_CHUNKS

# Coptic Unicode blocks: main block + the Coptic letters inside Greek block
_COPTIC_RANGES = ((0x2C80, 0x2CFF), (0x03E2, 0x03EF))


def contains_coptic(text):
    """True if any character falls in the Coptic Unicode ranges."""
    return any(
        lo <= ord(c) <= hi for c in text for lo, hi in _COPTIC_RANGES
    )


def chunk_text(text, max_chars=LLM_CHUNK_CHARS):
    """Split text into chunks of at most max_chars, on line boundaries when possible."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""
    for line in text.splitlines(keepends=True):
        while len(line) > max_chars:  # a single oversized line: hard split
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:max_chars])
            line = line[max_chars:]
        if len(current) + len(line) > max_chars:
            chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks


def clean_llm_output(raw):
    """Normalize an LLM response to the plain-ASCII transliteration contract.

    The system prompt demands ASCII-only output, but the model can still
    return markdown fences, diacritics, or echo the Coptic input. Returns
    the cleaned text, or None when the response can't be salvaged (caller
    should fall back to the rule-based result).
    """
    if not raw:
        return None
    text = raw.strip()

    if text.startswith("```"):
        text = re.sub(r"^```[^\n]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()
    if not text:
        return None

    if contains_coptic(text):
        return None

    # Decompose accented Latin (ā, ē…) into base letter + combining mark,
    # then drop everything non-ASCII.
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in decomposed if ord(c) < 128).strip()

    # Losing a lot of characters means the output wasn't a transliteration.
    if len(ascii_text) < 0.8 * len(decomposed):
        return None
    return ascii_text or None


def interlinear_lines(source_text, translit_text):
    """Pair source and transliterated words line by line for interlinear display.

    Returns a list of lines. Each line is a list of (source_word, latin_word)
    pairs when the word counts match, a single (source_line, latin_line) pair
    when they don't, or an empty list for a blank spacer line.
    """
    src_lines = source_text.splitlines() or [source_text]
    lat_lines = translit_text.splitlines() or [translit_text]

    lines = []
    for i, src in enumerate(src_lines):
        lat = lat_lines[i] if i < len(lat_lines) else ""
        src_words = src.split()
        lat_words = lat.split()
        if src_words and len(src_words) == len(lat_words):
            lines.append(list(zip(src_words, lat_words)))
        elif src.strip() or lat.strip():
            lines.append([(src.strip(), lat.strip())])
        else:
            lines.append([])
    return lines
