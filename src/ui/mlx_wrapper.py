"""Own MLX 2.2 surfaces, transparent layering, and safe native callbacks."""
from collections import deque
from typing import Any, Callable
from mlx import Mlx

from .events import Event, EventFactory


# X11 event types used by MLX 2.2.
#
# These values come from the X11/XCB protocol.

KEY_PRESS = 2
KEY_RELEASE = 3

BUTTON_PRESS = 4
BUTTON_RELEASE = 5

MOTION_NOTIFY = 6

EXPOSE = 12

DESTROY_NOTIFY = 17

CLIENT_MESSAGE = 33


# X11 event masks.
#
# These are bit masks used with mlx_hook().
KEY_PRESS_MASK = 1
KEY_RELEASE_MASK = 2


"""X11 keysyms returned by the assigned MLX 2.2 XCB backend."""
KEY_ESC = 65307
KEY_ENTER = 65293
KEY_BACKSPACE = 65288

KEY_W = 119
KEY_A = 97
KEY_S = 115
KEY_D = 100
KEY_P = 112
KEY_C = 99
KEY_I = 105
KEY_N = 110
KEY_F = 102
KEY_L = 108
KEY_B = 98
KEY_V = 118

KEY_UP = 65362
KEY_DOWN = 65364
KEY_LEFT = 65361
KEY_RIGHT = 65363

POINTER_MOTION_MASK = 1 << 6


class ImageLayer:
    """One independent mlx image buffer. Nothing else can alias into it."""

    def __init__(
        self,
        mlx_instance: Any,
        mlx_ptr: Any,
        width: int,
        height: int,
    ) -> None:
        """Allocate and validate a transparent native image."""
        self.mlx = mlx_instance
        self.mlx_ptr = mlx_ptr
        self.data = memoryview(bytearray())
        self.width = width
        self.height = height

        self.image = mlx_instance.mlx_new_image(mlx_ptr, width, height)
        if not self.image:
            raise RuntimeError("MLX image creation failed")

        try:
            (
                self.data,
                self.bits_per_pixel,
                self.line_length,
                self.endian,
            ) = mlx_instance.mlx_get_data_addr(self.image)
            if (
                self.bits_per_pixel != 32
                or self.endian not in (0, 1)
                or self.line_length < width * 4
                or len(self.data) < self.line_length * height
            ):
                raise RuntimeError("Unsupported MLX image layout")
            self.bytes_per_pixel = 4
            self.clear()
        except BaseException:
            try:
                self.destroy()
            except BaseException:
                pass
            raise

    def destroy(self) -> None:
        """Invalidate the mapped buffer and destroy its native image once."""
        if not self.image:
            return
        image, self.image = self.image, None
        self.data.release()
        self.mlx.mlx_destroy_image(self.mlx_ptr, image)

    def _require_alive(self) -> None:
        """Raise RuntimeError if the native image has been destroyed."""
        if not self.image:
            raise RuntimeError("MLX image has been destroyed")

    def clear(self) -> None:
        """Clear all pixels to transparent, including row padding."""
        self._require_alive()
        self.data[:] = bytes(len(self.data))

    def fill(
        self,
        color: int,
    ) -> None:
        """Fill visible pixels with an ARGB opacity color."""
        self.put_rectangle(0, 0, self.width, self.height, color)

    def put_pixel(
        self,
        x: int,
        y: int,
        color: int,
    ) -> None:
        """Write one pixel, silently clipping out-of-bounds coordinates."""
        self._require_alive()
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        offset = y * self.line_length + x * self.bytes_per_pixel
        self.data[offset:offset + 4] = (color & 0xFFFFFFFF).to_bytes(
            4,
            "little" if self.endian == 0 else "big",
        )

    def put_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
    ) -> None:
        """Write a clipped rectangle using contiguous row writes."""
        self._require_alive()
        left, right = max(0, x), min(self.width, x + width)
        top, bottom = max(0, y), min(self.height, y + height)
        if left >= right or top >= bottom:
            return
        # MLX's format selects byte order; each row respects native padding.
        pixel = (color & 0xFFFFFFFF).to_bytes(
            4,
            "little" if self.endian == 0 else "big",
        )
        row = pixel * (right - left)
        for py in range(top, bottom):
            offset = py * self.line_length + left * 4
            self.data[offset:offset + len(row)] = row


class MlxWrapper:
    """Manage a window and independent ARGB layers with native blending."""

    def __init__(
        self,
        width: int,
        height: int,
        loop_callback: Callable[[deque[Event]], None],
    ) -> None:
        """Create a screen-bounded window, layers, and frame callback state."""
        self.width = width
        self.height = height

        self.mlx = Mlx()
        self.mlx_ptr: Any = None
        self.window: Any = None
        self._layers: dict[str, ImageLayer] = {}
        self._layer_order: list[str] = []
        self._background: ImageLayer | None = None
        self._closed = False
        self._stopped = False
        self._running = False
        self._loop_callback = loop_callback
        self._event_buffer: deque[Event] = deque()
        self._callback_error: BaseException | None = None
        self._close_requested = False
        try:
            self.mlx_ptr = self.mlx.mlx_init()
            if not self.mlx_ptr:
                raise RuntimeError("MLX initialization failed")
            _, screen_width, screen_height = self.mlx.mlx_get_screen_size(
                self.mlx_ptr,
            )
            width = min(width, max(1, int(screen_width) - 64))
            height = min(height, max(1, int(screen_height) - 64))
            self.width, self.height = width, height
            self.window = self.mlx.mlx_new_window(
                self.mlx_ptr,
                width,
                height,
                "Pac-Man",
            )
            if not self.window:
                raise RuntimeError("MLX window creation failed")
            self.create_layer("main")
            self._background = ImageLayer(
                self.mlx,
                self.mlx_ptr,
                width,
                height,
            )
            self._background.fill(0xFF000000)
        except BaseException:
            try:
                self.quit()
            except BaseException:
                pass
            raise

    def _require_open(self) -> None:
        """Raise RuntimeError if graphics resources have been closed."""
        if self._closed:
            raise RuntimeError("MLX graphics have been closed")

    # ------------------------------------------------------------------
    # Layer management
    # ------------------------------------------------------------------

    def create_layer(
        self,
        name: str,
    ) -> None:
        """Create a new independent drawing surface named `name`.

        A layer you draw to once and never clear() *is* the cache —
        it's a separate real mlx image, nothing can overwrite it
        except code that explicitly targets that layer name.
        """
        self._require_open()
        if name in self._layers:
            return
        layer = ImageLayer(self.mlx, self.mlx_ptr, self.width, self.height)
        self._layers[name] = layer
        self._layer_order.append(name)

    def remove_layer(
        self,
        name: str,
    ) -> None:
        """Remove and destroy a layer; missing layers are a no-op."""
        layer = self._layers.pop(name, None)
        if layer is not None:
            self._layer_order = [n for n in self._layer_order if n != name]
            layer.destroy()

    def has_layer(
        self,
        name: str,
    ) -> bool:
        """Report whether a named drawing surface exists."""
        return name in self._layers

    def get_layer(
        self,
        name: str,
    ) -> ImageLayer:
        """Return a layer, raising KeyError for unknown names."""
        return self._layers[name]

    def set_layer_order(
        self,
        order: list[str],
    ) -> None:
        """Bottom-to-top draw order, e.g. ['main', 'pacman', 'ghosts']."""
        missing = [n for n in order if n not in self._layers]
        if missing:
            raise KeyError(f"Unknown layer(s): {missing}")
        self._layer_order = list(order)

    def clear_layer(
        self,
        name: str,
    ) -> None:
        """Reset a layer to fully transparent pixels."""
        self._layers[name].clear()

    def fill_layer(
        self,
        name: str,
        color: int,
    ) -> None:
        """Fill a named layer using an ARGB opacity color."""
        self._layers[name].fill(color)

    # ------------------------------------------------------------------
    # Drawing (layer-aware)
    # ------------------------------------------------------------------

    def put_pixel(
        self,
        x: int,
        y: int,
        color: int,
        layer: str = "main",
    ) -> None:
        """Write a clipped pixel to a named layer."""
        self._layers[layer].put_pixel(x, y, color)

    def put_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
        layer: str = "main",
    ) -> None:
        """Write a clipped rectangle to a named layer."""
        self._layers[layer].put_rectangle(x, y, width, height, color)

    # ------------------------------------------------------------------
    # Native input and guarded event loop
    # ------------------------------------------------------------------

    def _guard_callback(
        self,
        action: Callable[[], None],
    ) -> None:
        """Contain even BaseException at the ctypes callback boundary."""
        if self._closed or self._stopped or self._callback_error is not None:
            return
        try:
            action()
        except BaseException as error:
            self._callback_error = error
            try:
                self.stop_loop()
            except BaseException:
                # Never let the error handler itself escape a C callback.
                pass

    def mouse_press(
        self,
        button: int,
        x: int,
        y: int,
        xvar: object,
    ) -> None:
        """Queue a mouse-button event safely from the native callback."""
        self._guard_callback(
            lambda: self._event_buffer.append(
                EventFactory.mouse_down(x, y, button)
            )
        )

    def mouse_move(
        self,
        x: int,
        y: int,
        xvar: object,
    ) -> None:
        """Queue pointer motion safely from the native callback."""
        self._guard_callback(
            lambda: self._event_buffer.append(
                EventFactory.mouse_move(x, y)
            )
        )

    def key_pressed(
        self,
        keycode: int,
        xvar: object,
    ) -> None:
        """Queue control and text events separately for the same key."""
        self._guard_callback(lambda: self._queue_key(keycode))

    def _queue_key(
        self,
        keycode: int,
    ) -> None:
        """Queue mapped controls and printable text for the supplied keysym."""
        controls: dict[int, Callable[[], Event]] = {
            KEY_ESC: EventFactory.key_esc,
            KEY_ENTER: EventFactory.key_enter,
            KEY_BACKSPACE: EventFactory.key_backspace,
            KEY_UP: EventFactory.key_up,
            KEY_DOWN: EventFactory.key_down,
            KEY_LEFT: EventFactory.key_left,
            KEY_RIGHT: EventFactory.key_right,
            ord("w"): EventFactory.key_up,
            ord("s"): EventFactory.key_down,
            ord("a"): EventFactory.key_left,
            ord("d"): EventFactory.key_right,
            ord("p"): EventFactory.key_pause,
            ord("c"): EventFactory.key_cheat,
            ord("i"): EventFactory.key_invincible,
            ord("n"): EventFactory.key_skip,
            ord("f"): EventFactory.key_freeze,
            ord("l"): EventFactory.key_life,
            ord("b"): EventFactory.key_speed,
            ord("v"): EventFactory.key_power,
        }
        # XCB provides keysyms (usually unshifted), not hardware scan codes.
        code = keycode + 32 if 65 <= keycode <= 90 else keycode
        factory = controls.get(code)
        if factory is not None:
            self._event_buffer.append(factory())
        if (
            48 <= keycode <= 57
            or 65 <= keycode <= 90
            or 97 <= keycode <= 122
            or keycode == 32
        ):
            self._event_buffer.append(EventFactory.text(chr(keycode)))

    def window_closed(
        self,
        xvar: object,
    ) -> None:
        """Deliver CLOSE on the next frame, then stop regardless of screen."""

        def close() -> None:
            """Queue a single close event and mark shutdown as requested."""
            if not self._close_requested:
                self._event_buffer.append(EventFactory.close())
                self._close_requested = True

        self._guard_callback(close)

    def loop(
        self,
        xvar: object,
    ) -> None:
        """Run one frame without allowing exceptions into native MLX."""

        def frame() -> None:
            """Deliver events to the app and stop after a close request."""
            self._loop_callback(self._event_buffer)
            if self._close_requested:
                self.stop_loop()

        self._guard_callback(frame)

    def start(self) -> None:
        """Run MLX, clean up outside C, then surface callback failures."""
        self._require_open()
        if self._running:
            raise RuntimeError("MLX loop is already running")
        error: BaseException | None = None
        try:
            # mlx_key_hook in this vendor binds KEY_RELEASE. Movement and
            # text input must react on press, so use the generic typed hook.
            self.mlx.mlx_hook(
                self.window,
                KEY_PRESS,
                KEY_PRESS_MASK,
                self.key_pressed,
                None,
            )
            self.mlx.mlx_mouse_hook(self.window, self.mouse_press, None)
            self.mlx.mlx_hook(
                self.window,
                MOTION_NOTIFY,
                POINTER_MOTION_MASK,
                self.mouse_move,
                None,
            )
            self.mlx.mlx_hook(
                self.window,
                CLIENT_MESSAGE,
                0,
                self.window_closed,
                None,
            )
            self.mlx.mlx_loop_hook(self.mlx_ptr, self.loop, None)
            if not self._stopped:
                self._running = True
                self.mlx.mlx_loop(self.mlx_ptr)
        except BaseException as failure:
            error = failure
        finally:
            self._running = False
            try:
                self.quit()
            except BaseException as failure:
                if error is None and self._callback_error is None:
                    error = failure
        if self._callback_error is not None:
            raise RuntimeError(
                f"MLX callback failed: {self._callback_error}"
            ) from self._callback_error
        if error is not None:
            raise error

    def stop_loop(self) -> None:
        """Request loop exit once; never touch an already released context."""
        if self._closed or self._stopped or not self.mlx_ptr:
            return
        self._stopped = True
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def quit(self) -> None:
        """Release images before window/context, attempting every cleanup."""
        if self._closed:
            return
        if self._running:
            self.stop_loop()
            return
        self._closed = True
        errors: list[BaseException] = []
        layers = list(self._layers.values())
        if self._background is not None:
            layers.append(self._background)
        self._layers.clear()
        self._layer_order.clear()
        self._background = None
        for layer in layers:
            try:
                layer.destroy()
            except BaseException as error:
                errors.append(error)
        window, self.window = self.window, None
        context, self.mlx_ptr = self.mlx_ptr, None
        if window:
            try:
                self.mlx.mlx_destroy_window(context, window)
            except BaseException as error:
                errors.append(error)
        if context:
            try:
                self.mlx.mlx_release(context)
            except BaseException as error:
                errors.append(error)
        if errors:
            raise RuntimeError(
                f"MLX cleanup failed: {errors[0]}"
            ) from errors[0]

    # ------------------------------------------------------------------
    # Compositing
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Blend layers bottom-to-top over a fresh opaque black surface.

        MLX 2.2 uses opacity (zero is transparent) and native source-over
        blending. The black base prevents trails when every layer is clear.
        """
        self._require_open()
        assert self._background is not None
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr,
            self.window,
            self._background.image,
            0,
            0,
        )
        for name in self._layer_order:
            layer = self._layers[name]
            self.mlx.mlx_put_image_to_window(
                self.mlx_ptr, self.window, layer.image, 0, 0,
            )
