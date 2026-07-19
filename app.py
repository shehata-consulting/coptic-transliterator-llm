import html
import json
import logging
import os
import time
import urllib.parse
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from coptictranslit import translit_with_warnings
from text_utils import LLM_MAX_CHARS, chunk_text, clean_llm_output, interlinear_lines

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file

REPO_URL = "https://github.com/shehata-consulting/coptic-transliterator-llm"
TEXTS_PATH = Path(__file__).parent / "texts" / "library.json"


def get_api_key() -> Optional[str]:
    """Streamlit secrets first (deployed app), then environment (local dev).

    Returns None when unconfigured — the app then runs in rule-based-only
    mode instead of stopping, so the tool keeps working without any key.
    """
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            logger.info("GEMINI_API_KEY loaded from Streamlit secrets")
            return st.secrets["GEMINI_API_KEY"]
    except Exception:  # no secrets.toml at all
        pass
    if "GEMINI_API_KEY" in os.environ:
        logger.info("GEMINI_API_KEY loaded from environment variable")
        return os.environ.get("GEMINI_API_KEY")
    logger.info("No GEMINI_API_KEY configured — running in rule-based mode")
    return None


GEMINI_API_KEY = get_api_key()

SYSTEM_INSTRUCTION = """You are an expert in Coptic language transliteration. Your task is to transliterate Coptic text to Latin script using standard transliteration conventions.
    Rules:
    - Convert each Coptic character to its Latin equivalent
    - Preserve word boundaries, line breaks, and spacing
    - Use lowercase Latin letters
    - **Crucially: The output MUST contain ONLY plain, unaccented Latin characters (ASCII a-z). No Coptic characters, no diacritics, and no special Latin characters (e.g., ā, ē, ī, ō, ū) are allowed in the final transliterated text.**
    - Do not add explanations, conversational filler, or additional text. Only return the transliterated text."""


@st.cache_resource(show_spinner=False)
def get_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def llm_transliterate(text: str) -> Optional[str]:
    """AI transliteration via Gemini 2.5 Flash Lite.

    Long input is split into line-boundary chunks to stay within free-tier
    request sizes, and every response is validated down to plain ASCII.
    Returns None on any failure so the caller falls back to rule-based.
    """
    if not text or not text.strip() or not GEMINI_API_KEY:
        return None

    pieces = []
    for chunk in chunk_text(text):
        prompt = f"""Examples:
            - ⲡⲛⲟⲩⲧⲉ → pnoute
            - ⲧⲉⲕⲕⲗⲏⲥⲓⲁ → tekklesia
            - ⲁⲅⲁⲡⲏ → agape
            - ⲙⲁⲣⲓⲁ → maria

            Transliterate this Coptic text to Latin script: {chunk}"""
        response = None
        for attempt in range(2):  # one retry: 503s during demand spikes are common
            try:
                response = get_client().models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                    ),
                )
                break
            except Exception as e:
                logger.error(f"Gemini request failed (attempt {attempt + 1}): {e}")
                if attempt == 0:
                    time.sleep(2)
        if response is None:
            return None

        cleaned = clean_llm_output(response.text)
        if cleaned is None:
            logger.warning("Gemini returned unusable output; falling back")
            return None
        pieces.append(cleaned)

    return "\n".join(pieces)


@st.cache_data(show_spinner=False)
def load_text_library() -> list:
    with open(TEXTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def interlinear_html(lines) -> str:
    """Render interlinear word pairs as HTML (shared by app view and export)."""
    parts = ['<div class="interlinear">']
    for line in lines:
        if not line:
            parts.append('<div class="il-gap"></div>')
            continue
        words = "".join(
            f'<span class="il-word">'
            f'<span class="il-cop">{html.escape(cop)}</span>'
            f'<span class="il-lat">{html.escape(lat)}</span></span>'
            for cop, lat in line
        )
        parts.append(f'<div class="il-line">{words}</div>')
    parts.append("</div>")
    return "".join(parts)


def build_printable_html(lines) -> str:
    """A self-contained, print-friendly page of the interlinear view."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Coptic Transliteration</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Coptic&display=swap');
body {{ font-family: Georgia, 'Times New Roman', serif; max-width: 48rem;
       margin: 2rem auto; padding: 0 1rem; color: #111; background: #fff; }}
h1 {{ font-size: 1.4rem; border-bottom: 1px solid #ccc; padding-bottom: .5rem; }}
.il-line {{ display: flex; flex-wrap: wrap; gap: .3rem 1.4rem; margin-bottom: 1.2rem; }}
.il-word {{ display: flex; flex-direction: column; align-items: center; }}
.il-cop {{ font-family: 'Noto Sans Coptic', serif; font-size: 1.5rem; line-height: 1.4; }}
.il-lat {{ font-size: .9rem; color: #555; }}
.il-gap {{ height: 1rem; }}
footer {{ margin-top: 3rem; font-size: .8rem; color: #888;
         border-top: 1px solid #ccc; padding-top: .5rem; }}
</style>
</head>
<body>
<h1>Coptic Transliteration</h1>
{interlinear_html(lines)}
<footer>Generated by the Coptic Transliteration Tool &mdash; {REPO_URL}</footer>
</body>
</html>
"""


# ─── Page setup ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Coptic Transliteration Tool",
    page_icon="🔤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Colors, radii, and fonts come from .streamlit/config.toml; CSS here covers
# what the theme can't: font loading, the hero, and the interlinear layout.
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Coptic&display=swap');

    /* Hide Streamlit chrome for a cleaner page */
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stDecoration"] { display: none; }

    /* Hero header */
    .hero { padding: .4rem 0 .2rem 0; }
    .hero-badges { display: flex; gap: .5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .hero-badges span {
        font-size: .7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: .07em; color: #A5B0FF;
        background: rgba(124, 108, 240, .12);
        border: 1px solid rgba(124, 108, 240, .35);
        padding: .28rem .7rem; border-radius: 999px;
    }
    .hero h1 {
        font-size: 2.5rem; font-weight: 800; letter-spacing: -.03em;
        line-height: 1.12; margin: 0 0 .5rem 0; padding: 0;
    }
    .hero h1 .grad {
        background: linear-gradient(90deg, #8B7CF8 0%, #C084FC 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .hero p { color: #97A0B5; font-size: 1.02rem; margin: 0 0 .4rem 0; max-width: 44rem; }

    /* Coptic input */
    .stTextArea textarea {
        font-family: 'Noto Sans Coptic', 'Inter', sans-serif !important;
        font-size: 17px !important;
        line-height: 1.9 !important;
    }

    /* Coptic showcase block (Text Library) */
    .coptic-display {
        font-family: 'Noto Sans Coptic', 'Inter', sans-serif;
        font-size: 1.5rem;
        line-height: 2;
        background-color: #151823;
        border: 1px solid #232839;
        border-radius: 12px;
        padding: 1.1rem 1.35rem;
        margin: .5rem 0 1rem 0;
    }

    /* Interlinear view */
    .interlinear {
        background-color: #151823;
        border: 1px solid #232839;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin: .5rem 0;
    }
    .il-line { display: flex; flex-wrap: wrap; gap: .3rem 1.35rem; margin-bottom: 1.15rem; }
    .il-word {
        display: flex; flex-direction: column; align-items: center;
        padding: .15rem .35rem; border-radius: .45rem;
        transition: background .15s ease;
    }
    .il-word:hover { background: rgba(124, 108, 240, .16); }
    .il-cop { font-family: 'Noto Sans Coptic', 'Inter', sans-serif;
              font-size: 1.45rem; line-height: 1.5; color: #F4F6FB; }
    .il-lat { font-size: .9rem; color: #8E99B7; }
    .il-gap { height: 1rem; }

    /* Button micro-interactions */
    .stButton > button, .stDownloadButton > button {
        transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        box-shadow: 0 6px 22px rgba(124, 108, 240, .28);
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ─── Successor-app banner ────────────────────────────────────────────────────
# The Expo PWA (coptic-transliterator-app) is the actively developed successor;
# this Streamlit app stays up as the AI-enhanced fallback until Phase 2 lands
# there. Keep the banner until then.

st.markdown(
    """
<div style="display:flex; align-items:center; gap:.6rem; flex-wrap:wrap;
            background: rgba(124, 108, 240, .12);
            border: 1px solid rgba(124, 108, 240, .35);
            border-radius: 12px; padding: .65rem 1rem; margin-bottom: 1rem;">
  <span style="font-size:1.1rem;">🚀</span>
  <span style="color:#E8EAF6;">
    <strong>A new, faster app is here</strong> — installable on your phone and
    works offline, perfect for following along in church:
    <a href="https://coptic-transliterator-app.web.app"
       style="color:#A5B0FF; font-weight:600;">coptic-transliterator-app.web.app</a>
  </span>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Session state ───────────────────────────────────────────────────────────

if "text_input" not in st.session_state:
    st.session_state.text_input = ""
if "transliteration_count" not in st.session_state:
    st.session_state.transliteration_count = 0


def set_input_text(text: str):
    st.session_state.text_input = text
    if "results" in st.session_state:
        st.session_state.results["has_results"] = False


def append_input_char(char: str):
    st.session_state.text_input += char


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f"[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)]({REPO_URL})"
    )
    st.markdown("---")

    st.markdown("### AI Model Status")
    if GEMINI_API_KEY:
        st.success("AI enhancement available")
        st.caption("Gemini 2.5 Flash Lite adds context-aware refinements.")
    else:
        st.info("Rule-based mode")
        st.caption(
            "No API key configured — the rule-based engine handles everything. "
            "Set GEMINI_API_KEY to enable AI enhancement."
        )

    st.markdown("---")
    st.metric("Transliterations this session", st.session_state.transliteration_count)

    st.markdown("---")
    st.markdown(
        f"""
        ### 🤝 Contribute
        - [Report an issue]({REPO_URL}/issues)
        - [Submit a pull request]({REPO_URL}/pulls)

        ### 📧 Contact
        **Michael Shehata** — shehatam.dev@gmail.com
        """
    )

# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="hero">
    <div class="hero-badges">
        <span>Free forever</span><span>Open source</span><span>AI-enhanced</span>
    </div>
    <h1>Coptic <span class="grad">Transliteration</span></h1>
    <p>Follow along with Coptic church services — rule-based Greco-Bohairic
    phonetics, optionally refined by AI. Made with ❤️ for the Coptic community.</p>
</div>
""",
    unsafe_allow_html=True,
)

tab_main, tab_library, tab_guide, tab_about = st.tabs(
    ["🔤 Transliterate", "📚 Text Library", "🗣️ Pronunciation Guide", "ℹ️ About"]
)

# ─── Transliterate tab ───────────────────────────────────────────────────────

COPTIC_ALPHABET = [
    ("ⲁ", "Alpha"), ("ⲃ", "Vita"), ("ⲅ", "Gamma"), ("ⲇ", "Delta"),
    ("ⲉ", "Eie"), ("ⲋ", "Soou"), ("ⲍ", "Zeta"), ("ⲏ", "Eta"),
    ("ⲑ", "Theta"), ("ⲓ", "Iota"), ("ⲕ", "Kappa"), ("ⲗ", "Laula"),
    ("ⲙ", "Mey"), ("ⲛ", "Ney"), ("ⲝ", "Eksi"), ("ⲟ", "O"),
    ("ⲡ", "Pi"), ("ⲣ", "Ro"), ("ⲥ", "Sima"), ("ⲧ", "Tav"),
    ("ⲩ", "Epsilon"), ("ⲫ", "Phi"), ("ⲭ", "Khi"), ("ⲯ", "Epsi"),
    ("ⲱ", "Omega"), ("ϣ", "Shai"), ("ϥ", "Fai"), ("ϧ", "Khai"),
    ("ϩ", "Hori"), ("ϫ", "Janja"), ("ϭ", "Chima"), ("ϯ", "Ti"),
]

with tab_main:
    col_input, col_results = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("##### Input")

        examples = [("ⲡⲛⲟⲩⲧⲉ", "God"), ("ⲧⲉⲕⲕⲗⲏⲥⲓⲁ", "Church"), ("ⲁⲅⲁⲡⲏ", "Love")]
        ex_cols = st.columns(len(examples))
        for i, (coptic, english) in enumerate(examples):
            ex_cols[i].button(
                f"{coptic} · {english}",
                key=f"example_{i}",
                use_container_width=True,
                help=f"Load example: {coptic} ({english})",
                on_click=set_input_text,
                args=(coptic,),
            )

        st.text_area(
            "Enter Coptic text",
            height=220,
            placeholder="Paste Coptic text here, pick an example above, "
            "or open the character palette below…",
            key="text_input",
            help="Type or paste Coptic Unicode text",
        )

        with st.expander("⌨️ Coptic character palette"):
            st.caption("No Coptic keyboard? Tap letters to build your text.")
            palette_cols = st.columns(8)
            for i, (char, name) in enumerate(COPTIC_ALPHABET):
                palette_cols[i % 8].button(
                    char,
                    key=f"palette_{i}",
                    help=name,
                    use_container_width=True,
                    on_click=append_input_char,
                    args=(char,),
                )
            extra_cols = st.columns(8)
            extra_cols[0].button(
                "◌̀",
                key="palette_jinkim",
                help="Jinkim (adds an 'e' sound before a consonant)",
                use_container_width=True,
                on_click=append_input_char,
                args=("̀",),
            )
            extra_cols[1].button(
                "␣",
                key="palette_space",
                help="Space",
                use_container_width=True,
                on_click=append_input_char,
                args=(" ",),
            )

        uploaded_file = st.file_uploader(
            "Or upload a text file",
            type="txt",
            help="A .txt file containing Coptic text (UTF-8)",
        )

        if st.button(
            "Transliterate",
            key="transliterate_btn",
            type="primary",
            use_container_width=True,
        ):
            processing_text = ""
            if st.session_state.text_input and st.session_state.text_input.strip():
                processing_text = st.session_state.text_input.strip()
                if uploaded_file:
                    st.info(
                        "Using the typed text. Clear the text box to "
                        "transliterate the uploaded file instead."
                    )
            elif uploaded_file:
                try:
                    processing_text = uploaded_file.read().decode("utf-8").strip()
                except Exception:
                    st.error(
                        "❌ Could not read the file. Please ensure it's a "
                        "valid UTF-8 text file."
                    )

            if processing_text:
                with st.status("Transliterating…", expanded=False) as status:
                    st.write("Applying rule-based transliteration…")
                    rule_based_output, unmapped = translit_with_warnings(
                        processing_text
                    )

                    llm_output = None
                    llm_note = None
                    if not GEMINI_API_KEY:
                        llm_note = "no_key"
                    elif len(processing_text) > LLM_MAX_CHARS:
                        llm_note = "too_long"
                    else:
                        st.write("Asking Gemini 2.5 Flash Lite…")
                        llm_output = llm_transliterate(processing_text)
                        if llm_output is None:
                            llm_note = "api_failed"

                    status.update(label="Transliteration complete", state="complete")

                st.session_state.transliteration_count += 1
                st.session_state.results = {
                    "rule_based": rule_based_output,
                    "llm_output": llm_output,
                    "llm_note": llm_note,
                    "unmapped": unmapped,
                    "processing_text": processing_text,
                    "has_results": True,
                }
            else:
                st.warning("⚠️ Please enter text or upload a file first.")

    with col_results:
        st.markdown("##### Results")

        results = st.session_state.get("results", {})
        if results.get("has_results"):
            rule_based_output = results["rule_based"]
            llm_output = results["llm_output"]
            llm_note = results["llm_note"]
            processing_text = results["processing_text"]

            if results["unmapped"]:
                st.warning(
                    "Some characters were not recognized and passed through "
                    f"unchanged: {results['unmapped']} — "
                    f"[let us know]({REPO_URL}/issues) so we can add them."
                )
            if llm_note == "too_long":
                st.info(
                    f"Text exceeds {LLM_MAX_CHARS:,} characters, so AI "
                    "enhancement was skipped to stay within free limits. "
                    "The rule-based engine handled the full text."
                )
            elif llm_note == "api_failed":
                st.info(
                    "AI enhancement is temporarily unavailable — showing the "
                    "rule-based result, which always works."
                )

            view = st.segmented_control(
                "View",
                ["Text", "Interlinear"],
                default="Text",
                label_visibility="collapsed",
            )

            if view != "Interlinear":
                st.markdown("**Rule-based**")
                st.code(rule_based_output, language=None, wrap_lines=True)
                if llm_output:
                    st.markdown("**AI-enhanced** · Gemini 2.5 Flash Lite")
                    st.code(llm_output, language=None, wrap_lines=True)
                    if llm_output != rule_based_output:
                        st.caption(
                            "💡 The two methods differ — compare and pick "
                            "what reads best."
                        )
            else:
                source = rule_based_output
                if llm_output and llm_output != rule_based_output:
                    pick = st.segmented_control(
                        "Interlinear source",
                        ["Rule-based", "AI-enhanced"],
                        default="Rule-based",
                    )
                    if pick == "AI-enhanced":
                        source = llm_output
                lines = interlinear_lines(processing_text, source)
                st.markdown(interlinear_html(lines), unsafe_allow_html=True)

            st.markdown("**Download**")
            dl1, dl2, dl3 = st.columns(3)
            stamp = int(time.time())
            dl1.download_button(
                "📝 Rule-based",
                data=rule_based_output,
                file_name=f"rule_based_{stamp}.txt",
                mime="text/plain",
                use_container_width=True,
            )
            dl2.download_button(
                "✨ AI-enhanced",
                data=llm_output or rule_based_output,
                file_name=f"ai_enhanced_{stamp}.txt",
                mime="text/plain",
                use_container_width=True,
                disabled=not llm_output,
            )
            dl3.download_button(
                "🖨️ Printable page",
                data=build_printable_html(
                    interlinear_lines(processing_text, rule_based_output)
                ),
                file_name=f"interlinear_{stamp}.html",
                mime="text/html",
                use_container_width=True,
                help="Interlinear view as a printable HTML page — open it "
                "and print to PDF for service bulletins.",
            )

            issue_body = (
                f"**Input (Coptic):**\n{processing_text}\n\n"
                f"**Rule-based output:**\n{rule_based_output}\n\n"
                f"**AI-enhanced output:**\n{llm_output or '(not available)'}\n\n"
                "**What should it be instead?**\n"
            )
            issue_url = f"{REPO_URL}/issues/new?" + urllib.parse.urlencode(
                {"title": "Transliteration correction", "body": issue_body[:4000]}
            )
            st.caption(
                f"Spotted a wrong transliteration? [Report it in one click]({issue_url}) "
                "— your input and both outputs are pre-filled."
            )
        else:
            st.info(
                "Enter text (or upload a file) and click **Transliterate** — "
                "results appear here, as plain text or an interlinear "
                "Coptic-over-Latin view."
            )

# ─── Text Library tab ────────────────────────────────────────────────────────

with tab_library:
    st.markdown("##### 📚 Common liturgical texts")
    st.caption(
        "A community-maintained collection of short excerpts. Spot an error "
        f"or want to add a text? [Open an issue or PR]({REPO_URL}/issues) — "
        "the library lives in `texts/library.json`."
    )

    library = load_text_library()
    titles = [t["title"] for t in library]
    selected = st.selectbox("Choose a text", titles)
    entry = library[titles.index(selected)]

    st.markdown(
        f'<div class="coptic-display">{html.escape(entry["coptic"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**Meaning:** {entry['meaning']}")
    st.markdown(f"**When you'll hear it:** {entry['occasion']}")

    st.button(
        "🔤 Load into transliterator",
        type="primary",
        on_click=set_input_text,
        args=(entry["coptic"],),
        help="Then switch to the Transliterate tab and press Transliterate",
    )

# ─── Pronunciation Guide tab ─────────────────────────────────────────────────

with tab_guide:
    st.markdown("##### 🗣️ Letter-by-letter pronunciation")
    st.caption(
        "Greco-Bohairic pronunciation as used in Coptic Orthodox services. "
        "Context-sensitive letters show their variants."
    )
    st.markdown(
        """
| Coptic | Name | Latin | Sounds like |
|:------:|------|-------|-------------|
| ⲁ | Alpha | a | [ɑː] as in *mark* |
| ⲃ | Vita | v / b | *v* before vowels, *b* elsewhere |
| ⲅ | Gamma | g / gh / n | *g* before front vowels, *n* before ⲅ, *gh* elsewhere |
| ⲇ | Delta | d | [d] as in *day* |
| ⲉ | Eie | e | [ɛ] as in *send* |
| ⲋ | Soou | 6 | the numeral six |
| ⲍ | Zeta | z | [z] as in *zoo* |
| ⲏ | Eta | e | [ɛ] as in *send* |
| ⲑ | Theta | th | [θ] as in *thanks* |
| ⲓ | Iota | i | [i] as in *eat* |
| ⲕ | Kappa | k | [k] as in *key* |
| ⲗ | Laula | l | [l] as in *lion* |
| ⲙ | Mey | m | [m] as in *may* |
| ⲛ | Ney | n | [n] as in *no* |
| ⲝ | Eksi | x | [ks] as in *taxi* |
| ⲟ | O | o | [oʊ] as in *code* |
| ⲡ | Pi | p | [p] as in *pizza*, *b* after ⲙ |
| ⲣ | Ro | r | [r] as in *rope* |
| ⲥ | Sima | s | [s] as in *see* |
| ⲧ | Tav | t | [t] as in *time*, *d* after ⲛ |
| ⲩ | Epsilon | u / v | *v* after ⲁ/ⲉ, *ou* in ⲟⲩ |
| ⲫ | Phi | ph | [f] as in *Phil* |
| ⲭ | Khi | kh / sh | *sh* before front vowels, [x] elsewhere |
| ⲯ | Epsi | ps | [ps] as in *wraps* |
| ⲱ | Omega | o | [oʊ] as in *code* |
| ϣ | Shai | sh | [ʃ] as in *she* |
| ϥ | Fai | f | [f] as in *fun* |
| ϧ | Khai | kh | [x], guttural *kh* |
| ϩ | Hori | h | [h] as in *happy* |
| ϫ | Janja | j | [dʒ] as in *joy* |
| ϭ | Chima | ch | [tʃ] as in *church* |
| ϯ | Ti | ti | [ti] as in *tea* |
| ◌̀ | Jinkim | e | adds an *e* sound before the consonant it sits on |
"""
    )

# ─── About tab ───────────────────────────────────────────────────────────────

with tab_about:
    st.markdown(
        f"""
##### ℹ️ About this tool

The vision of this project is to help English speakers follow along with
Coptic church services by providing accurate, transparent transliterations
of Coptic text into Latin script.

**How it works**

1. A **rule-based engine** applies Greco-Bohairic phonetic rules — fast,
   consistent, works offline, and always available.
2. When configured, **Gemini 2.5 Flash Lite** refines the result with
   context-aware adjustments. If the AI is unavailable for any reason, the
   rule-based result is shown — the tool never goes down with it.

**Views**

- **Side by side** compares both methods so you can pick the better reading.
- **Interlinear** stacks each Latin word under its Coptic word — ideal for
  following along in a service. The printable download turns it into a
  bulletin-ready page.

**Free forever**

This tool is open source ([MIT license]({REPO_URL}/blob/main/LICENSE)) and
runs entirely on free infrastructure. If it helps you, consider
[starring it on GitHub]({REPO_URL}) or contributing texts, rules, and fixes.

**Credits**

Based on the original [coptic-transliterator](https://github.com/shehata-consulting/coptic-transliterator)
(Michael Shehata, Montclair State University, 2020). Special thanks to the
Coptic community for feedback and support.

*Preserving ancient language through modern technology.*
"""
    )
