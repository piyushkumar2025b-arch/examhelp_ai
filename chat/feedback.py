import streamlit as st

class ChatFeedback:
    @staticmethod
    def save_feedback(message_id, liked: bool):
        st.toast(f"Feedback {'saved - liked! ✅' if liked else 'logged - we will improve 📉'}")
        
    @staticmethod
    def regenerate_prompt(messages):
        # Prevent zero-state pops
        if not messages: return None
        # Discard the last assistant output
        if messages[-1]["role"] == "assistant":
            messages.pop()
        # Rerun from the last user input
        if messages and messages[-1]["role"] == "user":
            return messages.pop()["content"]
        return None
