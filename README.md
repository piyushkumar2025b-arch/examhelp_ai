# 🚀 ExamHelp AI v4.0 — The Ultimate Elite Academic Intelligence Platform

ExamHelp AI is a production-grade, multi-modal artificial intelligence ecosystem explicitly engineered for high-performance academic assistance, technical problem-solving, and professional-grade research. 

This platform transcends traditional study chatbots by providing a unified, multi-key rotation architecture that powers a specialized suite of **"Elite Expert Engines"** — meticulously crafted AI personas designed for clinical precision in Law, Medicine, Engineering, and more.

---

## 💎 The Elite Expert Engine Suite
ExamHelp v4.0 introduces nine highly-specialized, autonomous expert modules accessible directly from the sidebar. Each engine uses its own centralized reasoning logic and temperature-tuned persona:

### 1. ⚡ Circuit Solver Pro
*   **Domain**: Electrical Engineering & Physics.
*   **Logic**: Vision-to-Topography Mapping.
*   **Capabilities**: Upload a circuit diagram; the AI identifies nodes, resistors, and sources to provide a step-by-step KVL/KCL solution with symbolic derivation.

### 2. 🎯 Advanced Math Solver
*   **Domain**: Higher Mathematics (Calculus, Linear Algebra, Real Analysis).
*   **Logic**: Hybrid Vision-to-LaTeX symbolic resolution.
*   **Capabilities**: Supports handwritten image OCR and typed expressions. Provides verified step-by-step proofs and numerical results in professional LaTeX notation.

### 3. ⚖️ Legal Analyser & Case Assistant
*   **Domain**: Law & Jurisprudence (Common Law, IPC, Federal).
*   **Persona**: Senior Counsel (Legal Expert).
*   **Capabilities**: Analyzes material facts, identifies legal issues, maps applicable statutes/case law, and generates hypothetical legal conclusions with judicial depth.

### 4. 🔬 Research Scholar & Paper Critiquer
*   **Domain**: Academic Research & Peer-Review.
*   **Capabilities**: Performs rigorous scientific peer-review critiques, maps literature reviews across specific focus areas, and identifies critical research gaps in existing abstracts.

### 5. 🏗️ Technical Project Architect
*   **Domain**: Software Engineering & CS Projects.
*   **Capabilities**: Generates full-file project blueprints, suggests optimal production-ready tech stacks, and creates system architecture diagrams (Mermaid.js).

### 6. 🩺 Medical Research Guide
*   **Domain**: Clinical Reasoning & Medical Education.
*   **Capabilities**: Analyzes symptomatic fact patterns for educational research, explains complex pathophysiology, and provides pharmacokinetic interaction profiles.

### 7. 💹 Elite Stocks Dashboard
*   **Domain**: Financial Analysis & Economics.
*   **Capabilities**: Real-time market sentiment analysis, technical indicator critiques, and sector-based trend forecasting for global and Indian markets.

### 8. 📚 AI Multi-Lang Dictionary & Lexicon
*   **Domain**: Linguistics & Cultural Etymology.
*   **Capabilities**: High-precision discovery of contextual meanings, difficulty-ranked synonyms/antonyms, usage variations, and cultural idiomatic depth.

### 9. 🎨 Professional HTML Page Builder
*   **Domain**: Full-Stack Frontend Engineering.
*   **Capabilities**: Generates stunning, single-file HTML/CSS pages using Tailwind CSS. Features glassmorphism designs, smooth animations, and interactive components by default.

---

## 📚 Complete Feature Checklist
The ExamHelp ecosystem provides a comprehensive set of multi-modal tools for every stage of your study journey:

*   📑 **Smart PDF Analyst**: Upload multiple PDFs and ask questions about your textbooks/notes.
*   ▶️ **YouTube Transcripts**: Paste any video link to get instant transcripts, summaries, and key takeaways.
*   🌐 **Web Page Scraper**: Scrape any research article or Wiki page and chat with the live content.
*   🃏 **Flashcard Generator**: Auto-generate Q&A flashcards from any existing study material.
*   📝 **Interactive Quiz Mode**: Test your knowledge with AI-tracked quizzes and step-by-step explanations.
*   📊 **Visual Mind Maps**: Create complex concept maps using Mermaid.js diagrams directly from text.
*   📅 **Dynamic Study Planner**: Generate day-by-day revision timetables based on your upcoming exams.
*   🎭 **30+ Logic Personas**: Switch between Einstein, Feynman, and Socrates for different learning perspectives.
*   🎙️ **Whisper Voice Chat**: Ask questions via high-precision voice recording and get real-time audio replies.
*   📸 **Image OCR Scanner**: Extract and analyze text from photos of handwritten notes or whiteboards.

---

## 🧠 System Architecture & Core Innovations

ExamHelp v4.0 is built on a "Logic-First" architecture that ensures reliability, performance, and scalability:

### 🔄 Multi-Key Gemini Rotation Pool
*   **Problem**: Free-tier Gemini keys have strict rate limits (RPM/RPD).
*   **Solution**: A high-performance failover pool (`utils/ai_engine.py`) that rotates through 9 unique API keys.
*   **Smart Cooldown**: If a key hits a rate limit, the engine automatically places it in a 65-second cooldown and switches to the next available key without interrupting the user session.

### 📖 Centralized Prompt Registry (`utils/prompts.py`)
*   **Personas**: All AI identities (Tutor, Architect, Senior Counsel, etc.) are defined in a single source of truth.
*   **Tuning**: Every individual task has pre-configured temperature settings (e.g., 0.1 for Math/Law, 0.8 for Creative Writing) and max token limits to optimize output quality and cost-efficiency.

### 💎 UX: Glassmorphism Design System
*   **Premium Aesthetic**: Standardized headers, action buttons, and result containers using modern CSS gradients and frosted-glass effects.
*   **Responsive Layout**: Fully optimized for Desktop, Tablet, and Mobile viewing within the Streamlit framework.

---

## 🛠️ Security & Configuration
ExamHelp AI is engineered for security. Direct API keys are **never** committed to the repository.

### 1. Local Secrets (.streamlit/secrets.toml)
Create this file in the root directory. It is git-ignored by default:
```toml
# .streamlit/secrets.toml
GEMINI_API_KEY_1 = "your-key-here"
GEMINI_API_KEY_2 = "your-key-here"
# ... up to GEMINI_API_KEY_9
```

### 2. Production Secrets (Streamlit Cloud)
In your Streamlit Cloud dashboard, navigate to **Settings → Secrets** and paste your keys in the following format:
```toml
GEMINI_API_KEY_1 = "AIza..."
...
```

---

## 🚦 Implementation & Deployment Guide

### Installation
1.  Clone the repository and enter the directory.
2.  Install all dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure your `secrets.toml` file.

### Execution
Launch the production server:
```bash
streamlit run app.py
```

### Deployment Strategy
ExamHelp v4.0 is optimized for **Streamlit Cloud** and **Render**:
*   **Lightweight Footprint**: Minimized dependency tree for fast builds.
*   **Lazy Loading**: Most engines and libraries (e.g., SymPy, Matplotlib) are loaded lazily to ensure a sub-5-second initial boot time.

---

## 📂 File Structure Overview
*   `app.py`: The central hub and navigation controller.
*   `new_features.py`: The primary UI rendering module for the Elite expert suite.
*   `utils/ai_engine.py`: The core multi-key rotation and standardized LLM interface.
*   `utils/prompts.py`: The central registry of all tasks, personas, and specialized configurations.
*   `utils/secret_manager.py`: Secure, lazy-loading interface for API credentials.
*   `legal_engine.py`: Specialized reasoning module for Case Law and Compliance.
*   `medical_engine.py`: Clinic-grade reasoning for medical education.
*   `math_solver_engine.py`: Symbolic and numerical mathematics solver.
*   `circuit_solver_engine.py`: Vision-based topological electrical reasoning.
*   `project_blueprint_engine.py`: Technical architect for software engineering projects.
*   `stocks_engine.py`: Financial intelligence and technical indicators.
*   `dictionary_engine.py`: Advanced linguistic and cultural lookup logic.

---

## 🏁 FAQ & Troubleshooting
*   **"No Gemini keys available"**: Ensure your `secrets.toml` variables are prefixed with `AIzaSy`. Check the "API Pool Status" button in the sidebar.
*   **"Slow initial solve"**: Specialized engines like Circuit/Math pre-load symbolic libraries on the first run.
*   **SSL Errors on Windows**: The `ai_engine.py` includes a self-correcting SSL context generator for systems with broken certificate chains.

---
*Built by **Antigravity** with Gemini-Pro and Streamlit. Designed for the professionals and students of tomorrow.*
