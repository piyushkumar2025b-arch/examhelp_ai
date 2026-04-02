"""
test_omnikey_live.py — Live test for OmniKey v4.0
Run: python test_omnikey_live.py
"""
import sys
sys.path.insert(0, ".")
from utils.omnikey_engine import OMNI_ENGINE

print("=== OMNIKEY LIVE TEST ===")
print(f"Keys loaded: {len(OMNI_ENGINE.slots)}")
print()

# Test 1: Basic call
print("[Test 1] Basic response...")
try:
    r = OMNI_ENGINE.execute(
        model="gemini-2.5-flash",
        prompt="What is 2+2? Answer in one sentence.",
        max_tokens=100,
    )
    print(f"  Result: {r.strip()}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: 3 rapid calls to verify RPM tracking & rotation
print()
print("[Test 2] 3 rapid calls (RPM + rotation)...")
for i in range(3):
    try:
        r = OMNI_ENGINE.execute(
            model="gemini-2.5-flash",
            prompt=f"Say only the exact text: Call{i+1} OK",
            max_tokens=30,
        )
        print(f"  Call {i+1}: {r.strip()}")
    except Exception as e:
        print(f"  Call {i+1} ERROR: {e}")

# Test 3: ai_engine.generate() wrapper
print()
print("[Test 3] ai_engine.generate() wrapper...")
try:
    from utils.ai_engine import generate
    r = generate(
        prompt="Name one planet in our solar system.",
        max_tokens=50,
    )
    print(f"  Result: {r.strip()}")
except Exception as e:
    print(f"  ERROR: {e}")

# Final status
print()
print("=== STATUS ===")
print(OMNI_ENGINE.get_key_status_line())
print()
for s in OMNI_ENGINE.slots:
    snap = s.snapshot()
    cd = f" | cooling {snap['cooldown_sec']:.0f}s" if snap["cooldown_sec"] > 0 else ""
    print(f"  {snap['alias']}: {snap['rpm_used']}/{snap['rpm_limit']} RPM, "
          f"{snap['total_calls']} calls, {snap['status']}{cd}")
