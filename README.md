# 🔤 Coptic Transliteration Tool with AI Enhancement

> A modern web-based tool for transliterating Coptic text to Latin script, enhanced with Google's Gemini 2.5 Flash Lite AI model. **Live Application:** (https://coptic-transliterator-llm.streamlit.app/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ Features

- **🖊️ Flexible Input**: Enter Coptic text directly or upload `.txt` files.
- **✨ AI-Enhanced**: Combines rule-based transliteration with Google's Gemini 2.5 Flash Lite model for superior accuracy and context-aware results.
- **📊 Side-by-Side Comparison**: View both rule-based and AI-enhanced results simultaneously.
- **📱 User-Friendly**: Clean, modern Streamlit interface.
- **⬇️ Export Ready**: Download individual or combined transliteration results as `.txt` files.
- **🚀 Fast & Reliable**: Rule-based fallback ensures the tool always works even if the API is unreachable.

---

## 🚀 Quick Start

### Prerequisites

- [Python 3.9+](https://www.python.org/downloads/)
- Google Gemini API key (for AI enhancement - optional)

### Local Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/shehatamichael/coptic-transliterator-llm.git
   cd coptic-transliterator-llm
   ```

2. **Create Virtual Environment**

   ```bash
   python -m venv coptic-llm
   source coptic-llm/bin/activate  # On Windows: coptic-llm\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Access (Optional)**
   - Get your [Google AI Studio API key](https://makersuite.google.com/app/apikey)
   - Create `.env` file:

     ```env
     GEMINI_API_KEY=your-google-ai-api-key-here
     ```

   - **Note**: The tool works without an API key using rule-based transliteration only

5. **Launch the App**

   ```bash
   streamlit run app.py
   ```

   Your app will be available at `http://localhost:8501`

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Rule-based      │    │  Google Gemini  │
│   Frontend      │───▶│  Transliterator  │───▶│  2.5 Flash Lite │
│                 │    │  (Always Works)  │    │  (Enhancement)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

- **Frontend**: Streamlit provides the web interface with side-by-side comparison
- **Core Logic**: Rule-based transliteration ensures reliability
- **Enhancement**: Gemini 2.5 Flash Lite model via Google AI Studio API

---

## 📁 Project Structure

```
coptic-transliterator-llm/
├── app.py                 # Main Streamlit application
├── transliterator.py      # Core transliteration logic
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── LICENSE               # MIT License
└── README.md             # This file
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google AI Studio API key for AI enhancement | No | Rule-based only |

### SDK Configuration

The tool uses the official google-genai SDK for API communication, replacing raw HTTP requests. The client is initialized in app.py:

```python
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt,
    config=...
)
```

---

## 🔧 Advanced Usage

### API Integration

You can use the core transliteration functions in your own projects:

```python
from transliterator import translit

# Rule-based transliteration
coptic_text = "ⲡⲛⲟⲩⲧⲉ"
latin_text = translit(coptic_text)
print(latin_text)  # Output: pnoute
```

### Customization

- **Character Mappings**: Modify `char_map` in `transliterator.py`
- **Contextual Rules**: Update `_apply_contextual_rules()` method
- **UI Styling**: Customize CSS in `app.py`
- **System Instructions**: Modify the system_instruction prompt in app.py to adjust how the LLM formats the output.

---

## 📊 Performance & Limitations

### AI Enhancement Notes

- **Google AI Studio**: Uses generous free tier with rate limits
- **Fallback**: Rule-based method always available when AI is unavailable
- **Accuracy**: AI enhancement improves context-aware transliteration
- **Performance**: Rule-based is instant, AI enhancement takes 2-5 seconds

### Accuracy Comparison

- Rule-based transliteration provides consistent, fast results
- AI enhancement improves context-aware transliteration for complex texts
- Side-by-side comparison lets users choose the best result
- Performance varies with input complexity and model availability

---

## 📚 Examples

### Quick Examples

| Coptic | Rule-based | AI-Enhanced | Meaning |
|--------|------------|-------------|---------|
| ⲡⲛⲟⲩⲧⲉ | pnoute | pnoute | God |
| ⲧⲉⲕⲕⲗⲏⲥⲓⲁ | tekklesia | tekklesia | Church |
| ⲁⲅⲁⲡⲏ | agape | agape | Love |
| ⲙⲁⲣⲓⲁ | maria | maria | Mary |

### Usage in Code

```python
from transliterator import CopticTransliterator

# Create transliterator instance
ct = CopticTransliterator()

# Transliterate text
result = ct.translit("ⲁⲛⲟⲕ ⲟⲩⲛ ⲟⲩⲙⲁⲓⲛⲟⲩⲧⲉ")
print(result)  # Output: anok oun oumai̇noute
```

---

## 🤝 Contributing

### Getting Started

1. **Fork the Repository**
2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
4. **Test Thoroughly**

   ```bash
   streamlit run app.py
   ```

5. **Submit a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code style
- Test both with and without API keys
- Update documentation as needed
- Ensure mobile responsiveness

### Ideas for Contributions

- Additional contextual transliteration rules
- Support for other Coptic dialects
- Batch processing for large texts
- Performance optimizations
- Enhanced error handling

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💬 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/shehatamichael/coptic-transliterator-llm/issues)
- **Email**: <shehatam.dev@gmail.com>
- **Pull Requests**: Contributions welcome!

---

## 🙏 Acknowledgments

- Based on the original [coptic-transliterator](https://github.com/shehatamichael/coptic-transliterator)
- Powered by [Google AI Studio](https://makersuite.google.com/)
- Built with [Streamlit](https://streamlit.io/)
- Special thanks to the Coptic community for feedback and support

---

<div align="center">
  <p><strong>Made with ❤️ for the Coptic community</strong><br>
  <em>Preserving ancient language through modern technology</em></p>
</div>