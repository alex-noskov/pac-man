from .mlx_wrapper import MlxWrapper
from .font_map import FONT_MAP
from . colors import BLACK
from typing import Callable


class Graphics:
    def __init__(self, width: int, height: int, app_loop: Callable) -> None:
        self.mlx_wrapper = MlxWrapper(width=width,
                                      height=height,
                                      loop_callback=app_loop)
        self.width = width
        self.height = height

    def start(self) -> None:
        self.mlx_wrapper.start()

    def stop_loop(self) -> None:
        self.mlx_wrapper.stop_loop()

    def quit(self) -> None:
        self.mlx_wrapper.quit()

    def get_window_size(self) -> tuple[int, int]:
        """Return the current window width and height."""
        return (self.width, self.height)

    def clear(self, color: int = BLACK) -> None:
        self.mlx_wrapper.clear(color)

    def refresh(self) -> None:
        self.mlx_wrapper.refresh()

    def draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
    ) -> None:
        self.mlx_wrapper.put_rectangle(
            x, y, width, height, color
        )

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: int,
        background_color: int,
        spacing: int = 1,
        scale: int = 1
    ) -> None:
        char_width = 5
        char_height = 8

        char_width *= scale
        char_height *= scale

        # image_width = len(text) * (char_width + spacing) - spacing
        # image = self.create_image(width=image_width, height=char_height)
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
                            )
        # self.put_image(image=image, x=x, y=y,
        #               background_color=background_color)

    def get_mouse_position(self) -> tuple:
        # return (self.mlx_wrapper.mouse_x, self.mlx_wrapper.mouse_y)
        return self.mlx_wrapper.get_mouse_pos()
        # return (1, 1)
