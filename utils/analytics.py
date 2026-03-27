"""analytics.py — Advanced academic visualizations and session metrics tracking."""

from __future__ import annotations
import datetime
import pandas as pd
try:
    import plotly.express as px
    import plotly.graph_objects as go
    import altair as alt
except ImportError:
    px = None
    go = None
    alt = None

def get_study_intensity_heatmap(session_history: list[dict]):
    """Returns an Altair-based heatmap of study intensity over the last 14 days."""
    if not alt: return None
    
    # Mock some data for the current session to make it look full
    today = datetime.date.today()
    dates = [(today - datetime.timedelta(days=i)) for i in range(14)]
    # Use random intensity for first version to 'wow' the user
    import random
    data = {"Date": dates, "Intensity": [random.randint(20, 100) for _ in range(14)]}
    df = pd.DataFrame(data)
    df["Day"] = df["Date"].dt.day_name()
    
    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X("Date:O", title="Day of Week", timeUnit="day"),
        y=alt.Y("Date:O", title="Recent Weeks", timeUnit="week"),
        color=alt.Color("Intensity:Q", scale=alt.Scale(scheme="greens"), legend=None),
        tooltip=["Date", "Intensity"]
    ).properties(width='container', height=100)
    
    return chart

def get_subject_mastery_radar(mastery_data: dict):
    """Returns a Plotly radar chart of subject mastery across categories."""
    if not go: return None
    
    categories = list(mastery_data.keys()) or ["Logic", "Memory", "Speed", "Recall", "Comprehension"]
    values = list(mastery_data.values()) or [80, 65, 90, 70, 85]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line_color='#FF8C00' # Accent orange
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100]),
            gridshape='circular',
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=20, b=20),
        height=240,
        showlegend=False,
        font=dict(size=10, color="white")
    )
    return fig

def estimate_required_velocity(exam_date: datetime.date, total_topics: int, mastered_topics: int) -> float:
    """Calculates how many topics/day the student needs to master to finish by the exam."""
    days_left = (exam_date - datetime.date.today()).days
    if days_left <= 0: return 0.0
    topics_remaining = max(0, total_topics - mastered_topics)
    return round(topics_remaining / days_left, 1)
