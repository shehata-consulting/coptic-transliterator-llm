#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the rule-based Greco-Bohairic transliterator."""

import pytest

from coptictranslit import translit, translit_with_warnings

# The contextual phonetic rules the engine was built around.
PHONETIC_CASES = [
    ("ⲉⲩⲁⲅⲅⲉⲗⲓⲟⲛ", "evangelion"),   # upsilon as 'v', double gamma as 'ng'
    ("ⲡⲁⲛⲧⲟⲕⲣⲁⲧⲱⲣ", "pandokrator"),  # tav softening after ni, omega to 'o'
    ("ⲁⲙⲡⲉⲗⲟⲛ", "ambelon"),          # pi softening after mey
    ("ⲭⲉⲣⲉ", "shere"),               # chi as 'sh' before front vowel
    ("ⲭⲣⲓⲥⲧⲟⲥ", "khristos"),         # chi as 'kh' before consonant
    ("ⲛ̀ⲑⲟⲕ", "enthok"),              # jinkim over consonant becomes leading 'e'
]

BASIC_CASES = [
    ("ⲡⲛⲟⲩⲧⲉ", "pnoute"),            # ou digraph
    ("ⲧⲉⲕⲕⲗⲏⲥⲓⲁ", "tekklesia"),      # double kappa, eta as 'e'
    ("ⲙⲁⲣⲓⲁ", "maria"),
    ("ϣⲉⲣⲉ", "shere"),               # shai
    ("ϯ", "ti"),
]


@pytest.mark.parametrize("coptic,expected", PHONETIC_CASES)
def test_contextual_phonetic_rules(coptic, expected):
    assert translit(coptic) == expected


@pytest.mark.parametrize("coptic,expected", BASIC_CASES)
def test_basic_mappings(coptic, expected):
    assert translit(coptic) == expected


def test_empty_and_none_input():
    assert translit("") == ""
    assert translit(None) == ""
    assert translit_with_warnings("") == ("", "")


def test_uppercase_is_lowercased():
    assert translit("Ⲙⲁⲣⲓⲁ") == "maria"


def test_whitespace_and_punctuation_preserved():
    assert translit("ⲡⲛⲟⲩⲧⲉ, ⲙⲁⲣⲓⲁ!") == "pnoute, maria!"
    assert translit("ⲙⲁⲣⲓⲁ\nⲙⲁⲣⲓⲁ") == "maria\nmaria"


def test_output_is_ascii():
    for coptic, _ in PHONETIC_CASES + BASIC_CASES:
        assert translit(coptic).isascii()


def test_no_warnings_for_mapped_text():
    result, unmapped = translit_with_warnings("ⲡⲛⲟⲩⲧⲉ")
    assert result == "pnoute"
    assert unmapped == ""


def test_unmapped_characters_reported():
    # ⳁ (U+2CC1, Old Coptic sampi) has no mapping and should be reported
    result, unmapped = translit_with_warnings("ⲡⲛⲟⲩⲧⲉ ⳁ")
    assert "ⳁ" in unmapped
    assert "ⳁ" in result  # passes through rather than being dropped


def test_unmapped_characters_deduplicated():
    _, unmapped = translit_with_warnings("ⳁ ⳁ ⳁ")
    assert unmapped == "ⳁ"
