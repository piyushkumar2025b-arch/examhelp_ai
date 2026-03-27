import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

STUDY_SYSTEM_PROMPT = """You are ExamHelp, a dedicated AI study assistant. Your ONLY purpose is to help students with academic topics, studying, exam preparation, and learning.

You have access to content the student has uploaded or linked (PDFs, YouTube videos, web pages). When context is provided, prioritize answering from that content specifically.

Rules:
- ONLY answer study, academic, and educational questions.
- If asked anything unrelated to studying or academics, politely decline and redirect to studying.
- Be thorough, clear, and structured in your answers.
- Use bullet points, numbered lists, and headers when explaining complex topics.
- When answering from uploaded/linked material, always reference the source explicitly.
- Encourage the student and be supportive.
- For exam prep: give summaries, key points, potential exam questions, and mnemonics when useful.

You are laser-focused on helping students learn and ace their exams."""


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            pass
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Please set it in your .env file or Streamlit secrets.")
    return Groq(api_key=api_key)


def chat_with_groq(messages: list, context: str = "") -> str:
    """
    Send messages to Groq and get a response.
    messages: list of {"role": "user"/"assistant", "content": "..."}
    context: optional injected study material context
    """
    client = get_groq_client()

    system_content = STUDY_SYSTEM_PROMPT
    if context:
        system_content += f"\n\n---\nSTUDY MATERIAL CONTEXT (answer questions based on this):\n{context[:12000]}\n---"

    groq_messages = [{"role": "system", "content": system_content}] + messages

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=groq_messages,
        temperature=0.4,
        max_tokens=2048,
        stream=False,
    )

    return response.choices[0].message.content


def stream_chat_with_groq(messages: list, context: str = ""):
    """
    Stream response from Groq (for real-time token streaming in Streamlit).
    Yields string chunks.
    """
    client = get_groq_client()

    system_content = STUDY_SYSTEM_PROMPT
    if context:
        system_content += f"\n\n---\nSTUDY MATERIAL CONTEXT (answer questions based on this):\n{context[:12000]}\n---"

    groq_messages = [{"role": "system", "content": system_content}] + messages

    stream = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=groq_messages,
        temperature=0.4,
        max_tokens=2048,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
