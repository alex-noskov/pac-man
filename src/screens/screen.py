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
    _self_app_state = AppState.EXIT

    def handle_event(self, event) -> AppState:
        """Handle an input event."""
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        return self._self_app_state
