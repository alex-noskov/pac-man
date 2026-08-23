from mlx import Mlx
from .mlx_constants import CLIENT_MESSAGE
from .mlx_keycodes import KEY_ESC
from typing import Callable


class MlxWrapper:
    def __init__(self, width: int, height: int,
                 loop_callback: Callable) -> None:
        self.mlx = Mlx()

        self.mlx_ptr = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise RuntimeError("MLX initialization failed")

        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr,
            width,
            height,
            "Pac-Man",
        )
        if not self.window:
            self.mlx.mlx_release(self.mlx_ptr)
            raise RuntimeError("MLX window creation failed")
        self._loop_callback = loop_callback

    def loop(self, _: object) -> None:
        self._loop_callback()

    def key_pressed(self, keycode: int, _: object) -> None:
        print(f"key: {keycode}")

        if keycode == KEY_ESC:  # Escape
            self.mlx.mlx_loop_exit(self.mlx_ptr)

    def window_closed(self, _) -> None:
        print("WINDOW CLOSED")
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def start(self) -> None:
        self.mlx.mlx_key_hook(self.window, self.key_pressed, None)
        self.mlx.mlx_hook(self.window, CLIENT_MESSAGE,
                          0, self.window_closed, None)
        self.mlx.mlx_loop_hook(self.mlx_ptr, self.loop, None)
        self.mlx.mlx_loop(self.mlx_ptr)

    def quit(self) -> None:
        self.mlx.mlx_destroy_window(
            self.mlx_ptr,
            self.window,
        )
        self.mlx.mlx_release(self.mlx_ptr)
