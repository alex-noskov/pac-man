from abc import ABC, abstractmethod

from ..models import AppState
from .events import Event


class Screen(ABC):
    """Base class for application screens."""

    @abstractmethod
    def handle_event(
        self,
        event: Event,
    ) -> AppState:
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

    def handle_event(
        self,
        event: Event,
    ) -> AppState:
        """Handle an input event."""
        return self._self_app_state

    def update(self) -> AppState:
        """Update screen logic."""
        return self._self_app_state

    def render(self) -> AppState:
        """Keep the terminal state inert while the native loop exits."""
        return self._self_app_state
