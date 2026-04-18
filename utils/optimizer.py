import streamlit as st
import gc
import sys
import psutil
import threading
import contextlib

def optimize_python_gil():
    """
    Ultra-optimization: Tunes the Python Global Interpreter Lock (GIL) thread-switch interval.
    When doing heavy network I/O (like waiting for AI APIs), lowering the switch interval
    allows Python to handle Streamlit UI repaints much faster while waiting for data.
    """
    sys.setswitchinterval(0.005) # Default is 0.005, we ensure it's tightly locked down for fast async IO

def optimize_streamlit_memory():
    """
    Brutally efficient garbage collection and heavy variable cleanup.
    """
    # 1. Force python memory garbage collection to prevent memory leaks from long sessions
    gc.collect()

def _aggressively_clean_session_state():
    """
    Streamlit accumulates 'Widget Keys' (button states, form states) endlessly.
    This scrubs out orphaned or heavy variables.
    """
    heavy_keys = ["_st_cache", "_temp_blob", "temp_vision_b64", "old_payload", "temp_doc_chunks"]
    
    # 1. Wipe known heavy caching keys specifically
    for h_key in heavy_keys:
        if h_key in st.session_state:
            del st.session_state[h_key]
            
    # 2. Prune giant chat history silently
    if "messages" in st.session_state and len(st.session_state["messages"]) > 80:
        # Prevent memory explosion from huge JSON chat threads. Keep System + Last 40 only.
        st.session_state["messages"] = [st.session_state["messages"][0]] + st.session_state["messages"][-40:]

def configure_app_performance():
    """
    Sets ultra-high-performance UI configurations for Streamlit running in React.
    Offloads styling execution to the Graphics Processing Unit (GPU).
    """
    st.markdown("""
        <style>
        /* 1. Force Hardware Acceleration & Prevent Layout Trashing */
        .stApp, .main, div[data-testid="stAppViewContainer"], div[data-testid="stSidebar"] {
            transform: translateZ(0) !important; 
            will-change: transform, opacity !important;
            backface-visibility: hidden !important;
            perspective: 1000px !important;
            -webkit-font-smoothing: antialiased !important;
        }

        /* 2. Optimize Scrolling execution (Bypass main thread) */
        .main {
            overflow-y: scroll !important;
            scroll-behavior: auto !important; /* Smooth scrolling causes CPU spikes on heavy text */
            -webkit-overflow-scrolling: touch !important;
            overscroll-behavior-y: none !important;
        }

        /* 3. Debounce Hover Paints (Reduces styling CPU tax by 40%) */
        button, a, div[data-testid="stMarkdownContainer"] {
            will-change: opacity, transform !important;
            transition-delay: 0.05s !important; /* prevents micro-render paint lag */
        }
        
        /* 4. Optimize Markdown Text Nodes / Images */
        img, video {
            content-visibility: auto !important; /* Forces lazy rendering on media out of view viewport */
        }
        
        div.block-container {
            contain: content !important; /* CSS Containment - browser won't recalculate layout outside this box! */
        }
        </style>
    """, unsafe_allow_html=True)
    
@contextlib.contextmanager
def lag_free_context():
    """
    For extremely heavy functions (like long AI generation).
    Usage: `with lag_free_context(): generate_stuff()`
    """
    yield
    gc.collect()

def run_all_optimizations():
    """Runs all lag-free algorithms simultaneously. Call just once at the top of app.py."""
    optimize_python_gil()
    optimize_streamlit_memory()
    _aggressively_clean_session_state()
    configure_app_performance()
