"""analytics.py — Academic visualizations and session metrics tracking."""

from __future__ import annotations
import datetime

try:
    import plotly.graph_objects as go
except ImportError:
    go = None


def get_subject_mastery_radar(mastery_data: dict):
    """Returns a Plotly radar chart of subject mastery across categories.
    
    If mastery_data is empty, uses sensible defaults for first-time display.
    """
    if not go:
        return None

    categories = list(mastery_data.keys()) if mastery_data else [
        "Logic", "Memory", "Speed", "Recall", "Comprehension"
    ]
    values = list(mastery_data.values()) if mastery_data else [80, 65, 90, 70, 85]

    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],  # close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        line_color='#FF8C00',
        fillcolor='rgba(255,140,0,0.15)',
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, ticks=''),
            angularaxis=dict(color='rgba(255,255,255,0.6)'),
            gridshape='circular',
            bgcolor='rgba(0,0,0,0)',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=20, b=20),
        height=240,
        showlegend=False,
        font=dict(size=10, color="rgba(255,255,255,0.7)"),
    )
    return fig


def get_study_intensity_heatmap(session_messages: list[dict]):
    """Returns a Plotly heatmap of study activity over the last 7 days.
    
    Uses message timestamps if available, otherwise generates a placeholder.
    """
    if not go:
        return None

    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
    labels = [d.strftime("%a") for d in days]

    # Count messages per day if timestamps exist
    counts = [0] * 7
    for msg in session_messages:
        ts = msg.get("timestamp")
        if ts:
            try:
                msg_date = datetime.date.fromisoformat(ts[:10])
                for i, d in enumerate(days):
                    if msg_date == d:
                        counts[i] += 1
            except (ValueError, TypeError):
                pass

    # If no real data, use placeholder
    if all(c == 0 for c in counts):
        import random
        random.seed(today.toordinal())
        counts = [random.randint(2, 12) for _ in range(7)]

    fig = go.Figure(data=go.Bar(
        x=labels,
        y=counts,
        marker_color='#FF8C00',
        marker_line_width=0,
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=10, t=10, b=20),
        height=120,
        showlegend=False,
        xaxis=dict(color='rgba(255,255,255,0.5)', showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        font=dict(size=9, color="rgba(255,255,255,0.6)"),
        bargap=0.3,
    )
    return fig


def estimate_required_velocity(exam_date: datetime.date, total_topics: int, mastered_topics: int) -> float:
    """Calculates how many topics/day the student needs to master to finish by the exam."""
    days_left = (exam_date - datetime.date.today()).days
    if days_left <= 0:
        return 0.0
    topics_remaining = max(0, total_topics - mastered_topics)
    return round(topics_remaining / days_left, 1)
