import sys
from unittest.mock import MagicMock

# 1. Brutally Mock Streamlit before it is ever imported by sub-modules
mock_st = MagicMock()
mock_st.session_state = {}
sys.modules["streamlit"] = mock_st

# 2. Mock other dependencies that might fail in CLI
sys.modules["utils.user_key_store"] = MagicMock()

from utils.token_tracker import init_token_state, track_tokens, check_limit_stop

def test_precision_tracking():
    print("--- [BATTLE-TEST] Precision Engine Integration ---")
    init_token_state()
    
    # 1. Verify current tracking state
    initial_gemini_count = mock_st.session_state["token_usage"].get("gemini", 0)
    print(f"Initial Gemini Count: {initial_gemini_count}")

    # 2. Test manual precision override
    print("Testing 100% Precision Override (500 tokens)...")
    track_tokens("gemini", "This text doesn't matter", exact_tokens=500)
    
    new_count = mock_st.session_state["token_usage"]["gemini"]
    print(f"New Gemini Count: {new_count}")
    
    if new_count == initial_gemini_count + 500:
        print("✅ SUCCESS: Precision override working perfectly.")
    else:
        print("❌ FAILURE: Precision override mismatch.")

    # 3. Verify limit stop logic
    mock_st.session_state["api_blocked"] = False
    print(f"Limit Stop Status (Before): {check_limit_stop()}")
    
    # Force breach
    track_tokens("gemini", "", exact_tokens=2_000_000)
    print(f"Limit Stop Status (After Breach): {check_limit_stop()}")
    
    if check_limit_stop():
        print("✅ SUCCESS: Security Core locked automatically on breach.")
    else:
        print("❌ FAILURE: Security Core failed to lock.")

if __name__ == "__main__":
    try:
        test_precision_tracking()
    except Exception as e:
        print(f"FATAL TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
