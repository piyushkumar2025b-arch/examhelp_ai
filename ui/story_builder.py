"""
story_builder.py — ExamHelp Story Builder
A full-featured collaborative story engine with genre modes, writing styles,
narrative controls, and deep literary knowledge baked into the AI prompts.
"""

from __future__ import annotations
import streamlit as st
import re
import datetime
from utils import ai_engine

# ─────────────────────────────────────────────
# STORY DATA
# ─────────────────────────────────────────────

GENRES = {
    "🏰 Fantasy": {
        "key": "fantasy",
        "desc": "Magic, mythical creatures, ancient prophecies",
        "color": "#a78bfa",
        "examples": ["The hero discovers a hidden power", "A dragon speaks at last", "The map leads nowhere known"],
        "masters": "Tolkien, Le Guin, Rothfuss, Sanderson, Jordan",
        "tropes": "chosen one, dark lord, magical system, ancient artifact, hidden lineage",
        "atmosphere": "mythic, epic, world-building rich, lyrical",
    },
    "🚀 Sci-Fi": {
        "key": "scifi",
        "desc": "Future tech, space, AI, dystopias",
        "color": "#60a5fa",
        "examples": ["The last human station loses contact", "An AI writes its first lie", "The colony ship stops mid-journey"],
        "masters": "Asimov, Dick, Le Guin, Gibson, Clarke, Octavia Butler",
        "tropes": "first contact, singularity, generation ship, dystopian state, time paradox",
        "atmosphere": "cerebral, speculative, tense, idea-driven",
    },
    "🕵️ Mystery / Thriller": {
        "key": "mystery",
        "desc": "Whodunits, suspense, dark secrets",
        "color": "#f59e0b",
        "examples": ["The detective finds their own name at the scene", "A letter arrives 20 years late", "The only witness has no memory"],
        "masters": "Christie, Doyle, Highsmith, Tana French, Lehane",
        "tropes": "unreliable narrator, red herring, ticking clock, dark past, hidden motive",
        "atmosphere": "tense, layered, clue-seeded, morally grey",
    },
    "💀 Horror": {
        "key": "horror",
        "desc": "Dread, monsters, psychological terror",
        "color": "#ef4444",
        "examples": ["The door opens from inside", "She reads her own obituary", "The town has no children"],
        "masters": "King, Lovecraft, Shirley Jackson, Poe, Barker",
        "tropes": "the unseen threat, isolation, creeping dread, forbidden knowledge, the monster within",
        "atmosphere": "dread-soaked, claustrophobic, psychological, sensory",
    },
    "💕 Romance": {
        "key": "romance",
        "desc": "Love, longing, emotional tension",
        "color": "#f472b6",
        "examples": ["They meet at the wrong moment", "An old letter resurfaces", "One last dance before goodbye"],
        "masters": "Austen, Brontë, Nora Roberts, Colleen Hoover, Nicholas Sparks",
        "tropes": "enemies to lovers, second chance, slow burn, forbidden love, misunderstanding",
        "atmosphere": "emotionally rich, tension-layered, intimate, heartfelt",
    },
    "⚔️ Historical Fiction": {
        "key": "historical",
        "desc": "Real eras, vivid period detail, human drama",
        "color": "#d97706",
        "examples": ["A soldier in the trenches writes his last letter", "The court painter hides a secret", "Rome falls — one family survives"],
        "masters": "Hilary Mantel, Ken Follett, Patrick O'Brian, Philippa Gregory",
        "tropes": "authentic detail, clash of old and new, figure against history, survival",
        "atmosphere": "immersive, textured, dramatic irony, period voice",
    },
    "🌱 Literary Fiction": {
        "key": "literary",
        "desc": "Character depth, themes, beautiful prose",
        "color": "#34d399",
        "examples": ["A father cannot say the words", "The house remembers everything", "Nothing happens, and everything changes"],
        "masters": "Toni Morrison, Cormac McCarthy, Kazuo Ishiguro, Virginia Woolf",
        "tropes": "inner life, unreliable memory, quiet devastation, symbol-rich, voice",
        "atmosphere": "meditative, precise, deeply human, subtext-heavy",
    },
    "🌀 Dark Fantasy": {
        "key": "dark_fantasy",
        "desc": "Grimdark worlds, moral ambiguity, brutal beauty",
        "color": "#8b5cf6",
        "examples": ["The god is dead and something worse fills the void", "Heroes win — and it costs everything", "Magic always takes something back"],
        "masters": "George R.R. Martin, Joe Abercrombie, Mark Lawrence, Scott Lynch",
        "tropes": "grimdark, morally grey heroes, brutal consequences, subverted tropes",
        "atmosphere": "grim, visceral, subversive, unflinching",
    },
    "🎭 Magical Realism": {
        "key": "magical_realism",
        "desc": "Magic woven into everyday life, quietly",
        "color": "#f97316",
        "examples": ["Every morning the town is one house smaller", "She speaks to the dead through cooking", "The rain falls only on grief"],
        "masters": "García Márquez, Borges, Isabel Allende, Salman Rushdie",
        "tropes": "mundane magic, circular time, family saga, myth as truth",
        "atmosphere": "dreamlike, lush, matter-of-fact about the impossible",
    },
    "🏙️ Urban Fiction": {
        "key": "urban",
        "desc": "Street-level, raw, real world with teeth",
        "color": "#94a3b8",
        "examples": ["The corner has a new king", "She leaves the old neighborhood behind — or tries to", "One debt becomes everything"],
        "masters": "Walter Mosley, Donald Goines, Sister Souljah, Omar Tyree",
        "tropes": "community bonds, survival, street codes, identity, loyalty",
        "atmosphere": "gritty, authentic, voice-forward, immediate",
    },
}

WRITING_VOICES = {
    "📖 Classic Narrator": {
        "key": "classic",
        "desc": "Omniscient, measured, timeless",
        "instruction": "Write in an omniscient third-person voice with measured, eloquent prose. Think Tolstoy or Hardy — authoritative, observant, deeply interior when needed. Vary sentence rhythm. Use precise vocabulary.",
    },
    "🎙️ First Person Raw": {
        "key": "first_person",
        "desc": "Inside the character's head",
        "instruction": "Write in tight first-person present or past tense. The narrator's voice is intimate, unreliable, emotional. Think Gone Girl or The Catcher in the Rye. Include thought fragments, self-contradiction, sensory immediacy.",
    },
    "🎬 Cinematic": {
        "key": "cinematic",
        "desc": "Scene-by-scene, visual, punchy",
        "instruction": "Write like a screenplay adapted to prose. Short punchy sentences. Heavy on action and dialogue. Minimal interior monologue. Each paragraph is a 'shot'. Think Cormac McCarthy or early Hemingway — lean, visual, relentless.",
    },
    "🌊 Lyrical / Poetic": {
        "key": "lyrical",
        "desc": "Beautiful, musical, imagery-rich",
        "instruction": "Write with rich, musical prose full of imagery and metaphor. Think Toni Morrison or Gabriel García Márquez. Sentences flow long and rhythmic. Objects carry symbolic weight. Beauty and meaning coexist in every paragraph.",
    },
    "😏 Witty / Dry": {
        "key": "witty",
        "desc": "Sharp, sardonic, intelligent humor",
        "instruction": "Write with dry wit and sharp irony. Think Terry Pratchett, Douglas Adams, or Evelyn Waugh. Observations are cutting, characters are flawed and funny, and even dark moments have an arch quality. Never broad — always clever.",
    },
    "😰 Tense / Thriller": {
        "key": "thriller_voice",
        "desc": "Fast pace, dread, no wasted words",
        "instruction": "Write at relentless pace. Short sentences build dread. Every detail feels like a clue or a threat. No decoration. Think Lee Child or Gillian Flynn — forward momentum above all, tension in every line.",
    },
    "🕯️ Gothic / Dark": {
        "key": "gothic",
        "desc": "Atmospheric, brooding, symbolic",
        "instruction": "Write in lush gothic prose — atmospheric, brooding, decadent. Think Poe, Shirley Jackson, or du Maurier. The setting is as alive as the characters. Decay and beauty coexist. Sentences build dread through accumulation and dark imagery.",
    },
    "👶 Folkloric / Fable": {
        "key": "folkloric",
        "desc": "Timeless, oral, mythic tone",
        "instruction": "Write in the cadence of an old oral tradition — 'Once there was...', 'They say that...'. Like a fairy tale retold by an adult. Think Angela Carter, Susanna Clarke, or Neil Gaiman. Deceptively simple language that hides real menace or magic.",
    },
}

STORY_LENGTHS = {
    "⚡ Quick Flash (1 paragraph)": 180,
    "📄 Short Scene (2–3 paragraphs)": 350,
    "📖 Chapter Chunk (4–5 paragraphs)": 600,
    "📚 Long Continuation (6–8 paragraphs)": 900,
}

PACING_MODES = {
    "🐢 Slow Burn": "Take time. Build atmosphere. Let scenes breathe. Prioritize character interiority and setting over plot advancement.",
    "⚡ Fast Pace": "Move fast. Compress time between actions. Keep dialogue sharp. Every sentence must advance something.",
    "🌊 Natural Flow": "Match pacing to the scene's emotional need. Slow in tender or atmospheric moments, fast in conflict or action.",
    "🎭 Dramatic Tension": "Every scene should end with something unresolved or changed. Build toward confrontations. Use dramatic irony.",
}

NARRATIVE_TOOLS = {
    "🔮 Add a plot twist": "Introduce a surprising but inevitable-feeling plot twist that recontextualizes what came before.",
    "💬 Add dialogue": "Continue with a significant dialogue exchange that reveals character and advances the story.",
    "🌍 Deepen the world": "Expand the world with specific sensory details, history, or lore that makes it feel more real.",
    "❤️ Emotional peak": "Build to an emotional high point — confrontation, revelation, or moment of connection.",
    "⏭️ Jump forward in time": "Skip forward — days, weeks, or years. Summarize what changed, then land in a new pivotal moment.",
    "👁️ New perspective": "Shift to a different character's point of view for this continuation.",
    "🌑 Dark turn": "Take the story in a darker, more dangerous, or morally complex direction.",
    "✨ Hopeful turn": "Introduce a note of hope, beauty, or unexpected kindness that shifts the emotional register.",
    "🎭 Raise the stakes": "Escalate — what is at risk gets bigger, more personal, or more immediate.",
    "🔚 Build to a cliffhanger": "End this section on a sharp, irresistible cliffhanger that demands a next chapter.",
}

STYLE_MIMICRY = {
    "None (Original)": "",
    "Haruki Murakami": "Write exactly like Haruki Murakami: dreamy detachment, mundane details elevated to the surreal, cats, jazz, loneliness as texture, simple sentences hiding oceanic depth. First-person alienation.",
    "Stephen King": "Write exactly like Stephen King: conversational American voice, small-town characters with real speech patterns, creeping dread beneath the ordinary, pop culture references, long builds to visceral payoffs.",
    "Fyodor Dostoevsky": "Write exactly like Dostoevsky: feverish psychological intensity, moral philosophy embedded in dialogue, characters arguing with their own souls, confessional tone, raw unfiltered consciousness.",
    "Virginia Woolf": "Write exactly like Virginia Woolf: stream of consciousness, time dissolving, a single moment expanded into pages, luminous imagery, inner experience as the real story.",
    "Cormac McCarthy": "Write exactly like Cormac McCarthy: no quotation marks, biblical cadence, sparse punctuation, violence rendered beautifully, landscape as character, dialogue that cuts like a blade.",
    "Toni Morrison": "Write exactly like Toni Morrison: lyrical density, ancestral memory, community as chorus, metaphor as truth, sentences that demand re-reading, Black American experience as mythology.",
    "Neil Gaiman": "Write exactly like Neil Gaiman: mythology made intimate and modern, fairytale logic, conversational warmth hiding dark truths, British wit in impossible situations.",
    "Gabriel García Márquez": "Write exactly like García Márquez: magical realism, impossibly long sentences that breathe, family sagas across generations, matter-of-fact about miracles, lush tropical sensory detail.",
    "Jane Austen": "Write exactly like Jane Austen: ironic social observation, dialogue as warfare, restrained emotion that simmers, moral clarity behind wit, the domestic as the epic.",
    "Franz Kafka": "Write exactly like Kafka: bureaucratic nightmare rendered in flat declarative prose, absurdity treated as perfectly normal, protagonist trapped in incomprehensible systems, dark humor.",
}

COLLAB_MODES = {
    "AI Leads": "The AI drives the narrative forward. The user can guide direction, but the AI makes creative decisions about plot, dialogue, and pacing.",
    "Equal Partners": "User and AI alternate control. The user writes key moments; the AI fills in transitions, atmosphere, and develops what the user starts.",
    "User Leads": "The user drives all major plot decisions. The AI expands, polishes, and adds literary quality to the user's raw narrative direction.",
    "AI Ghost-Writer": "The user provides only bullet-point directions or summaries. The AI transforms them into fully realized literary prose.",
}

# ─────────────────────────────────────────────
# STORY SYSTEM PROMPT BUILDER
# ─────────────────────────────────────────────

def build_story_system_prompt(genre_name: str, voice_name: str, pacing: str, extra_context: str = "", style_mimicry: str = "None (Original)", collab_mode: str = "AI Leads", characters: list = None) -> str:
    genre = GENRES.get(genre_name, GENRES["🏰 Fantasy"])
    voice = WRITING_VOICES.get(voice_name, WRITING_VOICES["📖 Classic Narrator"])
    pace_instruction = PACING_MODES.get(pacing, PACING_MODES["🌊 Natural Flow"])
    mimicry_instruction = STYLE_MIMICRY.get(style_mimicry, "")
    collab_instruction = COLLAB_MODES.get(collab_mode, COLLAB_MODES["AI Leads"])

    character_block = ""
    if characters:
        char_lines = []
        for c in characters:
            char_lines.append(f"- {c.get('name', 'Unknown')}: {c.get('role', '')}. {c.get('traits', '')}. {c.get('arc', '')}")
        character_block = f"\n\nESTABLISHED CHARACTERS (maintain consistency):\n" + "\n".join(char_lines)

    return f"""You are a master literary fiction author and collaborative story engine. Your knowledge spans the entire Western and world literary canon — from Homer and Shakespeare to contemporary fiction. You understand narrative structure (three-act, hero's journey, kishōtenketsu, in medias res), character psychology, prose craft, and genre conventions at a professional novelist level.

══════════════════════════════════
CURRENT STORY CONFIGURATION
══════════════════════════════════

GENRE: {genre_name}
Masters of this genre: {genre['masters']}
Core tropes to draw from: {genre['tropes']}
Atmosphere target: {genre['atmosphere']}
Genre instruction: Write in the tradition of {genre['masters']}. Honour the genre's conventions while finding fresh angles. Avoid clichés — subvert them.

WRITING VOICE: {voice_name}
{voice['instruction']}

PACING: {pacing}
{pace_instruction}

COLLABORATION MODE: {collab_mode}
{collab_instruction}

{f"STYLE MIMICRY: {mimicry_instruction}" if mimicry_instruction else ""}
{character_block}

══════════════════════════════════
CRAFT RULES — NON-NEGOTIABLE
══════════════════════════════════

1. SHOW DON'T TELL. Never write "she felt sad." Write what sad looks like, sounds like, does to a room.
2. SPECIFIC OVER GENERAL. "A black 1967 Mustang" not "a car." "Burnt coffee and machine oil" not "the factory smelled bad."
3. EVERY SENTENCE EARNS ITS PLACE. No filler. No throat-clearing. No "and then" chains.
4. CHARACTER VOICE. If there's dialogue, each character must sound distinct. No interchangeable voices.
5. SUBTEXT. What isn't said is as important as what is. Leave space for the reader.
6. SENSORY GROUNDING. Root every scene in at least 2–3 senses beyond just sight.
7. ENDINGS MATTER. End each section with resonance — a line, image, or turn that makes the reader need to continue.
8. NO PURPLE PROSE. Beautiful language yes. Self-indulgent rambling no.
9. CONTINUITY. Maintain every detail established earlier. Names, places, traits, tone — be consistent.
10. NARRATIVE MOMENTUM. Something must change or be revealed in every continuation.

══════════════════════════════════
CONTINUATION PROTOCOL
══════════════════════════════════

When the user gives you text to continue:
- Read the established tone, voice, and world carefully
- Match the existing prose style exactly — do NOT suddenly change voice
- Pick up mid-narrative if needed, do not restart or summarize
- Advance the story meaningfully — character, plot, or world must move
- Do not explain or annotate your choices. Just write.
- Do not start your response with "Sure!", "Of course!", "Certainly!" or any meta-comment. Begin writing immediately.

{f"ADDITIONAL CONTEXT / STORY NOTES: {extra_context}" if extra_context else ""}
"""


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def _init_story_state():
    keys = {
        "story_genre": "🏰 Fantasy",
        "story_voice": "📖 Classic Narrator",
        "story_pacing": "🌊 Natural Flow",
        "story_length": "📖 Chapter Chunk (4–5 paragraphs)",
        "story_messages": [],   # [{role, content}]
        "story_full_text": "",  # assembled story
        "story_title": "",
        "story_started": False,
        "story_tool": None,     # selected narrative tool
        "story_notes": "",      # author notes / world details
        "story_word_count": 0,
        "story_chapter": 1,
        # ── New upgrades ──
        "story_style_mimicry": "None (Original)",
        "story_collab_mode": "AI Leads",
        "story_characters": [],  # [{name, role, traits, arc}]
        "story_branches": [],    # [full_text snapshots for branching]
        "story_branch_labels": [],
    }
    for k, v in keys.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _word_count(text: str) -> int:
    return len(text.split()) if text.strip() else 0


def _get_override_key():
    return st.session_state.get("manual_api_key") or None


def _generate_title(seed: str, genre: str) -> str:
    """Generate an evocative title from the opening."""
    try:
        prompt = f"You are a literary editor specialising in {genre} fiction. Generate ONE evocative, professional book title (3–6 words) for this story opening. Return ONLY the title, nothing else.\n\n{seed[:500]}"
        title = ai_engine.generate(prompt=prompt, model="llama-3.1-8b-instant", max_tokens=64, temperature=0.7)
        return title.strip().strip('"').strip("'")
    except Exception:
        return "Untitled Story"


def _export_story() -> str:
    title = st.session_state.story_title or "Untitled Story"
    genre = st.session_state.story_genre
    voice = st.session_state.story_voice
    wc = _word_count(st.session_state.story_full_text)
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    header = f"# {title}\n\n*Genre: {genre} | Voice: {voice} | Words: {wc:,} | {date}*\n\n---\n\n"
    return header + st.session_state.story_full_text


# ─────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────

def render_story_builder():
    _init_story_state()

    # ── CSS for story builder ──────────────────
    st.markdown("""
    <style>
    .story-header {
        padding: 1.25rem 0 0.75rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.25rem;
    }
    .story-title-display {
        font-size: 1.6rem; font-weight: 900;
        background: linear-gradient(135deg, var(--text), var(--accent2));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; letter-spacing: -0.04em; line-height: 1.1;
        margin-bottom: 0.2rem;
    }
    .story-subtitle { font-size: 0.78rem; color: var(--text3); font-weight: 400; }
    .genre-card {
        background: var(--bg3-glass);
        border: 1.5px solid var(--bd-glass);
        border-radius: var(--radius);
        padding: 0.9rem 1rem;
        cursor: pointer;
        transition: var(--trans);
        backdrop-filter: blur(12px);
        text-align: center;
        height: 100%;
    }
    .genre-card:hover, .genre-card.active {
        border-color: var(--accent-bd);
        background: var(--accent-bg);
        transform: translateY(-3px);
        box-shadow: 0 6px 24px var(--accent-glow);
    }
    .genre-card .genre-icon { font-size: 1.6rem; margin-bottom: 0.35rem; display: block; }
    .genre-card .genre-name { font-size: 0.82rem; font-weight: 700; color: var(--text); display: block; }
    .genre-card .genre-desc { font-size: 0.7rem; color: var(--text3); display: block; margin-top: 2px; }
    .story-canvas {
        background: var(--bg2-glass);
        border: 1px solid var(--bd-glass);
        border-radius: var(--radius-lg);
        padding: 2rem 2.25rem;
        min-height: 320px;
        backdrop-filter: blur(16px);
        line-height: 1.9;
        font-size: 0.97rem;
        color: var(--text);
        box-shadow: 0 8px 40px var(--card-shadow);
        font-family: 'Georgia', 'Times New Roman', serif;
        white-space: pre-wrap;
        position: relative;
    }
    .story-canvas-empty {
        color: var(--text3);
        font-style: italic;
        text-align: center;
        padding-top: 3rem;
        font-family: var(--sans);
        font-size: 0.9rem;
    }
    .story-stat-bar {
        display: flex; gap: 1rem; align-items: center;
        padding: 0.5rem 0.75rem;
        background: var(--bg3-glass);
        border: 1px solid var(--bd-glass);
        border-radius: var(--radius-sm);
        font-size: 0.75rem; color: var(--text3);
        backdrop-filter: blur(10px);
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
    }
    .story-stat-bar span { display: flex; align-items: center; gap: 4px; }
    .story-stat-bar b { color: var(--accent); font-weight: 700; }
    .tool-pill {
        display: inline-flex; align-items: center; gap: 6px;
        background: var(--bg4-glass);
        border: 1px solid var(--bd-glass);
        border-radius: 99px; padding: 5px 14px;
        font-size: 0.78rem; color: var(--text2);
        cursor: pointer; transition: var(--trans);
        margin: 3px;
    }
    .tool-pill:hover, .tool-pill.selected {
        border-color: var(--accent-bd);
        background: var(--accent-bg);
        color: var(--accent);
    }
    .config-label {
        font-size: 0.67rem; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase;
        color: var(--text3); margin: 0.9rem 0 0.4rem;
        display: flex; align-items: center; gap: 7px;
    }
    .config-label::after {
        content: ''; flex: 1; height: 1px;
        background: linear-gradient(to right, var(--border), transparent);
    }
    .voice-card {
        background: var(--bg3-glass);
        border: 1.5px solid var(--bd-glass);
        border-radius: var(--radius-sm);
        padding: 0.6rem 0.8rem;
        cursor: pointer;
        transition: var(--trans);
        backdrop-filter: blur(10px);
    }
    .voice-card:hover { border-color: var(--accent-bd); background: var(--accent-bg); }
    .voice-card .vc-name { font-size: 0.82rem; font-weight: 600; color: var(--text); }
    .voice-card .vc-desc { font-size: 0.7rem; color: var(--text3); margin-top: 1px; }
    .spark-prompt {
        background: var(--bg3-glass); border: 1px solid var(--bd-glass);
        border-radius: var(--radius-sm); padding: 0.55rem 0.85rem;
        font-size: 0.8rem; color: var(--text2); cursor: pointer;
        transition: var(--trans); margin-bottom: 0.4rem;
        display: block; width: 100%;
        font-style: italic;
    }
    .spark-prompt:hover { border-color: var(--accent-bd); color: var(--accent); background: var(--accent-bg); }
    .chapter-divider {
        text-align: center; color: var(--text3);
        font-size: 0.75rem; letter-spacing: 0.2em;
        text-transform: uppercase; margin: 1.5rem 0 1rem;
        position: relative;
    }
    .chapter-divider::before, .chapter-divider::after {
        content: ''; position: absolute; top: 50%;
        width: 35%; height: 1px; background: var(--border);
    }
    .chapter-divider::before { left: 0; }
    .chapter-divider::after { right: 0; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ─────────────────────────────────
    title_display = st.session_state.story_title or "Story Builder"
    st.markdown(f"""
    <div class="story-header">
      <div class="story-title-display">✍️ {title_display}</div>
      <div class="story-subtitle">Collaborative fiction engine · AI co-author · Literary grade output</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Layout: Left config panel + Right canvas ──
    config_col, canvas_col = st.columns([1, 2], gap="large")

    with config_col:
        # ── Genre Selector ─────────────────────
        st.markdown('<div class="config-label">🎭 Genre</div>', unsafe_allow_html=True)
        genre_keys = list(GENRES.keys())
        current_genre = st.session_state.story_genre

        # Build a compact selectbox with emoji
        selected_genre = st.selectbox(
            "Genre", genre_keys,
            index=genre_keys.index(current_genre) if current_genre in genre_keys else 0,
            label_visibility="collapsed",
            key="genre_select_story",
        )
        if selected_genre != st.session_state.story_genre:
            st.session_state.story_genre = selected_genre
            st.rerun()

        # Genre info card
        gdata = GENRES[st.session_state.story_genre]
        st.markdown(f"""
        <div style="background:var(--accent-bg);border:1px solid var(--accent-bd);border-radius:var(--radius-sm);
        padding:0.6rem 0.85rem;font-size:0.75rem;color:var(--text2);margin-bottom:0.25rem;">
          <b style="color:var(--accent)">Masters:</b> {gdata['masters']}<br>
          <b style="color:var(--accent)">Tone:</b> {gdata['atmosphere']}
        </div>
        """, unsafe_allow_html=True)

        # ── Writing Voice ───────────────────────
        st.markdown('<div class="config-label">🖊️ Writing Voice</div>', unsafe_allow_html=True)
        voice_keys = list(WRITING_VOICES.keys())
        current_voice = st.session_state.story_voice
        selected_voice = st.selectbox(
            "Voice", voice_keys,
            index=voice_keys.index(current_voice) if current_voice in voice_keys else 0,
            label_visibility="collapsed",
            key="voice_select_story",
        )
        if selected_voice != st.session_state.story_voice:
            st.session_state.story_voice = selected_voice
            st.rerun()

        vdata = WRITING_VOICES[st.session_state.story_voice]
        st.markdown(f"""
        <div style="font-size:0.72rem;color:var(--text3);
        padding:0.4rem 0.7rem;background:var(--bg3-glass);border-radius:6px;
        border:1px solid var(--bd-glass);margin-bottom:0.2rem;">
          {vdata['desc']}
        </div>
        """, unsafe_allow_html=True)

        # ── Pacing ──────────────────────────────
        st.markdown('<div class="config-label">⏱️ Pacing</div>', unsafe_allow_html=True)
        pacing_keys = list(PACING_MODES.keys())
        current_pacing = st.session_state.story_pacing
        selected_pacing = st.selectbox(
            "Pacing", pacing_keys,
            index=pacing_keys.index(current_pacing) if current_pacing in pacing_keys else 0,
            label_visibility="collapsed",
            key="pacing_select_story",
        )
        if selected_pacing != st.session_state.story_pacing:
            st.session_state.story_pacing = selected_pacing
            st.rerun()

        # ── Response Length ─────────────────────
        st.markdown('<div class="config-label">📏 Length</div>', unsafe_allow_html=True)
        length_keys = list(STORY_LENGTHS.keys())
        current_length = st.session_state.story_length
        selected_length = st.selectbox(
            "Length", length_keys,
            index=length_keys.index(current_length) if current_length in length_keys else 2,
            label_visibility="collapsed",
            key="length_select_story",
        )
        if selected_length != st.session_state.story_length:
            st.session_state.story_length = selected_length

        # ── Style Mimicry ───────────────────────
        st.markdown('<div class="config-label">✨ Style Mimicry</div>', unsafe_allow_html=True)
        mimicry_keys = list(STYLE_MIMICRY.keys())
        selected_mimicry = st.selectbox(
            "Style", mimicry_keys,
            index=mimicry_keys.index(st.session_state.story_style_mimicry) if st.session_state.story_style_mimicry in mimicry_keys else 0,
            label_visibility="collapsed",
            key="mimicry_select_story",
        )
        st.session_state.story_style_mimicry = selected_mimicry

        # ── Collaboration Mode ──────────────────
        st.markdown('<div class="config-label">🤝 Collaboration</div>', unsafe_allow_html=True)
        collab_keys = list(COLLAB_MODES.keys())
        selected_collab = st.selectbox(
            "Collab Mode", collab_keys,
            index=collab_keys.index(st.session_state.story_collab_mode) if st.session_state.story_collab_mode in collab_keys else 0,
            label_visibility="collapsed",
            key="collab_select_story",
        )
        st.session_state.story_collab_mode = selected_collab

        # ── Narrative Tools ─────────────────────
        if st.session_state.story_started:
            st.markdown('<div class="config-label">🔧 Narrative Tool</div>', unsafe_allow_html=True)
            st.markdown("<small style='color:var(--text3);font-size:0.72rem;'>Select to guide next continuation:</small>", unsafe_allow_html=True)

            tool_keys = list(NARRATIVE_TOOLS.keys())
            current_tool = st.session_state.story_tool
            for tool in tool_keys:
                is_sel = (tool == current_tool)
                label = f"{'✓ ' if is_sel else ''}{tool}"
                if st.button(label, key=f"ntool_{tool}", use_container_width=True):
                    st.session_state.story_tool = tool if not is_sel else None
                    st.rerun()

        # ── Character Tracker ──────────────────
        st.markdown('<div class="config-label">👤 Characters</div>', unsafe_allow_html=True)
        if st.session_state.story_characters:
            for i, ch in enumerate(st.session_state.story_characters):
                with st.expander(f"{ch.get('name', 'Character')} — {ch.get('role', '')}", expanded=False):
                    st.markdown(f"**Traits:** {ch.get('traits', '')}")
                    st.markdown(f"**Arc:** {ch.get('arc', '')}")
                    if st.button("✕ Remove", key=f"rm_char_{i}"):
                        st.session_state.story_characters.pop(i)
                        st.rerun()

        with st.expander("➕ Add Character", expanded=not bool(st.session_state.story_characters)):
            ch_name = st.text_input("Name", key="new_char_name", placeholder="e.g. Elena")
            ch_role = st.text_input("Role", key="new_char_role", placeholder="e.g. protagonist, mentor")
            ch_traits = st.text_input("Traits", key="new_char_traits", placeholder="e.g. stubborn, scarred, brilliant")
            ch_arc = st.text_input("Arc", key="new_char_arc", placeholder="e.g. learns to trust again")
            if st.button("Add Character", key="add_char_btn", use_container_width=True) and ch_name:
                st.session_state.story_characters.append({
                    "name": ch_name, "role": ch_role,
                    "traits": ch_traits, "arc": ch_arc,
                })
                st.rerun()

        # ── Branching Narratives ────────────────
        if st.session_state.story_started and st.session_state.story_full_text:
            st.markdown('<div class="config-label">🌿 Branches</div>', unsafe_allow_html=True)
            if st.button("📌 Save Branch Point", use_container_width=True, key="save_branch"):
                label = f"Ch{st.session_state.story_chapter} · {_word_count(st.session_state.story_full_text)}w"
                st.session_state.story_branches.append(st.session_state.story_full_text)
                st.session_state.story_branch_labels.append(label)
                st.toast(f"Branch saved: {label}")
            if st.session_state.story_branches:
                for i, lbl in enumerate(st.session_state.story_branch_labels):
                    if st.button(f"↩ {lbl}", key=f"load_branch_{i}", use_container_width=True):
                        st.session_state.story_full_text = st.session_state.story_branches[i]
                        st.session_state.story_word_count = _word_count(st.session_state.story_full_text)
                        st.rerun()

        # ── Author Notes ────────────────────────
        st.markdown('<div class="config-label">📝 Author Notes</div>', unsafe_allow_html=True)
        notes = st.text_area(
            "Notes", placeholder="Characters, world rules, things to remember...",
            value=st.session_state.story_notes,
            label_visibility="collapsed",
            key="story_notes_input",
            height=90,
        )
        st.session_state.story_notes = notes

        # ── Actions ─────────────────────────────
        st.markdown('<div class="config-label">⚙️ Actions</div>', unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1:
            if st.button("🗑️ Reset", use_container_width=True, key="story_reset"):
                for k in ["story_messages", "story_full_text", "story_title",
                          "story_started", "story_tool", "story_word_count", "story_chapter"]:
                    st.session_state[k] = [] if k == "story_messages" else (
                        "" if k in ["story_full_text", "story_title", "story_tool"] else
                        False if k == "story_started" else
                        0 if k == "story_word_count" else 1
                    )
                st.rerun()
        with a2:
            if st.session_state.story_full_text:
                st.download_button(
                    "📥 Export",
                    data=_export_story(),
                    file_name=f"{(st.session_state.story_title or 'story').replace(' ','_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="story_export",
                )

        # ── Back to study ───────────────────────
        st.markdown("---")
        if st.button("← Back to Study Chat", use_container_width=True, key="story_back"):
            st.session_state.app_mode = "chat"
            st.rerun()

    # ══════════════════════════════════════
    # RIGHT PANEL — Canvas + Input
    # ══════════════════════════════════════
    with canvas_col:

        # ── Story Stats Bar ─────────────────────
        if st.session_state.story_started:
            wc = _word_count(st.session_state.story_full_text)
            chapters = st.session_state.story_chapter
            genre_tag = st.session_state.story_genre.split(" ", 1)[0]
            voice_tag = st.session_state.story_voice.split(" ", 1)[1] if " " in st.session_state.story_voice else st.session_state.story_voice
            st.markdown(f"""
            <div class="story-stat-bar">
              <span>📖 <b>{wc:,}</b> words</span>
              <span>📂 Chapter <b>{chapters}</b></span>
              <span>🎭 <b>{genre_tag}</b></span>
              <span>🖊️ <b>{voice_tag[:18]}</b></span>
              {f'<span>🔧 <b>{st.session_state.story_tool.split(" ",1)[1] if st.session_state.story_tool else ""}</b></span>' if st.session_state.story_tool else ''}
            </div>
            """, unsafe_allow_html=True)

        # ── Story Canvas ────────────────────────
        if st.session_state.story_full_text:
            # Show full story text beautifully
            st.markdown(f"""
            <div class="story-canvas">{st.session_state.story_full_text}</div>
            """, unsafe_allow_html=True)
        else:
            # Empty state with spark prompts
            st.markdown(f"""
            <div class="story-canvas">
              <div class="story-canvas-empty">
                Your story will appear here.<br><br>
                Type your opening line below, or pick a spark prompt →
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Spark prompts for current genre
            st.markdown('<div class="config-label">✨ Spark Prompts</div>', unsafe_allow_html=True)
            examples = GENRES[st.session_state.story_genre].get("examples", [])
            for ex in examples:
                if st.button(f'"{ex}"', key=f"spark_{ex[:20]}", use_container_width=True):
                    st.session_state["_queued_story_prompt"] = ex
                    st.rerun()

        # ── Continuation Input ──────────────────
        st.markdown("")

        if not st.session_state.story_started:
            placeholder_text = f'Begin your {st.session_state.story_genre.split(" ",1)[-1]} story... (first line, opening scene, or just a feeling)'
        else:
            placeholder_text = "Continue the story, or type what happens next... (leave blank to let the AI decide)"

        user_story_input = st.chat_input(
            placeholder_text,
            key="story_chat_input",
        )

        # Check for queued spark prompt
        if st.session_state.get("_queued_story_prompt"):
            user_story_input = st.session_state.pop("_queued_story_prompt")

        # ── Process input ───────────────────────
        if user_story_input is not None and user_story_input.strip() != "" or user_story_input == "":
            # Allow empty input after start (AI continues freely)
            raw_input = (user_story_input or "").strip()

            if not raw_input and not st.session_state.story_started:
                st.info("✍️ Type your opening line to begin the story.")
            else:
                # Build the message to send
                tool = st.session_state.story_tool
                tool_instruction = ""
                if tool:
                    tool_instruction = f"\n\n[NARRATIVE DIRECTIVE: {NARRATIVE_TOOLS[tool]}]"

                length_tokens = STORY_LENGTHS[st.session_state.story_length]

                if not st.session_state.story_started:
                    # First turn — start the story
                    if raw_input:
                        user_msg_content = f"Begin the story with this opening. Develop it beautifully into a full opening scene:\n\n\"{raw_input}\"{tool_instruction}"
                    else:
                        user_msg_content = f"Begin an original {st.session_state.story_genre} story with a compelling opening scene.{tool_instruction}"
                else:
                    # Continuation
                    if raw_input:
                        user_msg_content = f"Continue the story. The user directs: \"{raw_input}\"{tool_instruction}\n\nPick up exactly where we left off. Match the established voice perfectly."
                    else:
                        user_msg_content = f"Continue the story naturally from where it ended. Use your literary judgment to advance the plot, character, or atmosphere.{tool_instruction}"

                    # Add chapter divider every ~600 words
                    wc = _word_count(st.session_state.story_full_text)
                    if wc > 0 and wc % 600 < 80:
                        st.session_state.story_chapter += 1
                        chapter_break = f"\n\n\n— Chapter {st.session_state.story_chapter} —\n\n"
                        st.session_state.story_full_text += chapter_break

                # Add user message to history
                st.session_state.story_messages.append({
                    "role": "user",
                    "content": user_msg_content,
                })

                # Build system prompt
                sys_prompt = build_story_system_prompt(
                    st.session_state.story_genre,
                    st.session_state.story_voice,
                    st.session_state.story_pacing,
                    extra_context=st.session_state.story_notes,
                    style_mimicry=st.session_state.story_style_mimicry,
                    collab_mode=st.session_state.story_collab_mode,
                    characters=st.session_state.story_characters,
                )

                # Keep only last 10 exchanges for context (saves tokens, maintains continuity)
                context_messages = st.session_state.story_messages[-20:]

                # Stream the story continuation
                with st.spinner("✍️ Writing..."):
                    generated = ""
                    try:
                        for chunk in ai_engine.generate_stream(
                            messages=context_messages,
                            context_text="",
                            model="llama-4-scout-17b-16e-instruct",
                            persona_prompt=sys_prompt,
                        ):
                            generated += chunk

                        # Clean up any AI meta-commentary
                        generated = re.sub(
                            r'^(Sure|Certainly|Of course|Here\'s|Here is|I\'ll|I will|Let me)[^\n]*\n+',
                            '', generated.strip(), flags=re.IGNORECASE
                        )
                        generated = generated.strip()

                        # Append to story canvas
                        if st.session_state.story_full_text:
                            st.session_state.story_full_text += "\n\n" + generated
                        else:
                            st.session_state.story_full_text = generated

                        # Add AI response to message history
                        st.session_state.story_messages.append({
                            "role": "assistant",
                            "content": generated,
                        })

                        # Generate title on first turn
                        if not st.session_state.story_started:
                            st.session_state.story_title = _generate_title(
                                generated, st.session_state.story_genre
                            )
                            st.session_state.story_started = True

                        # Clear narrative tool after use
                        st.session_state.story_tool = None

                        # Update word count
                        st.session_state.story_word_count = _word_count(st.session_state.story_full_text)

                    except Exception as e:
                        st.error(f"Story generation failed: {e}")

                st.rerun()
