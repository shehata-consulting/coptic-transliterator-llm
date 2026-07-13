#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Coptic to Latin transliterator
Aligns with ASCII-only standard transliteration conventions and 
incorporates Greco-Bohairic contextual phonetic rules.
"""

import re
import unicodedata


class CopticTransliterator:
    def __init__(self):
        # Streamlined to lowercase only.
        # Note: ⲭ (Chi) is removed from the static map as it is fully handled by regex rules.
        self.char_map = {
            "ⲁ": "a",
            "ⲃ": "b",
            "ⲅ": "g",
            "ⲇ": "d",
            "ⲉ": "e",
            "ⲍ": "z",
            # Standardized to 'e' to match LLM examples (like tekklesia)
            "ⲏ": "e",
            "ⲑ": "th",
            "ⲓ": "i",
            "ⲕ": "k",
            "ⲗ": "l",
            "ⲙ": "m",
            "ⲛ": "n",
            "ⲝ": "x",
            "ⲟ": "o",
            "ⲡ": "p",
            "ⲣ": "r",
            "ⲥ": "s",
            "ⲧ": "t",
            "ⲩ": "u",
            "ⲫ": "ph",
            "ⲯ": "ps",
            "ⲱ": "o",   # ASCII representation of Omega
            "ϣ": "sh",
            "ϥ": "f",
            "ϧ": "kh",
            "ϩ": "h",
            "ϫ": "j",
            "ϭ": "ch",  # Shima is standardly mapped to ch (as in church)
            "ϯ": "ti",
            "ⲋ": "6",   # Soou is the number 6, not 'f'
        }

    def translit(self, text):
        """
        Transliterate Coptic text to Latin script
        """
        result, _ = self.translit_with_warnings(text)
        return result

    def translit_with_warnings(self, text):
        """
        Transliterate Coptic text to Latin script.

        Returns (result, unmapped) where unmapped is a string of distinct
        Coptic characters that had no mapping and passed through unchanged —
        callers (e.g. the UI) decide how to surface them.
        """
        if not text:
            return "", ""

        # 1. Normalize input to decompose combining characters and lowercase immediately
        text = unicodedata.normalize("NFKD", text).lower()

        # 2. Handle the Jinkim (grave accent \u0300) before stripping other diacritics.
        # When over a consonant, it adds an 'e' sound before it (e.g., ⲛ̀ -> en).
        text = re.sub(r"([ⲃⲅⲇⲍⲑⲕⲗⲙⲛⲝⲡⲣⲥⲧⲫⲭⲯϣϥϧϩϫϭϯ])\u0300", r"e\1", text)

        # 3. Remove any remaining combining diacritics (e.g., supralinear strokes over vowels)
        text = "".join(c for c in text if not unicodedata.combining(c))

        # 4. Apply advanced contextual phonetic rules
        result = self._apply_contextual_rules(text)

        # 5. Apply basic character mappings for everything else
        for coptic_char, latin_char in self.char_map.items():
            result = result.replace(coptic_char, latin_char)

        # 6. Collect unmapped Coptic characters (Unicode blocks 2C80-2CFF and 03E2-03EF)
        unmapped = "".join(dict.fromkeys(c for c in result if (
            0x2C80 <= ord(c) <= 0x2CFF) or (0x03E2 <= ord(c) <= 0x03EF)))

        return result, unmapped

    def _apply_contextual_rules(self, text):
        """
        Apply context-sensitive transliteration rules based on Greco-Bohairic pronunciation
        """
        # Upsilon (ⲩ) contextual rules - must happen before Alpha/Ei mappings
        # ⲩ -> v after ⲁ (a) or ⲉ (e)
        text = re.sub(r"([ⲁⲉ])ⲩ", r"\1v", text)

        # Standardize Ou early
        text = re.sub(r"ⲟⲩ", "ou", text)             # ⲟⲩ -> ou

        # Veeta (ⲃ) contextual rules
        text = re.sub(r"ⲃ(?=[ⲁⲉⲓⲏⲟⲩⲱ])", "v", text)  # ⲃ -> v before vowels
        text = re.sub(r"ⲃ", "b", text)               # ⲃ -> b elsewhere

        # Gamma (ⲅ) contextual rules
        # ⲅ -> n before another ⲅ (ng)
        text = re.sub(r"ⲅ(?=ⲅ)", "n", text)
        # ⲅ -> g before front vowels
        text = re.sub(r"ⲅ(?=[ⲓⲉⲏⲩ])", "g", text)
        text = re.sub(r"ⲅ", "gh", text)              # ⲅ -> gh elsewhere

        # Chi (ⲭ) contextual rules
        # ⲭ -> sh before front vowels
        text = re.sub(r"ⲭ(?=[ⲉⲏⲓⲩ])", "sh", text)
        text = re.sub(r"ⲭ", "kh", text)              # ⲭ -> kh elsewhere

        # Consonant softening rules (Greek influence)
        # ⲧ -> d after ⲛ (e.g., Pantokrator -> Pandokrator)
        text = re.sub(r"(?<=ⲛ)ⲧ", "d", text)
        # ⲡ -> b after ⲙ (e.g., Ampelon -> Ambelon)
        text = re.sub(r"(?<=ⲙ)ⲡ", "b", text)

        # Multi-character sequences (double consonants)
        text = re.sub(r"ⲕⲕ", "kk", text)
        text = re.sub(r"ⲙⲙ", "mm", text)
        text = re.sub(r"ⲛⲛ", "nn", text)

        return text


# Create instance for easy use
transliterator = CopticTransliterator()


def translit(text):
    return transliterator.translit(text)


def translit_with_warnings(text):
    return transliterator.translit_with_warnings(text)


# Example usage/Testing
if __name__ == "__main__":
    tests = {
        "ⲉⲩⲁⲅⲅⲉⲗⲓⲟⲛ": "evangelion",       # Upsilon as 'v', double gamma as 'ng'
        "ⲡⲁⲛⲧⲟⲕⲣⲁⲧⲱⲣ": "pandokrator",      # Tav softening after Ni, Omega to 'o'
        "ⲁⲙⲡⲉⲗⲟⲛ": "ambelon",            # Pi softening after Mey
        "ⲭⲉⲣⲉ": "shere",                 # Chi as 'sh' before 'e'
        "ⲭⲣⲓⲥⲧⲟⲥ": "khristos",            # Chi as 'kh' before consonant
        "ⲛ̀ⲑⲟⲕ": "enthok",                 # Jinkim becoming 'e'
    }

    print("Running phonetic tests...")
    for coptic, expected in tests.items():
        result = translit(coptic)
        status = "✅" if result == expected else f"❌ (Expected: {expected})"
        print(f"{coptic.ljust(15)} -> {result.ljust(15)} {status}")
