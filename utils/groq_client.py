import os
from groq import Groq

MODEL = "llama3-8b-8192"  # old - decommissioned
MODEL = "llama-3.1-8b-instant"  # new replacement on Groq free tier

SYSTEM_PROMPT = """You are ExamHelp, a focused AI study assistant. Your ONLY purpose is to help students learn and understand academic material.

You MUST:
- Answer questions related to studying, learning, academic topics, and educational content
- Help summarize, explain, quiz, and clarify study material
- Be concise, clear, and educational in your responses

You MUST NOT:
- Answer questions unrelated to studying or academics
- Engage in casual conversation beyond brief greetings
- Help with non-academic tasks

If the user asks something off-topic, politely redirect them to study-related questions."""


def stream_chat_with_groq(messages: list, context_text: str = ""):
    """Stream a response from Groq given chat history and optional context."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set.")

    client = Groq(api_key=api_key)

    # Build system message with optional context
    system_content = SYSTEM_PROMPT
    if context_text:
        system_content += f"\n\n--- STUDY MATERIAL CONTEXT ---\n{context_text[:12000]}\n--- END CONTEXT ---"

    full_messages = [{"role": "system", "content": system_content}] + messages

    stream = client.chat.completions.create(
        model=MODEL,
        messages=full_messages,
        max_tokens=1024,
        temperature=0.7,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
