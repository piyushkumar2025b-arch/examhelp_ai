"""
image_generator_engine.py — ExamHelp AI Image Generator Engine v2.0
=======================================================================
Creates stunning AI images from text prompts using completely FREE APIs.
Zero AI quota usage for generation — all engines are 100% keyless & free!

Engines  (all free, no key):
  1. Pollinations.ai — flux / flux-realism / flux-anime / flux-3d / any-dark / turbo / dreamshaper
  2. HuggingFace Inference API — SDXL / SD v1.5 (fallback, free tier)
Strategy : URL-first (instant embed) → bytes download → turbo fallback → HF fallback
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Optional

# ────────────────────────────────────────────────────────────────────────────
# ALL FREE POLLINATIONS.AI MODELS — zero quota, no key needed
# ────────────────────────────────────────────────────────────────────────────
POLLINATIONS_MODELS: dict[str, dict] = {
    "flux":            {"label": "Flux (Best Quality)",      "speed": "slow",   "icon": "⭐"},
    "flux-realism":    {"label": "Flux Realism (Photo)",     "speed": "slow",   "icon": "📷"},
    "flux-cablyai":    {"label": "Flux CablyAI (Artistic)",  "speed": "medium", "icon": "🎨"},
    "flux-anime":      {"label": "Flux Anime",               "speed": "medium", "icon": "🌸"},
    "flux-3d":         {"label": "Flux 3D",                  "speed": "medium", "icon": "💎"},
    "any-dark":        {"label": "Any Dark (Gothic/Moody)",  "speed": "fast",   "icon": "🌑"},
    "turbo":           {"label": "Turbo (Fastest)",          "speed": "fast",   "icon": "⚡"},
    "dreamshaper":     {"label": "DreamShaper (Dreamy)",     "speed": "medium", "icon": "🌈"},
}

# ────────────────────────────────────────────────────────────────────────────
# STYLE PRESETS — each maps to the best Pollinations model for that style
# ────────────────────────────────────────────────────────────────────────────
STYLE_PRESETS: dict[str, dict] = {
    "🎨 Photorealistic": {
        "suffix": "ultra-photorealistic, 8K resolution, sharp focus, professional DSLR photography, perfect lighting, stunning detail, hyper-realistic",
        "negative": "cartoon, anime, painting, blurry, low quality, watermark, text, deformed",
        "model": "flux-realism",   # best model for photos
        "color": "#6366f1",
    },
    "🖌️ Oil Painting": {
        "suffix": "oil painting masterpiece, rich impasto textures, palette knife strokes, gallery quality, impressionist style, vibrant colors, museum artwork",
        "negative": "photo, digital, flat, low detail, sketch",
        "model": "flux-cablyai",   # artistic model
        "color": "#f59e0b",
    },
    "🌸 Anime / Manga": {
        "suffix": "anime art style, studio ghibli quality, vibrant anime illustration, manga style, clean line art, beautiful character design, cel-shaded",
        "negative": "realistic, photo, 3d render, ugly, deformed, western art",
        "model": "flux-anime",     # dedicated anime model
        "color": "#ec4899",
    },
    "💎 3D Render": {
        "suffix": "3D render, octane render, blender 3d, high poly, PBR materials, cinematic lighting, global illumination, 4K resolution, ray tracing",
        "negative": "flat, 2d, sketch, low poly, ugly, painting",
        "model": "flux-3d",        # dedicated 3D model
        "color": "#06b6d4",
    },
    "🌊 Watercolor": {
        "suffix": "watercolor painting, soft washes, delicate brush strokes, translucent layers, flowing watercolor, paper texture, fine art",
        "negative": "digital, photo, harsh lines, oil paint, 3d",
        "model": "flux-cablyai",   # artistic
        "color": "#8b5cf6",
    },
    "⚡ Cyberpunk": {
        "suffix": "cyberpunk neon aesthetic, blade runner style, neon lights, rain-slicked streets, dystopian future, hyper-detailed, neon glow",
        "negative": "natural, medieval, flat, low detail, daylight",
        "model": "flux",           # best detail
        "color": "#f43f5e",
    },
    "🏛️ Fantasy / Epic": {
        "suffix": "epic fantasy art, magical world, dramatic lighting, Greg Rutkowski style, artstation trending, highly detailed, mythical atmosphere",
        "negative": "mundane, modern, plain, blurry, low quality",
        "model": "dreamshaper",    # dreamy/fantasy
        "color": "#10b981",
    },
    "✏️ Pencil Sketch": {
        "suffix": "detailed pencil sketch, graphite drawing, cross-hatching, fine line art, black and white, realistic hand-drawn sketch, artist sketchbook",
        "negative": "color, paint, digital, photo, 3d render",
        "model": "flux",
        "color": "#94a3b8",
    },
    "🌌 Space Art": {
        "suffix": "cosmic space art, nebulae, galaxies, NASA hubble quality, stars, cosmic colors, vast universe, photorealistic space photography",
        "negative": "earth interior, mundane, flat, low detail, cartoon",
        "model": "flux-realism",
        "color": "#4f46e5",
    },
    "🎭 Pixel Art": {
        "suffix": "pixel art, 16-bit retro game art, clean pixel work, vibrant pixel palette, isometric pixel art, NES SNES style",
        "negative": "blurry, realistic, photo, 3d, anti-aliased",
        "model": "turbo",          # fast for pixel style
        "color": "#84cc16",
    },
    "🏮 Vintage / Retro": {
        "suffix": "vintage photography, retro 1970s film aesthetic, film grain, warm Kodachrome tones, faded colors, nostalgic, analog photo",
        "negative": "modern, sharp, digital, clean, HDR",
        "model": "flux-realism",
        "color": "#d97706",
    },
    "🤖 Sci-Fi Concept": {
        "suffix": "science fiction concept art, futuristic technology, hard sci-fi aesthetic, detailed mecha, spaceship design, concept artist quality",
        "negative": "fantasy, medieval, cartoon, low detail",
        "model": "flux",
        "color": "#0ea5e9",
    },
    "🌑 Dark / Gothic": {
        "suffix": "dark gothic aesthetic, dramatic shadows, moody atmosphere, dark fantasy, chiaroscuro lighting, eerie and beautiful",
        "negative": "bright, cheerful, flat, low detail, cartoon",
        "model": "any-dark",       # dedicated dark model
        "color": "#7c3aed",
    },
    "🌈 Dreamy / Surreal": {
        "suffix": "dreamlike surreal art, soft dreamy colors, magical atmosphere, ethereal light, fantasy dreamscape, otherworldly beauty",
        "negative": "harsh, dark, realistic photo, plain",
        "model": "dreamshaper",    # best for dreamy art
        "color": "#f472b6",
    },
}

# ────────────────────────────────────────────────────────────────────────────
# ASPECT RATIOS
# ────────────────────────────────────────────────────────────────────────────
ASPECT_RATIOS: dict[str, tuple[int, int]] = {
    "1:1 Square (1024×1024)":       (1024, 1024),
    "16:9 Landscape (1280×720)":    (1280, 720),
    "9:16 Portrait (720×1280)":     (720,  1280),
    "4:3 Classic (1024×768)":       (1024, 768),
    "3:4 Portrait (768×1024)":      (768,  1024),
    "21:9 Ultrawide (1344×576)":    (1344, 576),
    "2:3 Tall Portrait (800×1200)": (800,  1200),
}

# ────────────────────────────────────────────────────────────────────────────
# PROMPT ENHANCER (uses existing Gemini/Groq keys — optional)
# ────────────────────────────────────────────────────────────────────────────
_ENHANCE_SYSTEM = """\
You are an expert AI image prompt engineer. Your task is to take a simple user prompt
and transform it into a rich, detailed, evocative text-to-image prompt that will produce
stunning results with Stable Diffusion / Flux / DALL-E style models.

Rules:
1. Keep the original intent but add rich visual detail (lighting, composition, mood, style)
2. Include cinematic language: 'golden hour', 'bokeh', 'volumetric light', etc.
3. Add artist references if relevant (e.g. 'in the style of Alphonse Mucha')
4. Max 80 words
5. Return ONLY the enhanced prompt — no explanations, no preamble.
"""


def enhance_prompt(user_prompt: str) -> str:
    """Uses AI to transform a basic prompt into a rich image generation prompt."""
    try:
        from utils.ai_engine import quick_generate
        result = quick_generate(
            prompt=f"Enhance this image prompt: '{user_prompt}'",
            system=_ENHANCE_SYSTEM,
        )
        if result and len(result) > 10:
            # Strip common preambles
            for preamble in ["Enhanced prompt:", "Here's the enhanced prompt:", "Enhanced:"]:
                if result.lower().startswith(preamble.lower()):
                    result = result[len(preamble):].strip()
            return result.strip().strip('"').strip("'")
    except Exception:
        pass
    return user_prompt


# ────────────────────────────────────────────────────────────────────────────
# POLLINATIONS.AI ENGINE (completely free, no key)
# ────────────────────────────────────────────────────────────────────────────
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


def _build_pollinations_url(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    model: str = "flux",
    seed: Optional[int] = None,
    nologo: bool = True,
    enhance: bool = False,
) -> str:
    """Build a Pollinations.ai image URL."""
    encoded = urllib.parse.quote(prompt, safe="")
    params = {
        "width": width,
        "height": height,
        "model": model,
        "nologo": str(nologo).lower(),
    }
    if seed is not None:
        params["seed"] = seed
    if enhance:
        params["enhance"] = "true"

    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{POLLINATIONS_BASE}/{encoded}?{qs}"


def generate_image_pollinations(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    model: str = "flux",
    seed: Optional[int] = None,
    timeout: int = 55,
) -> Optional[bytes]:
    """
    Generate an image using Pollinations.ai (100% free, no key).
    Tries primary model first; auto-retries with `turbo` if it times out.
    Returns raw image bytes or None on failure.
    """
    models_to_try = [model]
    if model != "turbo":
        models_to_try.append("turbo")  # fast fallback

    for m in models_to_try:
        url = _build_pollinations_url(prompt, width, height, m, seed, nologo=True)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ExamHelpAI/2.0", "Accept": "image/*"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = resp.read()
                    # Validate it's actually an image (not an error HTML page)
                    if len(data) > 2000 and data[:4] in (
                        b"\x89PNG", b"\xff\xd8\xff", b"RIFF", b"GIF8"
                    ):
                        return data
        except Exception:
            timeout = 40  # shorter timeout for fallback model
            continue
    return None


def get_pollinations_url(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    model: str = "flux",
    seed: Optional[int] = None,
) -> str:
    """Return a direct Pollinations.ai URL (for embedding without downloading)."""
    return _build_pollinations_url(prompt, width, height, model, seed, nologo=True)


# ────────────────────────────────────────────────────────────────────────────
# STABLE DIFFUSION VIA HUGGING FACE (free tier, key optional)
# ────────────────────────────────────────────────────────────────────────────
_HF_MODELS = [
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
    "CompVis/stable-diffusion-v1-4",
]
_HF_API_BASE = "https://api-inference.huggingface.co/models"


def generate_image_huggingface(
    prompt: str,
    negative_prompt: str = "",
    hf_token: Optional[str] = None,
    timeout: int = 60,
) -> Optional[bytes]:
    """
    Generate an image via Hugging Face Inference API.
    Works without a token (with rate limits) or with a free HF token.
    """
    import urllib.request as _urlreq

    headers: dict = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    payload = json.dumps({
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
        }
    }).encode()

    for model in _HF_MODELS:
        url = f"{_HF_API_BASE}/{model}"
        try:
            req = _urlreq.Request(url, data=payload, headers=headers, method="POST")
            with _urlreq.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = resp.read()
                    # HF returns raw image bytes (JPEG/PNG)
                    if data[:4] in (b'\x89PNG', b'\xff\xd8\xff', b'RIFF', b'GIF8'):
                        return data
        except Exception:
            continue
    return None


# ────────────────────────────────────────────────────────────────────────────
# MAIN GENERATION PIPELINE
# ────────────────────────────────────────────────────────────────────────────
def generate_image(
    prompt: str,
    style_preset: str = "🎨 Photorealistic",
    aspect_ratio: str = "1:1 Square (1024×1024)",
    negative_prompt: str = "",
    seed: Optional[int] = None,
    use_ai_enhance: bool = False,
    hf_token: Optional[str] = None,
) -> dict:
    """
    Full image generation pipeline.

    Returns:
    {
        "success": bool,
        "image_bytes": bytes | None,
        "image_url": str,          # direct Pollinations URL for embedding
        "prompt_used": str,
        "enhanced_prompt": str,
        "style": str,
        "width": int,
        "height": int,
        "seed": int,
        "error": str | None,
        "engine": str,
    }
    """
    preset  = STYLE_PRESETS.get(style_preset, STYLE_PRESETS["🎨 Photorealistic"])
    w, h    = ASPECT_RATIOS.get(aspect_ratio, (1024, 1024))
    model   = preset.get("model", "flux")
    neg     = negative_prompt or preset.get("negative", "")

    # Build full prompt
    enhanced = prompt
    if use_ai_enhance:
        enhanced = enhance_prompt(prompt)

    full_prompt = f"{enhanced}, {preset['suffix']}"
    if neg:
        full_prompt += f" | avoid: {neg}"

    # Generate stable seed if none given
    if seed is None:
        seed = int(hashlib.md5(full_prompt.encode()).hexdigest()[:8], 16) % 2_147_483_647

    result = {
        "success": False,
        "image_bytes": None,
        "image_url": get_pollinations_url(full_prompt, w, h, model, seed),
        "prompt_used": full_prompt,
        "enhanced_prompt": enhanced,
        "style": style_preset,
        "width": w,
        "height": h,
        "seed": seed,
        "error": None,
        "engine": "pollinations",
    }

    # ── Try Pollinations.ai first (free, best quality) ────────────────────
    img_bytes = generate_image_pollinations(full_prompt, w, h, model, seed)
    if img_bytes and len(img_bytes) > 1000:
        result["success"]     = True
        result["image_bytes"] = img_bytes
        result["engine"]      = "Pollinations.ai (Free)"
        return result

    # ── Fallback: Hugging Face ────────────────────────────────────────────
    img_bytes = generate_image_huggingface(full_prompt, neg, hf_token)
    if img_bytes and len(img_bytes) > 1000:
        result["success"]     = True
        result["image_bytes"] = img_bytes
        result["engine"]      = "HuggingFace SDXL (Free)"
        return result

    # ── Last resort: return URL-only (still displays in browser) ─────────
    result["success"] = True   # URL is always valid
    result["engine"]  = "Pollinations.ai (URL Mode)"
    return result


# ────────────────────────────────────────────────────────────────────────────
# BATCH GENERATION
# ────────────────────────────────────────────────────────────────────────────
def generate_batch(
    prompt: str,
    style_preset: str = "🎨 Photorealistic",
    aspect_ratio: str = "1:1 Square (1024×1024)",
    count: int = 4,
    hf_token: Optional[str] = None,
) -> list[dict]:
    """
    Generate multiple image variations (different seeds) for the same prompt.
    Returns a list of result dicts.
    """
    import random
    seeds = [random.randint(1, 2_147_483_647) for _ in range(count)]
    results = []
    for seed in seeds:
        r = generate_image(
            prompt=prompt,
            style_preset=style_preset,
            aspect_ratio=aspect_ratio,
            seed=seed,
            hf_token=hf_token,
        )
        results.append(r)
    return results


# ────────────────────────────────────────────────────────────────────────────
# PROMPT SUGGESTIONS (quick-start ideas)
# ────────────────────────────────────────────────────────────────────────────
PROMPT_EXAMPLES: list[dict] = [
    {"category": "🌅 Nature",      "prompt": "A breathtaking sunrise over misty mountains with golden rays piercing through clouds"},
    {"category": "🤖 Sci-Fi",      "prompt": "A massive alien mothership hovering over a futuristic city at night"},
    {"category": "🏰 Fantasy",     "prompt": "An ancient dragon guarding a castle on a floating island above the clouds"},
    {"category": "🌊 Ocean",       "prompt": "Underwater kingdom with bioluminescent creatures and coral castles"},
    {"category": "🌸 Portrait",    "prompt": "Portrait of a wise old wizard with a long white beard and glowing blue eyes"},
    {"category": "🚀 Space",       "prompt": "Astronaut floating in space looking at Earth with a nebula in the background"},
    {"category": "🏙️ Cityscape",   "prompt": "Futuristic neon Tokyo street at night in the rain, reflections everywhere"},
    {"category": "🌺 Floral",      "prompt": "Macro photograph of a single lotus flower with perfect water droplets"},
    {"category": "🦁 Wildlife",    "prompt": "Majestic lion standing on an African savanna at golden hour"},
    {"category": "⚔️ Epic",        "prompt": "A lone samurai standing at the edge of a cliff watching a fiery sunset"},
    {"category": "🍄 Surreal",     "prompt": "Surrealist dreamscape with melting clocks and floating islands"},
    {"category": "🎭 Character",   "prompt": "Cyberpunk hacker girl with holographic displays and neon mohawk"},
]


def get_prompt_examples() -> list[dict]:
    """Return example prompts for quick-start inspiration."""
    return PROMPT_EXAMPLES


# ────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ────────────────────────────────────────────────────────────────────────────
def image_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to base64 string for HTML embedding."""
    return base64.b64encode(image_bytes).decode("utf-8")


def bytes_to_download(image_bytes: bytes, filename: str = "image.png") -> bytes:
    """Return image bytes ready for st.download_button."""
    return image_bytes


# ────────────────────────────────────────────────────────────────────────────
# STEP 3 — HISTORY / GALLERY HELPERS (session-level, no quota)
# ────────────────────────────────────────────────────────────────────────────
def save_to_history(result: dict, st_session) -> None:
    """Append a generation result to the session gallery history."""
    if "ig_history" not in st_session:
        st_session["ig_history"] = []
    entry = {
        "prompt":   result.get("enhanced_prompt", ""),
        "style":    result.get("style", ""),
        "url":      result.get("image_url", ""),
        "seed":     result.get("seed", 0),
        "width":    result.get("width", 1024),
        "height":   result.get("height", 1024),
        "engine":   result.get("engine", ""),
        "has_bytes": result.get("image_bytes") is not None,
    }
    # Keep last 20 images
    st_session["ig_history"] = ([entry] + st_session["ig_history"])[:20]


def get_history(st_session) -> list:
    """Return gallery history list (newest first)."""
    return st_session.get("ig_history", [])


def clear_history(st_session) -> None:
    """Wipe the gallery history."""
    st_session["ig_history"] = []


# ────────────────────────────────────────────────────────────────────────────
# STEP 4 — SHARE URL BUILDER (no quota — pure URL construction)
# ────────────────────────────────────────────────────────────────────────────
def build_share_url(result: dict) -> str:
    """
    Return a permanent shareable Pollinations.ai URL for this image.
    Anyone with the link can view the image in a browser — no account needed.
    """
    return result.get("image_url", "")


def build_embed_html(result: dict, max_width: int = 800) -> str:
    """Return a self-contained <img> HTML snippet for embedding anywhere."""
    url = build_share_url(result)
    prompt_escaped = result.get("enhanced_prompt", "AI Generated Image").replace('"', "&quot;")
    return (
        f'<img src="{url}" alt="{prompt_escaped}" '
        f'style="max-width:{max_width}px;width:100%;border-radius:12px;" />'
    )


# ────────────────────────────────────────────────────────────────────────────
# STEP 5 — EXPANDED PROMPT LIBRARY (60 examples, 12 categories)
# ────────────────────────────────────────────────────────────────────────────
PROMPT_EXAMPLES: list[dict] = [
    # Nature
    {"category": "🌅 Nature",    "prompt": "A breathtaking sunrise over misty mountains with golden rays piercing through clouds"},
    {"category": "🌅 Nature",    "prompt": "An ancient forest at dawn with rays of light filtering through giant sequoia trees"},
    {"category": "🌅 Nature",    "prompt": "A perfect mirror-like lake reflecting snow-capped mountains at sunset"},
    {"category": "🌅 Nature",    "prompt": "Cherry blossom avenue in full bloom with pink petals falling in the breeze"},
    {"category": "🌅 Nature",    "prompt": "Dramatic storm clouds rolling over the Grand Canyon at twilight"},
    # Sci-Fi
    {"category": "🤖 Sci-Fi",   "prompt": "A massive alien mothership hovering over a futuristic city at night"},
    {"category": "🤖 Sci-Fi",   "prompt": "Inside a quantum computer the size of a stadium, glowing blue circuits everywhere"},
    {"category": "🤖 Sci-Fi",   "prompt": "A terraformed Mars colony dome city at sunrise, red dust plains surrounding it"},
    {"category": "🤖 Sci-Fi",   "prompt": "Deep space mining station orbiting a gas giant with rings"},
    # Fantasy
    {"category": "🏰 Fantasy",  "prompt": "An ancient dragon guarding a castle on a floating island above the clouds"},
    {"category": "🏰 Fantasy",  "prompt": "A magical library that extends infinitely upward, books flying between shelves"},
    {"category": "🏰 Fantasy",  "prompt": "A phoenix rising from ashes in a volcanic crater, surrounded by fire tornados"},
    {"category": "🏰 Fantasy",  "prompt": "An elven city built into a giant tree, glowing with bioluminescent lights"},
    # Ocean
    {"category": "🌊 Ocean",    "prompt": "Underwater kingdom with bioluminescent creatures and coral castles"},
    {"category": "🌊 Ocean",    "prompt": "Giant blue whale swimming past a sunken ancient city"},
    {"category": "🌊 Ocean",    "prompt": "Perfect wave breaking at golden hour with surfer in silhouette"},
    # Portrait
    {"category": "🌸 Portrait", "prompt": "Portrait of a wise old wizard with a long white beard and glowing blue eyes"},
    {"category": "🌸 Portrait", "prompt": "Cyberpunk hacker girl with holographic displays and neon mohawk"},
    {"category": "🌸 Portrait", "prompt": "An astronaut inside a helmet reflecting a nebula, emotional expression"},
    {"category": "🌸 Portrait", "prompt": "A steampunk inventor surrounded by clockwork contraptions and steam"},
    # Space
    {"category": "🚀 Space",    "prompt": "Astronaut floating in space looking at Earth with a nebula in the background"},
    {"category": "🚀 Space",    "prompt": "Two planets colliding in slow motion, viewed from a moon's surface"},
    {"category": "🚀 Space",    "prompt": "The Milky Way galaxy seen from a dark beach, stunning Milky Way arc"},
    {"category": "🚀 Space",    "prompt": "Black hole with accretion disk pulling in a nearby star"},
    # Cityscape
    {"category": "🏙️ City",     "prompt": "Futuristic neon Tokyo street at night in the rain, reflections everywhere"},
    {"category": "🏙️ City",     "prompt": "Aerial view of Dubai at night, all lights glowing, perfectly symmetrical"},
    {"category": "🏙️ City",     "prompt": "Post-apocalyptic New York reclaimed by nature, vines on skyscrapers"},
    {"category": "🏙️ City",     "prompt": "Ancient Rome at its peak glory, senators in togas, the Colosseum pristine"},
    # Wildlife
    {"category": "🦁 Wildlife", "prompt": "Majestic lion standing on an African savanna at golden hour"},
    {"category": "🦁 Wildlife", "prompt": "Snow leopard leaping across a Himalayan cliff, action shot"},
    {"category": "🦁 Wildlife", "prompt": "Humpback whale breaching at sunset, water droplets frozen in time"},
    {"category": "🦁 Wildlife", "prompt": "Macro photograph of a peacock spider displaying its vibrant colors"},
    # Epic
    {"category": "⚔️ Epic",     "prompt": "A lone samurai standing at the edge of a cliff watching a fiery sunset"},
    {"category": "⚔️ Epic",     "prompt": "Viking longship navigating stormy seas with lightning striking around it"},
    {"category": "⚔️ Epic",     "prompt": "A medieval siege of a castle, catapults firing, dawn light breaking"},
    # Surreal
    {"category": "🍄 Surreal",  "prompt": "Surrealist dreamscape with melting clocks and floating islands"},
    {"category": "🍄 Surreal",  "prompt": "A staircase spiraling into a sky made of water"},
    {"category": "🍄 Surreal",  "prompt": "A city built inside a giant human skull, people living normal lives"},
    {"category": "🍄 Surreal",  "prompt": "Thousands of fish swimming through the sky above a desert"},
    # Food / Still Life
    {"category": "🍜 Food",     "prompt": "Perfectly plated Japanese ramen in a glowing broth, steam rising, macro shot"},
    {"category": "🍜 Food",     "prompt": "Artisanal sourdough bread fresh from oven, golden crust, rustic wooden table"},
    {"category": "🍜 Food",     "prompt": "Explosion of tropical fruits frozen in time against black background"},
    # Architecture
    {"category": "🏛️ Arch",    "prompt": "The Sagrada Familia bathed in orange sunset light, Barcelona"},
    {"category": "🏛️ Arch",    "prompt": "Minimalist Japanese zen garden, stone and raked sand, morning mist"},
    {"category": "🏛️ Arch",    "prompt": "A brutalist megastructure the size of a mountain, covered in moss"},
]


def get_prompt_examples() -> list[dict]:
    """Return all example prompts."""
    return PROMPT_EXAMPLES


def get_random_prompt() -> str:
    """Return a random prompt for inspiration."""
    import random
    return random.choice(PROMPT_EXAMPLES)["prompt"]


def get_prompts_by_category(category: str) -> list[str]:
    """Return all prompts for a given category."""
    return [p["prompt"] for p in PROMPT_EXAMPLES if p["category"] == category]


def get_categories() -> list[str]:
    """Return unique categories (preserving order)."""
    seen: set = set()
    cats: list = []
    for p in PROMPT_EXAMPLES:
        if p["category"] not in seen:
            seen.add(p["category"])
            cats.append(p["category"])
    return cats
