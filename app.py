import streamlit as st
from google import genai
from google.genai import types
from transliterator import translit
import os
from dotenv import load_dotenv
import time
from typing import Optional
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file

# Get API key from Streamlit secrets or environment variables
try:
    # Try Streamlit secrets first (for deployed app)
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        logger.info("GEMINI_API_KEY loaded from Streamlit secrets")
    # Fallback to environment variable (for local development)
    elif "GEMINI_API_KEY" in os.environ:
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        logger.info("GEMINI_API_KEY loaded from environment variable")
    else:
        GEMINI_API_KEY = None
        logger.error(
            "GEMINI_API_KEY not found in secrets or environment variables")
        st.error("⚠️ API key not configured. Please contact the administrator.")
        st.stop()

except Exception as e:
    logger.error(f"Error loading API key: {str(e)}")
    st.error("⚠️ Error loading API configuration. Please contact the administrator.")
    st.stop()

# Streamlit natively hashes input parameters for caching, so we don't need hashlib


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def llm_transliterate(text: str) -> Optional[str]:
    """Function for LLM transliteration using Gemini 2.5 Flash Lite with native caching"""
    if not text or not text.strip() or not GEMINI_API_KEY:
        return None

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Prompt optimized for Gemini 2.5 Flash Lite using system instructions
    system_instruction = """You are an expert in Coptic language transliteration. Your task is to transliterate Coptic text to Latin script using standard transliteration conventions.
        Rules:
        - Convert each Coptic character to its Latin equivalent
        - Preserve word boundaries and spacing
        - Use lowercase Latin letters
        - **Crucially: The output MUST contain ONLY plain, unaccented Latin characters (ASCII a-z). No Coptic characters, no diacritics, and no special Latin characters (e.g., ā, ē, ī, ō, ū) are allowed in the final transliterated text.**
        - Do not add explanations, conversational filler, or additional text. Only return the transliterated text."""

    prompt = f"""Examples:
        - ⲡⲛⲟⲩⲧⲉ → pnoute
        - ⲧⲉⲕⲕⲗⲏⲥⲓⲁ → tekklesia  
        - ⲁⲅⲁⲡⲏ → agape
        - ⲙⲁⲣⲓⲁ → maria

        Transliterate this Coptic text to Latin script: {text}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
            )
        )

        if response.text:
            return response.text.strip()

        return None

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


# Page configuration
st.set_page_config(
    page_title="Coptic Transliteration Tool",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern CSS styling
st.markdown(
    """
<style>
    /* Global modern dark theme */
    .stApp {
        background-color: #0f1115;
        color: #e2e8f0;
    }
    
    /* Clean, flat main header */
    .main-header {
        background-color: #1a1d24;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #2d3139;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        color: #94a3b8;
    }
    
    /* Simplified Info Boxes */
    .info-box {
        background-color: #1a1d24;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #6366f1;
        margin: 1rem 0;
        color: #cbd5e1;
    }
    
    /* Sleek Result Info */
    .result-info {
        background-color: #1a1d24;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #2d3139;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
        color: #cbd5e1;
    }
    
    /* Text Area Styling */
    .stTextArea textarea {
        background-color: #14161b !important;
        border: 1px solid #2d3139 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
        font-size: 16px !important;
        font-family: 'Consolas', 'Monaco', monospace !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 1px #6366f1 !important;
    }
    
    .stTextArea textarea[disabled] {
        background-color: #1a1d24 !important;
        color: #e2e8f0 !important;
        opacity: 1 !important;
    }
    
    /* Modern Buttons */
    .stButton > button {
        background-color: #2d3139 !important;
        color: #f8fafc !important;
        border: 1px solid #3f444e !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        min-height: 44px !important;
    }
    
    .stButton > button:hover {
        background-color: #3f444e !important;
        border-color: #6366f1 !important;
    }
    
    /* Primary action button override */
    button[data-testid="baseButton-primary"] {
        background-color: #6366f1 !important;
        border-color: #6366f1 !important;
        color: white !important;
    }
    
    button[data-testid="baseButton-primary"]:hover {
        background-color: #4f46e5 !important;
        border-color: #4f46e5 !important;
    }
    
    /* File Uploader */
    .stFileUploader > div {
        background-color: #14161b !important;
        border: 1px dashed #3f444e !important;
        border-radius: 8px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #14161b !important;
        border-right: 1px solid #2d3139 !important;
    }
    
    /* Method Headers */
    .method-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        border-radius: 6px;
        text-align: center;
        background-color: #1a1d24;
        border: 1px solid #2d3139;
        color: #e2e8f0;
    }
    
    /* Footer styling */
    .footer-box {
        background-color: #1a1d24;
        border: 1px solid #2d3139;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin: 2rem 0;
        color: #94a3b8;
    }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
    [![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/shehata-consulting/coptic-transliterator-llm)
    """
    )
    st.markdown("---")
    st.markdown(
        """
    ### 🤝 Contribute
    - [Report Issues](https://github.com/shehata-consulting/coptic-transliterator-llm/issues)
    - [Submit Pull Requests](https://github.com/shehata-consulting/coptic-transliterator-llm/pulls)
    - [Fork the Project](https://github.com/shehata-consulting/coptic-transliterator-llm/fork)
    """
    )
    st.markdown("---")

    # API Status indicator with debugging
    st.markdown("### 🔌 AI Model Status")
    if GEMINI_API_KEY:
        st.success("✅ AI Enhancement Available")
        st.info("Using Gemini 2.5 Flash Lite for superior accuracy")
    else:
        st.warning("⚠️ Rule-based Mode Only")
        st.info("Set GEMINI_API_KEY for AI enhancement")

    st.markdown("---")

    # Usage statistics
    if "transliteration_count" not in st.session_state:
        st.session_state.transliteration_count = 0

    st.markdown(f"### 📊 Session Stats")
    st.metric("Transliterations", st.session_state.transliteration_count)

    st.markdown("---")
    st.markdown("### ℹ️ How It Works")
    st.markdown(
        """
    <div class="info-box">
        <h4>Two-Method Comparison:</h4>
        <strong>1️⃣ Rule-based</strong> transliteration (fast, consistent)<br>
        <strong>2️⃣ AI enhancement</strong> with Gemini 2.5 Flash Lite (context-aware improvements)<br><br>
        <strong>📊 Side-by-side results</strong> let you compare both methods!
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎯 Features")
    st.markdown(
        """
    <div class="info-box">
        <ul>
            <li>✅ Handles complex Coptic characters</li>
            <li>✨ Advanced AI with Gemini 2.5 Flash Lite</li>
            <li>📊 Method comparison view</li>
            <li>📱 Mobile-friendly interface</li>
            <li>⬇️ Download results</li>
            <li>🆓 Completely free to use</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        """
    ### 📧 Contact
    **Michael Shehata** 📧 shehatam.dev@gmail.com
    
    ### ⭐ Support
    If this tool helps you, consider giving it a star on GitHub!
    """
    )

# Main header
st.markdown(
    """
<div class="main-header">
    <h1>📱 Coptic Transliteration Tool</h1>
    <p>AI-enhanced transliteration with Gemini 2.5 Flash Lite for Coptic text to Latin script</p>
</div>
""",
    unsafe_allow_html=True,
)

# Initialize session state for the text input
if "text_input" not in st.session_state:
    st.session_state.text_input = ""

# Quick examples section
st.markdown("#### ✨ Try These Examples")
st.markdown("---")

col1, col2, col3 = st.columns(3)
example_texts = [("ⲡⲛⲟⲩⲧⲉ", "God"), ("ⲧⲉⲕⲕⲗⲏⲥⲓⲁ", "Church"), ("ⲁⲅⲁⲡⲏ", "Love")]

# Callback function to handle the state update securely


def set_example_text(text):
    # Update the text area
    st.session_state.text_input = text
    # Clear previous results so the screen resets for the new example
    if "results" in st.session_state:
        st.session_state.results["has_results"] = False


for i, (coptic, english) in enumerate(example_texts):
    with [col1, col2, col3][i]:
        st.button(
            f"{coptic}\n({english})",
            key=f"example_{i}",
            use_container_width=True,
            help=f"Click to load example: {coptic} ({english})",
            on_click=set_example_text,
            args=(coptic,)  # Passes the Coptic text to the callback function
        )

# MAIN INTERFACE
st.markdown("---")
st.markdown("#### 🔄 Transliteration Interface")
st.markdown("---")

# Create two main columns: Input (left) and Results (right)
main_col1, main_col2 = st.columns([1, 1])

with main_col1:
    st.markdown("##### 📝 Input")

    # Text input utilizing key directly instead of value
    input_text = st.text_area(
        "Enter Coptic Text",
        height=200,
        placeholder="Paste your Coptic text here or click an example above...",
        key="text_input",
        help="You can type or paste Coptic Unicode text here",
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Or Upload a Text File",
        type="txt",
        help="Upload a .txt file containing Coptic text",
    )

    # Transliteration button
    if st.button("🚀 Transliterate Text", type="primary", use_container_width=True):
        processing_text = ""

        # Check for input text from text area
        if st.session_state.text_input and st.session_state.text_input.strip():
            processing_text = st.session_state.text_input.strip()
        # Check for uploaded file
        elif uploaded_file:
            try:
                processing_text = uploaded_file.read().decode("utf-8").strip()
            except Exception as e:
                st.error(
                    "❌ Error reading file. Please ensure it's a valid UTF-8 text file.")
                processing_text = ""

        if processing_text:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("🔄 Starting transliteration...")
            progress_bar.progress(25)

            try:
                # Rule-based transliteration (always works)
                status_text.text("📝 Applying rule-based transliteration...")
                progress_bar.progress(50)
                rule_based_output = translit(processing_text)

                # AI enhancement (if available)
                llm_output = None
                if GEMINI_API_KEY:
                    status_text.text(
                        "✨ Enhancing with Gemini 2.5 Flash Lite...")
                    progress_bar.progress(75)

                    llm_output = llm_transliterate(processing_text)

                    if llm_output:
                        st.success("✅ AI enhancement successful!")
                    else:
                        st.info(
                            "ℹ️ AI enhancement unavailable, showing rule-based result in both columns")
                        st.warning(
                            "⚠️ Using rule-based transliteration due to API issues.")
                        llm_output = rule_based_output
                else:
                    st.info(
                        "ℹ️ API key not configured, showing rule-based result in both columns")
                    llm_output = rule_based_output

                progress_bar.progress(100)
                status_text.text("✅ Transliteration completed!")

                # Update session stats
                st.session_state.transliteration_count += 1

                # Store results in session state to display them in the right column
                st.session_state.results = {
                    "rule_based": rule_based_output,
                    "llm_output": llm_output,
                    "processing_text": processing_text,
                    "has_results": True,
                }

                # Clear progress indicators
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(
                    "❌ An error occurred during transliteration. Please try again.")
                st.error(f"Error details: {str(e)}")
        else:
            st.warning("⚠️ Please provide input text or upload a file.")

with main_col2:
    st.markdown("##### 📊 Results")

    if "results" in st.session_state and st.session_state.results.get("has_results", False):
        rule_based_output = st.session_state.results["rule_based"]
        llm_output = st.session_state.results["llm_output"]
        processing_text = st.session_state.results["processing_text"]

        ai_status = (
            "Gemini 2.5 Flash Lite Enhanced"
            if GEMINI_API_KEY and llm_output != rule_based_output
            else "Rule-based (Fallback)"
        )
        st.markdown(
            f"""
        <div class="result-info">
            <strong>Input Length:</strong> {len(processing_text)} characters<br>
            <strong>Rule-based Output:</strong> {len(rule_based_output)} characters<br>
            <strong>AI-Enhanced Output:</strong> {len(llm_output)} characters<br>
            <strong>AI Model:</strong> {ai_status}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Rule-based result
        st.markdown(
            '<div class="method-header">📝 Rule-based Method</div>', unsafe_allow_html=True)
        st.text_area(
            "Rule-based Transliteration",
            value=rule_based_output if rule_based_output else "Results will appear here...",
            height=100,
            disabled=True,
            key="rule_result_display",
            label_visibility="collapsed",
        )

        # AI-enhanced result
        st.markdown(
            '<div class="method-header">✨ Gemini 2.5 Flash Lite Enhanced</div>', unsafe_allow_html=True)
        st.text_area(
            "AI-Enhanced Transliteration",
            value=llm_output if llm_output else "Results will appear here...",
            height=100,
            disabled=True,
            key="ai_result_display",
            label_visibility="collapsed",
        )

        # Download section
        st.markdown("#### ⬇️ Download Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                label="📝 Rule-based",
                data=rule_based_output,
                file_name=f"rule_based_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="✨ Gemini Enhanced",
                data=llm_output,
                file_name=f"gemini_enhanced_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col3:
            combined_output = (
                f"Rule-based Transliteration:\n{rule_based_output}\n\n"
                f"Gemini 2.5 Flash Lite Enhanced Transliteration:\n{llm_output}\n\n"
                f"Original Coptic Text:\n{processing_text}"
            )
            st.download_button(
                label="📊 Both",
                data=combined_output,
                file_name=f"combined_results_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if rule_based_output != llm_output and GEMINI_API_KEY:
            st.info("💡 **Different Results Detected:** The AI-enhanced method produced a different result than the rule-based method. Compare both to see which better fits your needs!")
        elif not GEMINI_API_KEY:
            st.warning(
                "🔑 **API Key Not Configured:** Set your Google AI Studio API key to enable AI-enhanced transliteration for potentially improved results.")

    else:
        st.info(
            "Enter text or upload a file and click 'Transliterate' to see results here!")
        st.markdown(
            '<div class="method-header">📝 Rule-based Method</div>', unsafe_allow_html=True)
        st.text_area("Rule-based Transliteration", value="Results will appear here...",
                     height=100, disabled=True, key="rule_placeholder", label_visibility="collapsed")
        st.markdown(
            '<div class="method-header">✨ AI-Enhanced Method</div>', unsafe_allow_html=True)
        st.text_area("AI-Enhanced Transliteration", value="Results will appear here...",
                     height=100, disabled=True, key="ai_placeholder", label_visibility="collapsed")

# Instructions section
st.markdown("---")
st.markdown("### 📖 Instructions")

with st.expander("📖 How to Use This Tool", expanded=False):
    st.markdown(
        """
    ### 🚀 Quick Start Guide
    
    1. **Choose Input Method:**
       - Type/paste Coptic text directly in the text area
       - Upload a `.txt` file containing Coptic text
       - Click one of the example buttons for quick testing
    
    2. **Transliterate:**
       - Click the "🚀 Transliterate Text" button
       - Wait for processing (usually takes 2-5 seconds)
       - View your results in the Results panel on the right
    
    3. **Compare & Choose:**
       - Review both the Rule-based and AI-Enhanced results
       - Choose the method that works best for your text
       - Download individual results or both together
    
    4. **Save Results:**
       - Download rule-based results as `.txt` file
       - Download AI-enhanced results as `.txt` file
       - Download combined results with both methods
    
    ### 🔧 Technical Details
    
    **Rule-based Transliteration:**
    - Fast and consistent
    - Based on linguistic rules
    - Works offline
    - Handles all standard Coptic characters
    - Always available as fallback
    
    **AI Enhancement:**
    - Uses Gemini 2.5 Flash Lite language model
    - Context-aware improvements
    - Better handling of ambiguous cases
    - Requires internet connection and API key
    - Shows rule-based result if unavailable
    
    ### 📊 Side-by-Side Comparison
    
    **Why Both Methods?**
    - Different approaches may yield different results
    - Rule-based is consistent and predictable
    - AI-enhanced considers context and patterns
    - You can choose the best result for your needs
    """
    )

# Footer
st.markdown("---")
st.markdown(
    """
<div class="footer-box">
    <h3 style="color: white; margin-top: 0;">🛠️ Open Source & Free Forever</h3>
    <p style="font-size: 1.1em; margin: 15px 0;">
        This tool is completely open source and will always be free to use!
    </p>
    <p>
        <a href="https://github.com/shehata-consulting/coptic-transliterator-llm" target="_blank" 
           style="text-decoration: none; color: white;">
            <img src="https://img.shields.io/badge/⭐_Star_on_GitHub-white?style=for-the-badge&logo=github&logoColor=black" 
                 alt="Star on GitHub">
        </a>
    </p>
    <p style="margin-top: 20px; font-size: 1.1em; color: white;">
        <strong>Made with ❤️ for the Coptic community</strong>
    </p>
    <p style="font-style: italic;">
        Preserving ancient language through modern technology
    </p>
</div>
""",
    unsafe_allow_html=True,
)
