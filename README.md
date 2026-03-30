# 📚 ExamHelp — AI Study Assistant

A premium AI study chatbot powered by **Groq (llama-3.3-70b-versatile)** — study-focused, context-aware, and completely free to run.

## Features
- 📄 **PDF Upload** — Upload multiple PDFs and ask questions about them
- ▶️ **YouTube Transcripts** — Paste any YouTube link and get it analyzed
- 🌐 **Web Page Scraper** — Paste any article/wiki URL and chat about it
- 🃏 **Flashcard Generator** — Auto-generate Q&A flashcards from your materials
- 📝 **Quiz Mode** — Interactive multiple-choice quizzes with explanations
- 📊 **Mind Map** — Visual concept mapping with Mermaid.js diagrams
- 📅 **Study Planner** — AI-generated day-by-day revision timetables
- 🎭 **30+ AI Personas** — Learn from Einstein, Feynman, Socrates, and more
- 🌍 **Multi-language** — Study in English, Hindi, Spanish, French, and more
- 🎙️ **Voice Input** — Record voice questions with Whisper transcription
- 📸 **OCR Scanner** — Extract text from photos of handwritten notes
- 📈 **Analytics Dashboard** — Track mastery and study progress
- 🔑 **8-Key Rotation** — Automatic API key failover for uninterrupted usage
- ⬇️ **Export Chat** — Download your study session as Markdown
- 💾 **Persistent Sessions** — Save and reload study sessions

---

## Setup & Run Locally

### 1. Clone / Download the project
```bash
cd examhelp_ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key(s)
Get a **free** API key at [console.groq.com](https://console.groq.com)

**Option A** — Create a `.env` file (supports up to 8 keys for rotation):
```
GROQ_API_KEY_1=YOUR_NEW_KEY_HERE
GROQ_API_KEY_2=YOUR_NEW_KEY_HERE
```

**Option B** — Enter it directly in the app sidebar (no setup needed)

### 4. Run the app
```bash
streamlit run app.py
```

---

## Deploy to Streamlit Cloud (Free)

1. Push this folder to a **GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. In **Advanced Settings → Secrets**, add:
```toml
GROQ_API_KEY_1 = "YOUR_NEW_KEY_HERE"
GROQ_API_KEY_2 = "YOUR_NEW_KEY_HERE"
```
4. Deploy — done! 🎉

---

## Project Structure
```
examhelp_ai/
├── app.py                  # Main Streamlit app (1500+ lines)
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── .streamlit/
│   ├── config.toml         # Theme config
│   └── secrets.toml        # API keys (gitignored)
└── utils/
    ├── groq_client.py      # Groq API + streaming + key rotation
    ├── key_manager.py      # Multi-key pool with failover
    ├── pdf_handler.py      # PDF text extraction (PyMuPDF)
    ├── youtube_handler.py  # YouTube transcript fetcher
    ├── web_handler.py      # Web page scraper
    ├── personas.py         # 30+ historical figure personas
    ├── ocr_handler.py      # Image text extraction
    └── analytics.py        # Study analytics & charts
```

---

## Tech Stack
- **Frontend:** Streamlit with custom CSS (dark/light themes)
- **LLM:** Groq API (llama-3.3-70b-versatile / llama-3.1-8b-instant)
- **PDF:** PyMuPDF for text extraction
- **YouTube:** youtube-transcript-api
- **Web:** BeautifulSoup4 + Requests
- **Charts:** Plotly
- **Voice:** Groq Whisper API

## Notes
- Primary model: `llama-3.3-70b-versatile` (high quality, 128k context)
- Fallback model: `llama-3.1-8b-instant` (fast, for summaries)
- Max context injected: ~25,000 chars (fits within model limits)
- The bot is hard-locked to study/academic topics only
- Supports up to 8 API keys with automatic rotation
