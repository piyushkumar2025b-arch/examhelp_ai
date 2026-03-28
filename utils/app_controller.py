import json
import time
import threading
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
try:
    import speech_recognition as sr
except ImportError:
    sr = None
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

from utils.groq_client import chat_with_groq

class AppController:
    _tts_engine = None
    _tts_lock = threading.Lock()

    @classmethod
    def get_tts_engine(cls):
        if pyttsx3 is None:
            return None
        with cls._tts_lock:
            if cls._tts_engine is None:
                try:
                    cls._tts_engine = pyttsx3.init()
                    cls._tts_engine.setProperty('rate', 160)
                except Exception as e:
                    print(f"Failed to config pyttsx3: {e}")
            return cls._tts_engine

    @staticmethod
    def speak(text: str):
        def _speak_thread():
            engine = AppController.get_tts_engine()
            if engine:
                with AppController._tts_lock:
                    engine.say(text)
                    engine.runAndWait()
        
        t = threading.Thread(target=_speak_thread, daemon=True)
        t.start()

    @staticmethod
    def voice_input():
        if sr is None: return "SpeechRecognition not installed."
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                text = recognizer.recognize_google(audio)
                return text
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError as e:
                return f"Could not request results; {e}"

    @staticmethod
    def get_context():
        import streamlit as st
        return st.session_state.get("context_text", "")

    @staticmethod
    def web_search(query: str, max_results=3) -> str:
        if DDGS is None:
            return "Web search unavailable (duckduckgo_search not installed)."
        try:
            results = DDGS().text(query, max_results=max_results)
            if not results: return "No web results found."
            search_context = []
            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                search_context.append(f"Title: {title}\nSummary: {body}")
            return "\n\n".join(search_context)
        except Exception as e:
            return f"Web search failed: {e}"

    @staticmethod
    def generate_flashcards(text: str, lang: str, api_key: str):
        prompt = [
            {"role": "system", "content": f"You are a master educator. Create 10 expert Q&A flashcards based strictly on the study material. "
                                          f"Return ONLY a strictly valid JSON object. Do NOT include any preamble. "
                                          f"Format: {{\"flashcards\": [{{'q': '...', 'a': '...', 'subject': '...', 'difficulty': 'easy/medium/hard'}}]}}. "
                                          f"All content MUST be in {lang}."},
            {"role": "user", "content": f"Study Material: {text[:12000]}"}
        ]
        return AppController._fetch_json(prompt, api_key)

    @staticmethod
    def generate_quiz(text: str, lang: str, api_key: str):
        prompt = [
            {"role": "system", "content": f"Create 5 challenging MCQs based strictly on the provided text. Return ONLY a strictly valid JSON object. No preamble. "
                                          f"Format: {{\"quiz\": [{{'q': '...', 'options': ['A', 'B', 'C', 'D'], 'correct': 'Correct Option Text', 'explanation': 'Brief reason'}}]}}. All content MUST be in {lang}."},
            {"role": "user", "content": f"Context Material: {text[:12000]}"}
        ]
        return AppController._fetch_json(prompt, api_key)

    @staticmethod
    def _fetch_json(prompt: list, api_key: str):
        from utils import key_manager
        success = False
        res_data = None
        for _ in range(key_manager.MAX_RETRIES):
            try:
                res_raw = chat_with_groq(prompt, json_mode=True, override_key=api_key)
                res_content = res_raw.strip()
                if not res_content.startswith("{"):
                    idx = res_content.find("{")
                    if idx != -1: res_content = res_content[idx:]
                data = json.loads(res_content)
                res_data = data
                success = True
                break
            except Exception:
                time.sleep(1)
        if success:
            return list(res_data.values())[0] if res_data else None
        return None
