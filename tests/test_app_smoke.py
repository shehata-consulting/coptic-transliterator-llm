#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test: the full Streamlit app must boot without raising.

Runs with no GEMINI_API_KEY in CI, which also guards the rule-based-only
fallback path (the app must not st.stop() when unconfigured).
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def test_app_boots_without_error():
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    assert not at.exception


def test_rule_based_flow_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    # Keep the test offline even if a local secrets.toml holds a real key
    at.secrets["GEMINI_API_KEY"] = ""
    at.run()
    assert not at.exception

    at.text_area(key="text_input").set_value("ⲡⲛⲟⲩⲧⲉ").run()
    button = next(b for b in at.button if b.label == "🚀 Transliterate")
    button.set_value(True).run()
    assert not at.exception
    assert at.session_state["results"]["rule_based"] == "pnoute"
    assert at.session_state["results"]["llm_note"] == "no_key"
