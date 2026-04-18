import streamlit as st

# High-Precision Limits (Conservative Safety Thresholds)
LIMITS = {
    "gemini": 1_000_000,
    "cerebras": 50_000,
    "groq": 20_000,  # Adjusted to more realistic free-tier TPM
}

def init_token_state():
    """Initialize necessary metrics in session state with low-lag defaults."""
    if "token_usage" not in st.session_state:
        st.session_state["token_usage"] = {"gemini": 0, "cerebras": 0, "groq": 0}
    if "api_blocked" not in st.session_state:
        st.session_state["api_blocked"] = False

def track_tokens(provider: str, text: str, exact_tokens: int = None):
    """
    ULTRA-LIVE TRACKING: 
    If exact_tokens is provided (from API usage metadata), use it for 100% precision.
    Otherwise, fall back to high-precision character estimate (1 t ≈ 3.5 chars).
    """
    init_token_state()
    
    if exact_tokens is not None:
        new_tokens = exact_tokens
    else:
        if not text: return
        # Calculate tokens precisely based on string length
        new_tokens = max(1, int(len(str(text)) / 3.5))
        
    st.session_state["token_usage"][provider] += new_tokens
    
    # Live Check for hard-stop breach
    max_thresh = LIMITS.get(provider, 1_000_000)
    if st.session_state["token_usage"][provider] >= max_thresh:
        st.session_state["api_blocked"] = True

def check_limit_stop():
    """Returns True if the engine must stop generation strictly due to limits."""
    init_token_state()
    return st.session_state.get("api_blocked", False)

def render_telemetry_sidebar():
    """
    Renders an Ultra-Advanced Cyber-Telemetry Dashboard.
    Features: Scanlines, Glowing Nodes, Glassmorphic Grid, and Secure Override UI.
    """
    init_token_state()
    
    # 1. Advanced Stylestylesheet Injection
    st.sidebar.markdown("""
        <style>
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
        }
        @keyframes glow-breathe {
            0%, 100% { opacity: 0.3; filter: blur(2px); }
            50% { opacity: 0.8; filter: blur(5px); }
        }
        .cyber-card {
            background: linear-gradient(145deg, rgba(10,20,40,0.9) 0%, rgba(5,10,20,0.95) 100%);
            border: 1px solid rgba(0, 255, 180, 0.2);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 0 15px rgba(0,255,180,0.05);
            margin-top: 25px;
        }
        .cyber-card::before {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: rgba(0, 255, 180, 0.4);
            animation: scanline 3s linear infinite;
            z-index: 1;
            opacity: 0.3;
        }
        .cyber-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 10px;
        }
        .node-dot {
            width: 6px; height: 6px;
            background: #00ffb4;
            border-radius: 50%;
            box-shadow: 0 0 10px #00ffb4;
            animation: glow-breathe 2s infinite;
        }
        .stat-label {
            font-family: 'Space Mono', monospace;
            font-size: 10px;
            color: rgba(0, 255, 180, 0.6);
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .progress-rail {
            width: 100%;
            height: 3px;
            background: #111;
            margin-top: 5px;
            position: relative;
        }
        .progress-bar-inner {
            height: 100%;
            transition: width 1s ease-out;
            box-shadow: 0 0 10px inherit;
        }
        .emergency-lock {
            background: rgba(255, 0, 0, 0.1);
            border: 1px dashed #ff4b4b;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: center;
        }
        </style>
        
        <div class='cyber-card'>
            <div class='cyber-header'>
                <span class='stat-label'>CORE LINK: ACTIVE</span>
                <div class='node-dot'></div>
            </div>
    """, unsafe_allow_html=True)
    
    # 2. Advanced Metrics Rows
    for provider, limit in LIMITS.items():
        used = st.session_state["token_usage"].get(provider, 0)
        pct = min(1.0, used / limit)
        
        color = "#00ffb4" if pct < 0.7 else "#ffaa00" if pct < 0.9 else "#ff4b4b"
        
        st.sidebar.markdown(f"""
            <div style='margin-bottom: 15px;'>
                <div style='display:flex; justify-content:space-between; font-family:"Space Mono", monospace; font-size:10px;'>
                    <span style='color:rgba(255,255,255,0.4);'>{provider.capitalize()} Submodule</span>
                    <span style='color:{color}; font-weight:bold;'>{used:,} TX</span>
                </div>
                <div class='progress-rail'>
                    <div class='progress-bar-inner' style='width:{pct*100}%; background:{color}; box-shadow: 0 0 8px {color};'></div>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:4px; font-size:9px; color:rgba(255,255,255,0.25);'>
                    <span>ALLOCATED: {limit//1000}k</span>
                    <span>{int(pct*100)}% LOAD</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # 3. Secure Override Button
    if st.session_state["api_blocked"]:
        st.sidebar.markdown("""
            <div class='emergency-lock'>
                <div style='color:#ff4b4b; font-family:"Orbitron", sans-serif; font-size:12px; font-weight:900; letter-spacing:1px;'>⚠️ PROTOCOL BREACH</div>
                <div style='color:rgba(255,255,255,0.4); font-size:9px; margin: 8px 0;'>QUOTA LIMIT EXCEEDED - CORE SEVERED</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button("EXECUTING SECURE OVERRIDE", use_container_width=True):
            st.session_state["api_blocked"] = False
            st.session_state["token_usage"] = {"gemini": 0, "cerebras": 0, "groq": 0}
            st.rerun()
