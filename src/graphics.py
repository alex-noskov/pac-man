from .mlx_wrapper import MlxWrapper
from .font_map import FONT_MAP
from typing import Callable


class Graphics:
    def __init__(self, width: int, height: int, app_loop: Callable) -> None:
        self.mlx_wrapper = MlxWrapper(width=width, height=height,
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
        return (self.width, self.height)

    def create_layer(self, name: str) -> None:
        self.mlx_wrapper.create_layer(name)

    def remove_layer(self, name: str) -> None:
        self.mlx_wrapper.remove_layer(name)

    def has_layer(self, name: str) -> bool:
        return self.mlx_wrapper.has_layer(name)

    def set_layer_order(self, order: list[str]) -> None:
        self.mlx_wrapper.set_layer_order(order)

    def clear(self, layer: str = "main") -> None:
        self.mlx_wrapper.clear_layer(layer)

    def fill(self, color: int, layer: str = "main") -> None:
        self.mlx_wrapper.fill_layer(layer, color)

    def refresh(self) -> None:
        self.mlx_wrapper.refresh()

    def draw_rectangle(self, x: int, y: int, width: int, height: int,
                       color: int, layer: str = "main") -> None:
        self.mlx_wrapper.put_rectangle(x, y, width, height, color, layer=layer)

    def draw_circle(self, center_x: int, center_y: int, radius: int,
                    color: int, layer: str = "main") -> None:
        radius_squared = radius * radius
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x * x + y * y <= radius_squared:
                    self.mlx_wrapper.put_pixel(
                        center_x + x, center_y + y, color, layer=layer)

    def draw_text(self, text: str, x: int, y: int, color: int,
                  spacing: int = 1, scale: int = 1,
                  layer: str = "main") -> None:
        char_width = 5 * scale
        # char_height = 8 * scale
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

    def draw_image(self, x: int, y: int, bits: list[str], line_len: int,
                   color: int, scale: int = 1,
                   layer: str = "main") -> None:
        ix = iy = 0
        for bit in bits:
            if bit == "1":
                for dy in range(scale):
                    for dx in range(scale):
                        self.mlx_wrapper.put_pixel(
                            x=x + ix * scale + dx,
                            y=y + iy * scale + dy,
                            color=color,
                            layer=layer,
                        )
            ix += 1
            if ix == line_len:
                ix = 0
                iy += 1

    def visualise_dot(self, x: int, y: int, layer: str = "main") -> None:
        self.mlx_wrapper.put_pixel(x, y, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+1, y+1, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+2, y+2, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+3, y+3, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+4, y+4, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+1, y-1, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+2, y-2, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+3, y-3, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x+4, y-4, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-1, y+1, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-2, y+2, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-3, y+3, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-4, y+4, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-1, y-1, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-2, y-2, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-3, y-3, 0xFF800080, layer)
        self.mlx_wrapper.put_pixel(x-4, y-4, 0xFF800080, layer)
        # def get_mouse_position(self) -> tuple:
        #    return self.mlx_wrapper.get_mouse_pos()
