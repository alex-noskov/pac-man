from collections import deque
from typing import Callable

from .events import Event
from .font_map import FONT_MAP
from .mlx_wrapper import MlxWrapper


class Graphics:
    """Expose layered MLX drawing with bitmap text and shape helpers."""

    def __init__(
        self,
        width: int,
        height: int,
        app_loop: Callable[[deque[Event]], None],
    ) -> None:
        """Create an MLX window and bind its frame callback to app_loop."""
        self.mlx_wrapper = MlxWrapper(
            width=width,
            height=height,
            loop_callback=app_loop,
        )
        self.width = self.mlx_wrapper.width
        self.height = self.mlx_wrapper.height

    def start(self) -> None:
        """Run the native input and rendering loop."""
        self.mlx_wrapper.start()

    def stop_loop(self) -> None:
        """Request that the native event loop stop."""
        self.mlx_wrapper.stop_loop()

    def quit(self) -> None:
        """Release native graphics resources through the MLX wrapper."""
        self.mlx_wrapper.quit()

    def get_window_size(self) -> tuple[int, int]:
        """Return the actual window width and height in pixels."""
        return (self.width, self.height)

    def create_layer(
        self,
        name: str,
    ) -> None:
        """Create an independent drawing layer with the given name."""
        self.mlx_wrapper.create_layer(name)

    def remove_layer(
        self,
        name: str,
    ) -> None:
        """Remove the named drawing layer if it exists."""
        self.mlx_wrapper.remove_layer(name)

    def has_layer(
        self,
        name: str,
    ) -> bool:
        """Return whether the named drawing layer exists."""
        return self.mlx_wrapper.has_layer(name)

    def set_layer_order(
        self,
        order: list[str],
    ) -> None:
        """Set the named layers' bottom-to-top compositing order."""
        self.mlx_wrapper.set_layer_order(order)

    def clear(
        self,
        layer: str = "main",
    ) -> None:
        """Reset the named layer to transparent pixels."""
        self.mlx_wrapper.clear_layer(layer)

    def fill(
        self,
        color: int,
        layer: str = "main",
    ) -> None:
        """Fill the named layer with the given ARGB color."""
        self.mlx_wrapper.fill_layer(layer, color)

    def refresh(self) -> None:
        """Composite the ordered layers onto the window."""
        self.mlx_wrapper.refresh()

    def draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
        layer: str = "main",
    ) -> None:
        """Draw a filled pixel rectangle in the named layer."""
        self.mlx_wrapper.put_rectangle(
            x,
            y,
            width,
            height,
            color,
            layer=layer,
        )

    def draw_circle(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        color: int,
        layer: str = "main",
    ) -> None:
        """Draw a filled circle at the pixel center in the named layer."""
        radius_squared = radius * radius
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x * x + y * y <= radius_squared:
                    self.mlx_wrapper.put_pixel(
                        center_x + x,
                        center_y + y,
                        color,
                        layer=layer,
                    )

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: int,
        spacing: int = 1,
        scale: int = 1,
        layer: str = "main",
    ) -> None:
        """Draw bitmap glyphs with pixel spacing and integer scale."""
        char_width = 5 * scale

        for char_index, char in enumerate(text):
            bitmap = FONT_MAP.get(char)
            if bitmap is None:
                continue
            offset_x = char_index * (char_width + spacing)
            for iy, row in enumerate(bitmap):
                for ix, pixel in enumerate(row):
                    if pixel != "1":
                        continue
                    for dy in range(scale):
                        for dx in range(scale):
                            self.mlx_wrapper.put_pixel(
                                x=offset_x + ix * scale + dx + x,
                                y=iy * scale + dy + y,
                                color=color,
                                layer=layer,
                            )
