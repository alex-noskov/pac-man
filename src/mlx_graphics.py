from ctypes import c_uint
from typing import Final

from mlx import Mlx

from .colors import BLACK, TRANSPARENT
from .font_map import FONT_MAP


_BYTES_PER_PIXEL: Final = 4


class Image:
    """An MLX image and its directly accessible pixel buffer."""

    def __init__(
        self,
        mlx: Mlx,
        mlx_ptr,
        width: int,
        height: int,
    ) -> None:
        self.width = width
        self.height = height

        self._mlx = mlx
        self._mlx_ptr = mlx_ptr

        self._ptr = mlx.mlx_new_image(
            mlx_ptr,
            width,
            height,
        )

        if not self._ptr:
            raise RuntimeError("mlx_new_image failed")

        (
            self.data,
            self.bits_per_pixel,
            self.line_length,
            self.endian,
        ) = mlx.mlx_get_data_addr(self._ptr)

        self.bytes_per_pixel = self.bits_per_pixel // 8

    @property
    def ptr(self):
        """Return the underlying MLX image pointer."""
        return self._ptr

    def set_pixel(self, x: int, y: int, color: int) -> None:
        """Set one pixel in the MLX image."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        offset = (
            y * self.line_length
            + x * self.bytes_per_pixel
        )

        # MLX images provided by the subject use 32-bit pixels.
        #
        # The exact byte order is determined by `endian`.
        # This writes the color in the usual little-endian
        # BGRA-style byte order used by MLX on the target system.
        self.data[offset] = color & 0xFF
        self.data[offset + 1] = (color >> 8) & 0xFF
        self.data[offset + 2] = (color >> 16) & 0xFF

        if self.bytes_per_pixel >= 4:
            self.data[offset + 3] = (color >> 24) & 0xFF

    def clear(self, color: int) -> None:
        """Fill the entire image with one color."""
        for y in range(self.height):
            for x in range(self.width):
                self.set_pixel(x, y, color)


class MlxGraphics:
    """Handle the game's MLX graphics."""

    def __init__(self, width: int, height: int) -> None:
        """Create the MLX context and window."""
        self.width = width
        self.height = height

        self.mlx = Mlx()

        self.mlx_ptr = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise RuntimeError("mlx_init failed")

        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr,
            width,
            height,
            "Pac-Man",
        )

        if not self.window:
            self.mlx.mlx_release(self.mlx_ptr)
            raise RuntimeError("mlx_new_window failed")

    def get_events(self):
        """
        MLX does not provide a pygame-style event queue.

        Event handling will be implemented through MLX hooks.
        """
        raise NotImplementedError

    def create_image(self, width: int, height: int) -> Image:
        """Create an independent MLX image."""
        return Image(
            mlx=self.mlx,
            mlx_ptr=self.mlx_ptr,
            width=width,
            height=height,
        )

    def put_image(
        self,
        image: Image,
        x: int,
        y: int,
        background_color: int = BLACK,
    ) -> None:
        """Display an image in the MLX window."""
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr,
            self.window,
            image.ptr,
            x,
            y,
        )

    def clear(self, color: int) -> None:
        """
        Clear the window.

        MLX's clear-window operation clears the window itself.
        """
        self.mlx.mlx_clear_window(
            self.mlx_ptr,
            self.window,
        )

        # `mlx_clear_window` does not take a color, so for now
        # this method only provides the same API as the old
        # Graphics class. A proper colored background should
        # be rendered through an image.
        _ = color

    def draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
    ) -> None:
        """
        Draw a rectangle.

        This preserves the old Graphics API. The rectangle is
        represented by an independent MLX image.
        """
        image = self.create_image(
            width=width,
            height=height,
        )

        image.clear(color)

        self.put_image(
            image=image,
            x=x,
            y=y,
        )

        self.mlx.mlx_destroy_image(
            self.mlx_ptr,
            image.ptr,
        )

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: int,
        background_color: int,
        spacing: int = 1,
        scale: int = 1,
    ) -> None:
        """Draw bitmap-font text."""
        char_width = 5
        char_height = 8

        scaled_char_width = char_width * scale
        scaled_char_height = char_height * scale
        scaled_spacing = spacing * scale

        image_width = (
            len(text) * (scaled_char_width + scaled_spacing)
            - scaled_spacing
        )

        if image_width <= 0:
            return

        image = self.create_image(
            width=image_width,
            height=scaled_char_height,
        )

        image.clear(background_color)

        for char_index, char in enumerate(text):
            bitmap = FONT_MAP.get(char)

            if bitmap is None:
                continue

            offset_x = char_index * (
                scaled_char_width + scaled_spacing
            )

            for iy, row in enumerate(bitmap):
                for ix, pixel in enumerate(row):
                    if pixel != "1":
                        continue

                    for dy in range(scale):
                        for dx in range(scale):
                            image.set_pixel(
                                x=offset_x + ix * scale + dx,
                                y=iy * scale + dy,
                                color=color,
                            )

        self.put_image(
            image=image,
            x=x,
            y=y,
        )

        self.mlx.mlx_destroy_image(
            self.mlx_ptr,
            image.ptr,
        )

    def get_window_size(self) -> tuple[int, int]:
        """Return the window dimensions."""
        return self.width, self.height

    def refresh(self) -> None:
        """
        MLX updates the window when images are put into it.

        Kept for compatibility with the existing Graphics API.
        """
        pass

    def quit(self) -> None:
        """Release MLX resources."""
        self.mlx.mlx_destroy_window(
            self.mlx_ptr,
            self.window,
        )

        self.mlx.mlx_release(
            self.mlx_ptr,
        )
