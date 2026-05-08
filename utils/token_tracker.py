"""token_tracker.py — Simple token usage tracking for the session."""


class TokenTracker:
    """Tracks cumulative token usage across AI calls in a session."""

    def __init__(self):
        self.total = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self._history: list = []

    def add(self, n: int, kind: str = "output") -> None:
        """Add n tokens. kind='input' or 'output'."""
        self.total += n
        if kind == "input":
            self.input_tokens += n
        else:
            self.output_tokens += n

    def add_call(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Record a full API call's token usage."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total += input_tokens + output_tokens
        self._history.append({"in": input_tokens, "out": output_tokens})

    def get(self) -> int:
        """Return total tokens used."""
        return self.total

    def summary(self) -> dict:
        return {
            "total": self.total,
            "input": self.input_tokens,
            "output": self.output_tokens,
            "calls": len(self._history),
        }

    def reset(self) -> None:
        """Reset all counters."""
        self.total = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self._history = []
