from collections import deque
from typing import Callable
from mlx import Mlx
from .mlx_keycodes import (
    KEY_ENTER, KEY_UP, KEY_DOWN,
    KEY_ESC, KEY_LEFT, KEY_RIGHT
)
from .mlx_constants import CLIENT_MESSAGE
from ..events import EventFactory


class ImageLayer:
    """One independent mlx image buffer. Nothing else can alias into it."""

    def __init__(self, mlx_instance, mlx_ptr, width: int, height: int) -> None:
        self.mlx = mlx_instance
        self.width = width
        self.height = height

        self.image = mlx_instance.mlx_new_image(mlx_ptr, width, height)
        if not self.image:
            raise RuntimeError("MLX image creation failed")

        (
            self.data,
            self.bits_per_pixel,
            self.line_length,
            self.endian,
        ) = mlx_instance.mlx_get_data_addr(self.image)
        self.bytes_per_pixel = self.bits_per_pixel // 8

    def clear(self) -> None:
        self.data[:] = bytes(len(self.data))

    def fill(self, color: int) -> None:
        pixel = bytes((
            color & 0xFF,
            (color >> 8) & 0xFF,
            (color >> 16) & 0xFF,
            (color >> 24) & 0xFF,
        ))
        self.data[:] = pixel * (self.width * self.height)

    def put_pixel(self, x: int, y: int, color: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        offset = y * self.line_length + x * self.bytes_per_pixel
        self.data[offset] = color & 0xFF
        self.data[offset + 1] = (color >> 8) & 0xFF
        self.data[offset + 2] = (color >> 16) & 0xFF
        self.data[offset + 3] = (color >> 24) & 0xFF

    def put_rectangle(self, x: int, y: int, width: int, height: int,
                      color: int) -> None:
        for py in range(y, y + height):
            for px in range(x, x + width):
                self.put_pixel(px, py, color)


class MlxWrapper:
    def __init__(self, width: int, height: int,
                 loop_callback: Callable) -> None:
        self.width = width
        self.height = height

        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise RuntimeError("MLX initialization failed")

        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr, width, height, "Pac-Man",
        )
        if not self.window:
            self.mlx.mlx_release(self.mlx_ptr)
            raise RuntimeError("MLX window creation failed")

        # Named, ordered image layers. Composited bottom-to-top on refresh().
        self._layers: dict[str, ImageLayer] = {}
        self._layer_order: list[str] = []

        # Default layer so existing single-buffer call sites keep working.
        self.create_layer("main")

        self._loop_callback = loop_callback
        self._event_buffer: deque = deque()

    # ------------------------------------------------------------------
    # Layer management
    # ------------------------------------------------------------------

    def create_layer(self, name: str) -> None:
        """Create a new independent drawing surface named `name`.

        A layer you draw to once and never clear() *is* the cache —
        it's a separate real mlx image, nothing can overwrite it
        except code that explicitly targets that layer name.
        """
        if name in self._layers:
            return
        layer = ImageLayer(self.mlx, self.mlx_ptr, self.width, self.height)
        self._layers[name] = layer
        self._layer_order.append(name)

    def remove_layer(self, name: str) -> None:
        if name in self._layers:
            del self._layers[name]
            self._layer_order.remove(name)

    def has_layer(self, name: str) -> bool:
        return name in self._layers

    def get_layer(self, name: str) -> ImageLayer:
        return self._layers[name]

    def set_layer_order(self, order: list[str]) -> None:
        """Bottom-to-top draw order, e.g. ['main', 'pacman', 'ghosts']."""
        missing = [n for n in order if n not in self._layers]
        if missing:
            raise KeyError(f"Unknown layer(s): {missing}")
        self._layer_order = list(order)

    def clear_layer(self, name: str) -> None:
        self._layers[name].clear()

    def fill_layer(self, name: str, color: int) -> None:
        self._layers[name].fill(color)

    # ------------------------------------------------------------------
    # Drawing (layer-aware)
    # ------------------------------------------------------------------

    def put_pixel(self, x: int, y: int, color: int,
                  layer: str = "main") -> None:
        self._layers[layer].put_pixel(x, y, color)

    def put_rectangle(self, x: int, y: int, width: int, height: int,
                      color: int, layer: str = "main") -> None:
        self._layers[layer].put_rectangle(x, y, width, height, color)

    # ------------------------------------------------------------------
    # Input / event loop (unchanged behaviourally)
    # ------------------------------------------------------------------

    def mouse_press(self, button, x, y, xvar) -> None:
        self._event_buffer.append(EventFactory.mouse_down(x, y, button))

    def mouse_move(self, x, y, xvar) -> None:
        pass

    def key_pressed(self, keycode: int, xvar) -> None:
        if keycode == KEY_ESC:
            self._event_buffer.append(EventFactory.key_esc())
        elif keycode == KEY_ENTER:
            self._event_buffer.append(EventFactory.key_enter())
        elif keycode == KEY_UP:
            self._event_buffer.append(EventFactory.key_up())
        elif keycode == KEY_DOWN:
            self._event_buffer.append(EventFactory.key_down())
        elif keycode == KEY_LEFT:
            self._event_buffer.append(EventFactory.key_left())
        elif keycode == KEY_RIGHT:
            self._event_buffer.append(EventFactory.key_right())

    def window_closed(self, xvar) -> None:
        self.stop_loop()

    def loop(self, xvar) -> None:
        self._loop_callback(self._event_buffer)

    def start(self) -> None:
        self.mlx.mlx_key_hook(self.window, self.key_pressed, None)
        self.mlx.mlx_hook(self.window, CLIENT_MESSAGE,
                          0, self.window_closed, None)
        self.mlx.mlx_loop_hook(self.mlx_ptr, self.loop, None)
        self.mlx.mlx_loop(self.mlx_ptr)

    def stop_loop(self) -> None:
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def quit(self) -> None:
        self.mlx.mlx_destroy_window(self.mlx_ptr, self.window)
        self.mlx.mlx_release(self.mlx_ptr)

    # ------------------------------------------------------------------
    # Compositing
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Blit every layer to the window, in order."""
        for name in self._layer_order:
            layer = self._layers[name]
            self.mlx.mlx_put_image_to_window(
                self.mlx_ptr, self.window, layer.image, 0, 0,
            )

    # def get_mouse_pos(self) -> tuple:
    #    return self.mlx.mlx_mouse_get_pos(self.mlx_ptr, self.window)
