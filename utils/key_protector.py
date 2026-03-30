"""
key_protector.py — no-op shim
Groq/key protection logic removed along with Groq.
"""

def protect(*args, **kwargs):
    pass

def scan_for_exposed_keys(*args, **kwargs) -> list:
    return []
