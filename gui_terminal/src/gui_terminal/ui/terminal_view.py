from __future__ import annotations

# Placeholder for future terminal widget implementation.

class TerminalView:  # pragma: no cover - GUI placeholder
    def __init__(self, max_buffer_lines: int = 5000) -> None:
        self.buffer: list[str] = []
        self.max_buffer_lines = max_buffer_lines

    def append_text(self, text: str) -> None:
        self.buffer.append(text)
        # Lazy trim to cap memory
        if len(self.buffer) > self.max_buffer_lines:
            # Drop older lines in batches for performance
            drop = len(self.buffer) - self.max_buffer_lines
            del self.buffer[:drop]
