#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the pure app helpers in text_utils.py."""

from text_utils import (
    chunk_text,
    clean_llm_output,
    contains_coptic,
    interlinear_lines,
)


class TestContainsCoptic:
    def test_detects_coptic(self):
        assert contains_coptic("ⲡⲛⲟⲩⲧⲉ")
        assert contains_coptic("mixed ⲁ text")

    def test_plain_latin_is_clean(self):
        assert not contains_coptic("pnoute agape")
        assert not contains_coptic("")


class TestChunkText:
    def test_short_text_single_chunk(self):
        assert chunk_text("hello", max_chars=100) == ["hello"]

    def test_splits_on_line_boundaries(self):
        text = "aaa\nbbb\nccc\n"
        chunks = chunk_text(text, max_chars=8)
        assert all(len(c) <= 8 for c in chunks)
        assert "".join(chunks) == text

    def test_oversized_single_line_hard_splits(self):
        text = "x" * 25
        chunks = chunk_text(text, max_chars=10)
        assert all(len(c) <= 10 for c in chunks)
        assert "".join(chunks) == text

    def test_content_always_preserved(self):
        text = "ⲡⲛⲟⲩⲧⲉ ⲙⲁⲣⲓⲁ\n" * 50
        assert "".join(chunk_text(text, max_chars=64)) == text


class TestCleanLlmOutput:
    def test_plain_output_passes_through(self):
        assert clean_llm_output("pnoute maria") == "pnoute maria"

    def test_strips_whitespace(self):
        assert clean_llm_output("  pnoute \n") == "pnoute"

    def test_strips_markdown_fences(self):
        assert clean_llm_output("```\npnoute\n```") == "pnoute"
        assert clean_llm_output("```text\npnoute\n```") == "pnoute"

    def test_removes_diacritics(self):
        assert clean_llm_output("pnoutē mārya") == "pnoute marya"

    def test_rejects_coptic_echo(self):
        assert clean_llm_output("ⲡⲛⲟⲩⲧⲉ") is None

    def test_rejects_empty(self):
        assert clean_llm_output("") is None
        assert clean_llm_output(None) is None
        assert clean_llm_output("```\n```") is None

    def test_rejects_mostly_non_ascii(self):
        assert clean_llm_output("日本語のテキストです") is None


class TestInterlinearLines:
    def test_word_pairs_when_counts_match(self):
        lines = interlinear_lines("ⲁ ⲃ", "a b")
        assert lines == [[("ⲁ", "a"), ("ⲃ", "b")]]

    def test_falls_back_to_line_pair_on_mismatch(self):
        lines = interlinear_lines("ⲁ ⲃ ⲅ", "a b")
        assert lines == [[("ⲁ ⲃ ⲅ", "a b")]]

    def test_multiline(self):
        lines = interlinear_lines("ⲁ ⲃ\nⲅ", "a b\ng")
        assert lines == [[("ⲁ", "a"), ("ⲃ", "b")], [("ⲅ", "g")]]

    def test_blank_lines_become_spacers(self):
        lines = interlinear_lines("ⲁ\n\nⲃ", "a\n\nb")
        assert lines == [[("ⲁ", "a")], [], [("ⲃ", "b")]]

    def test_missing_translit_line(self):
        lines = interlinear_lines("ⲁ\nⲃ", "a")
        assert lines[0] == [("ⲁ", "a")]
        assert lines[1] == [("ⲃ", "")]
