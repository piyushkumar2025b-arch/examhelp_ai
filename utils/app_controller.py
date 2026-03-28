import json
import time
import threading
import re

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
try:
    import speech_recognition as sr
except ImportError:
    sr = None
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None
try:
    from sympy import sympify
except ImportError:
    sympify = None

from utils.ai_engine import generate as ai_generate


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
                except Exception:
                    pass
            return cls._tts_engine

    @staticmethod
    def speak(text: str):
        def _speak():
            engine = AppController.get_tts_engine()
            if engine:
                with AppController._tts_lock:
                    engine.say(text)
                    engine.runAndWait()
        threading.Thread(target=_speak, daemon=True).start()

    @staticmethod
    def voice_input():
        if sr is None:
            return "SpeechRecognition not installed."
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                return recognizer.recognize_google(audio)
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
            return "Web search unavailable."
        try:
            results = DDGS().text(query, max_results=max_results)
            if not results:
                return "No results found."
            return "\n\n".join(
                f"Title: {r.get('title','')}\nSummary: {r.get('body','')}"
                for r in results
            )
        except Exception as e:
            return f"Web search failed: {e}"

    @staticmethod
    def generate_flashcards(text: str, lang: str, api_key: str):
        prompt = [
            {"role": "system", "content": (
                f"You are a master educator. Create 10 expert Q&A flashcards from the study material. "
                f"Return ONLY strictly valid JSON. No preamble. "
                f'Format: {{"flashcards": [{{"q": "...", "a": "...", "subject": "...", "difficulty": "easy/medium/hard"}}]}}. '
                f"All content MUST be in {lang}."
            )},
            {"role": "user", "content": f"Study Material: {text[:12000]}"}
        ]
        return AppController._fetch_json(prompt, api_key)

    @staticmethod
    def generate_quiz(text: str, lang: str, api_key: str):
        prompt = [
            {"role": "system", "content": (
                f"Create 5 challenging MCQs from the provided text. Return ONLY strict JSON. No preamble. "
                f'Format: {{"quiz": [{{"q": "...", "options": ["A","B","C","D"], "correct": "Correct Option Text", "explanation": "Brief reason"}}]}}. '
                f"All content MUST be in {lang}."
            )},
            {"role": "user", "content": f"Context: {text[:12000]}"}
        ]
        return AppController._fetch_json(prompt, api_key)

    @staticmethod
    def _fetch_json(prompt: list, api_key: str):
        from utils import key_manager
        # Only retry 3 times for JSON parse failures.
        # chat_with_groq already handles key rotation internally.
        for _ in range(3):
            try:
                res_raw = ai_generate(messages=prompt, json_mode=True).strip()
                if not res_raw.startswith("{"):
                    idx = res_raw.find("{")
                    if idx != -1:
                        res_raw = res_raw[idx:]
                data = json.loads(res_raw)
                return list(data.values())[0] if data else None
            except json.JSONDecodeError:
                time.sleep(1)
                continue
            except Exception:
                return None
        return None

    @staticmethod
    def evaluate_expression(expr: str):
        if sympify is None:
            return "Error (sympy not installed)"
        if not expr.strip():
            return ""
        safe_expr = (expr
                     .replace('×', '*').replace('÷', '/').replace('^', '**')
                     .replace('−', '-').replace('π', 'pi')
                     .replace('√(', 'sqrt(').replace('x²', '**2')
                     .replace('log(', 'log10(').replace('ln(', 'log(')
                     .replace('x³', '**3').replace('|x|', 'Abs(')
                     .replace('| (OR)', '|').replace('& (AND)', '&')
                     .replace('~ (NOT)', '~').replace('^ (XOR)', '^')
                     # Physics Constants
                     .replace('c_LIGHT', '299792458').replace('G_GRAV', '6.67430e-11')
                     .replace('h_PLANCK', '6.62607015e-34').replace('hbar', '1.054571817e-34')
                     .replace('m_e', '9.10938370e-31').replace('m_p', '1.67262192e-27')
                     .replace('m_n', '1.67492750e-27').replace('e_CHARGE', '1.602176634e-19')
                     .replace('mu_0', '1.256637062e-6').replace('eps_0', '8.8541878128e-12')
                     .replace('k_BOLTZ', '1.380649e-23')
                     # Astro Constants
                     .replace('M_SUN', '1.98847e30').replace('R_SUN', '6.957e8')
                     .replace('M_EARTH', '5.9722e24').replace('R_EARTH', '6.371e6')
                     .replace('g_EARTH', '9.80665').replace('AU_DIST', '1.495978707e11')
                     # Chemistry Constants
                     .replace('N_AVOGADRO', '6.02214076e23').replace('R_GAS', '8.314462618')
                     .replace('F_FARADAY', '96485.33212').replace('Rydberg', '10973731.568160')
                     .replace('Bohr_rad', '5.291772109e-11').replace('alpha_fs', '0.007297352569')
                     .replace('atm_press', '101325').replace('eV_J', '1.602176634e-19')
                     .replace('u_AMU', '1.6605390666e-27').replace('sigma_SB', '5.670374419e-8')
                     .replace('wien_b', '2.897771955e-3').replace('flux_phi0', '2.067833848e-15')
                     .replace('G_0_cond', '7.748091729e-5').replace('K_J_jos', '483597.8484e9')
                     .replace('R_K_von', '25812.80745').replace('mu_Bohr', '9.274010078e-24')
                     .replace('mu_N', '5.050783746e-27'))
        try:
            result = sympify(safe_expr).evalf()
            res_float = float(result)
            if res_float == int(res_float):
                return str(int(res_float))
            return f"{res_float:.8f}".rstrip('0').rstrip('.')
        except Exception:
            return "Error"

    @staticmethod
    def generate_study_schedule(text: str, num_days: int, lang: str, api_key: str):
        import datetime as dt
        prompt = [
            {"role": "system", "content": (
                f"You are a study coach. Extract {num_days * 2} discrete study tasks from the material. "
                f"Return ONLY strict JSON: "
                f'{{"tasks": [{{"task": "...", "topic": "...", "estimated_minutes": 30, "priority": "high", "deadline_offset_days": 1}}]}}. '
                f"Space deadline_offset_days from 1 to {num_days}. Priority: high/medium/low. Language: {lang}."
            )},
            {"role": "user", "content": f"Study Material: {text[:12000]}"}
        ]
        raw = AppController._fetch_json(prompt, api_key)
        if not raw:
            return []
        today = dt.date.today()
        result = []
        for item in raw:
            if isinstance(item, str):
                result.append({"task": item, "topic": "", "estimated_minutes": 30,
                                "priority": "medium",
                                "deadline": (today + dt.timedelta(days=1)).isoformat(),
                                "done": False})
            elif isinstance(item, dict):
                offset = int(item.get("deadline_offset_days", 1))
                result.append({
                    "task": item.get("task", ""),
                    "topic": item.get("topic", ""),
                    "estimated_minutes": int(item.get("estimated_minutes", 30)),
                    "priority": item.get("priority", "medium"),
                    "deadline": (today + dt.timedelta(days=offset)).isoformat(),
                    "done": False
                })
        return result

    @staticmethod
    def estimate_task_time(task: str, api_key: str) -> int:
        prompt = [
            {"role": "system", "content": "Estimate study time in minutes for the following task. Reply with ONLY a single integer."},
            {"role": "user", "content": task}
        ]
        try:
            result = ai_generate(messages=prompt).strip()
            m = re.search(r'\d+', result)
            return int(m.group()) if m else 30
        except Exception:
            return 30
