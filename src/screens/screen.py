from abc import ABC, abstractmethod
from ..models.app_state import AppState


class Screen(ABC):
    """Base class for application screens."""

    @abstractmethod
    def handle_event(self, event) -> AppState:
        """Handle an input event."""

    @abstractmethod
    def update(self) -> AppState:
        """Update screen logic."""

    @abstractmethod
    def render(self) -> AppState:
        """Render the screen."""


class ExitScreen(Screen):
    """Dummy exit screen"""

    def handle_event(self, event) -> AppState:
        """Handle an input event."""
        return AppState.EXIT

    def update(self) -> AppState:
        """Update screen logic."""
        return AppState.EXIT

    def render(self) -> AppState:
        return AppState.EXIT
