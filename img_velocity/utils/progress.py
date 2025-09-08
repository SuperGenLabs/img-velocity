"""Progress tracking utilities."""

import shutil
import sys

from .helpers import format_time


class ProgressTracker:
    """Handles progress display and time estimation."""

    def __init__(self):
        self.active = False
        self.last_line = ""

    def display_progress(
        self, current: int, total: int, elapsed_time: float, bar_width: int = 40
    ) -> None:
        """Display progress bar with time estimation."""
        self.active = True
        percent = (current / total) * 100
        filled = int(bar_width * current / total)
        bar = "█" * filled + "░" * (bar_width - filled)

        # Calculate estimated time remaining
        if current > 0:
            avg_time_per_item = elapsed_time / current
            remaining_items = total - current
            eta_seconds = avg_time_per_item * remaining_items
            eta_str = f" ETA: {format_time(eta_seconds)}"
        else:
            eta_str = " ETA: calculating..."

        # Build progress line and ensure it fits in terminal
        progress_line = f"[{bar}] {current}/{total} ({percent:.1f}%){eta_str}"

        # Get terminal width and truncate if necessary
        try:
            terminal_width = shutil.get_terminal_size().columns
            if len(progress_line) > terminal_width - 1:  # Leave 1 char margin
                # Reduce bar width if line is too long
                max_bar_width = (
                    terminal_width
                    - len(f"[] {current}/{total} ({percent:.1f}%){eta_str}")
                    - 2
                )
                if max_bar_width > 10:  # Minimum bar width
                    filled = int(max_bar_width * current / total)
                    bar = "█" * filled + "░" * (max_bar_width - filled)
                    progress_line = (
                        f"[{bar}] {current}/{total} ({percent:.1f}%){eta_str}"
                    )
                else:
                    # If still too long, show minimal version
                    progress_line = f"{current}/{total} ({percent:.1f}%){eta_str}"
        except (OSError, ValueError):
            # Fallback if terminal size detection fails
            pass

        # Store and display the progress line
        self.last_line = progress_line
        sys.stdout.write(f"\r{progress_line}")
        sys.stdout.flush()

        # Mark as inactive when complete
        if current >= total:
            self.active = False
            sys.stdout.write("\n")
            sys.stdout.flush()

    def redraw(self) -> None:
        """Redraw the last progress line (used after logging output)."""
        if self.active and self.last_line:
            sys.stdout.write(f"\r{self.last_line}")
            sys.stdout.flush()
