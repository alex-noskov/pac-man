from mlx import Mlx
from .mlx_constants import CLIENT_MESSAGE  # , MOTION_NOTIFY
from .mlx_keycodes import KEY_ENTER, KEY_UP, KEY_DOWN, KEY_ESC
# from .mlx_masks import POINTER_MOTION_MASK
from typing import Callable
from collections import deque
from ..events import EventFactory  # , EventType


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
            self.mlx_ptr,
            width,
            height,
            "Pac-Man",
        )
        if not self.window:
            self.mlx.mlx_release(self.mlx_ptr)
            raise RuntimeError("MLX window creation failed")

        self.image = self.mlx.mlx_new_image(self.mlx_ptr, width, height)
        if not self.image:
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.window)
            self.mlx.mlx_release(self.mlx_ptr)
            raise RuntimeError("MLX image creation failed")
        (
            self.image_data,
            self.bits_per_pixel,
            self.line_length,
            self.endian,
        ) = self.mlx.mlx_get_data_addr(self.image)
        self.bytes_per_pixel = self.bits_per_pixel // 8

        # self.mouse_x = 0
        # self.mouse_y = 0
        # self.mouse_moved = False

        self._loop_callback = loop_callback
        self._event_buffer: deque = deque()

    def mouse_press(self, button, x, y, xvar) -> None:
        # print("MOUSE PRESSED!!!")
        # print(button)
        # print(f"({x},{y})")
        # print(xvar)
        self._event_buffer.append(EventFactory.mouse_down(x, y, button))

    def mouse_move(self, x, y, xvar) -> None:
        pass
        # if self._event_buffer:
        #    last_event = self._event_buffer[-1]

        #    if last_event.type == EventType.MOUSE_MOVE:
        #        self._event_buffer[-1] = EventFactory.mouse_move(x, y)
        #        return

        # self._event_buffer.append(EventFactory.mouse_move(x, y))

        # self.mouse_x = x
        # self.mouse_y = y

        # self.mouse_moved = True
        # pass

    def key_pressed(self, keycode: int, xvar) -> None:
        print(f"key: {keycode}")

        # self._event_buffer.append(keycode)

        # if keycode == KEY_ESC:  # Escape
        #    self.stop_loop()
        if keycode == KEY_UP:
            self._event_buffer.append(EventFactory.key_up())
        elif keycode == KEY_DOWN:
            self._event_buffer.append(EventFactory.key_down())
        elif keycode == KEY_ENTER:
            self._event_buffer.append(EventFactory.key_enter())
        elif keycode == KEY_ESC:
            self._event_buffer.append(EventFactory.key_esc())

    def window_closed(self, xvar) -> None:
        print("WINDOW CLOSED")
        print(xvar)
        self.stop_loop()
        # self._event_buffer.appendleft(EventFactory.close())

    def loop(self, xvar) -> None:
        # if self.mouse_moved:
        #    self._event_buffer.append(
        #        EventFactory.mouse_move(self.mouse_x, self.mouse_y)
        #    )
        #    self.mouse_moved = False
        self._loop_callback(self._event_buffer)

    def start(self) -> None:
        # handle mouse button press
        # self.mlx.mlx_mouse_hook(self.window, self.mouse_press, None)
        # handle keyboard pressed
        self.mlx.mlx_key_hook(self.window, self.key_pressed, None)
        # handle window "x" click
        self.mlx.mlx_hook(self.window, CLIENT_MESSAGE,
                          0, self.window_closed, None)
        # handle mouse motion
        # self.mlx.mlx_hook(self.window, MOTION_NOTIFY,
        #                  POINTER_MOTION_MASK,
        #                  self.mouse_move, None)
        # handle mlx loop iteration
        self.mlx.mlx_loop_hook(self.mlx_ptr, self.loop, None)
        self.mlx.mlx_loop(self.mlx_ptr)

    def stop_loop(self) -> None:
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def quit(self) -> None:
        self.mlx.mlx_destroy_window(
            self.mlx_ptr,
            self.window,
        )
        self.mlx.mlx_release(self.mlx_ptr)

    def refresh(self) -> None:
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.window,
            self.image, 0, 0)

    def clear(self, color: int) -> None:
        pixel = bytes((
            color & 0xFF,
            (color >> 8) & 0xFF,
            (color >> 16) & 0xFF,
            (color >> 24) & 0xFF,
        ))
        self.image_data[:] = pixel * (self.width * self.height)

    def put_pixel(self, x: int, y: int, color: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        offset = (
            y * self.line_length
            + x * self.bytes_per_pixel
        )

        self.image_data[offset] = color & 0xFF
        self.image_data[offset + 1] = (color >> 8) & 0xFF
        self.image_data[offset + 2] = (color >> 16) & 0xFF
        self.image_data[offset + 3] = (color >> 24) & 0xFF

    def put_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
    ) -> None:
        for py in range(y, y + height):
            for px in range(x, x + width):
                self.put_pixel(px, py, color)

    def get_mouse_pos(self) -> tuple:
        return self.mlx.mlx_mouse_get_pos(self.mlx_ptr, self.window)
