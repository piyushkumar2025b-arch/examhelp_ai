# 📚 ExamHelp — AI Study Assistant

A Claude-like study chatbot powered by **Groq (llama3-8b-8192)** — study-focused, context-aware, and completely free to run.

## Features
- 📄 **PDF Upload** — Upload multiple PDFs and ask questions about them
- ▶️ **YouTube Transcripts** — Paste any YouTube link and get it analyzed
- 🌐 **Web Page Scraper** — Paste any article/wiki URL and chat about it
- ⬇️ **Export Chat** — Download your study session as Markdown
- 🔄 **New Chat** — Reset anytime

---

## Setup & Run Locally

### 1. Clone / Download the project
```bash
cd examhelp
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key
Get a **free** API key at [console.groq.com](https://console.groq.com)

**Option A** — Create a `.env` file:
```
GROQ_API_KEY=gsk_your_key_here
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
GROQ_API_KEY = "gsk_your_key_here"
```
4. Deploy — done! 🎉

---

## Project Structure
```
examhelp/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── .streamlit/
│   └── config.toml         # Theme config
└── utils/
    ├── groq_client.py      # Groq API + streaming
    ├── pdf_handler.py      # PDF text extraction
    ├── youtube_handler.py  # YouTube transcript fetcher
    └── web_handler.py      # Web page scraper
```

---

## Notes
- Model: `llama3-8b-8192` — fastest on Groq free tier (6000 tokens/min)
- Max context injected: ~12,000 chars per source (fits within model limits)
- The bot is hard-locked to study/academic topics only
