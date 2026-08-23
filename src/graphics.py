from .mlx_wrapper import MlxWrapper
from typing import Callable


class Graphics:
    def __init__(self, width: int, height: int, app_loop: Callable) -> None:
        self.mlx_wrapper = MlxWrapper(width=width,
                                      height=height,
                                      loop_callback=app_loop)

    def start(self) -> None:
        self.mlx_wrapper.start()

    def quit(self) -> None:
        self.mlx_wrapper.quit()

    # def refresh(self) -> None:
    #    self.mlx_wrapper.refresh()
