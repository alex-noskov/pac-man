from copy import copy


class Rect():
    def __init__(self, name: str, xp: int = 0, yp: int = 0,
                 widthp: int = 0, heightp: int = 0, text: str = "") -> None:
        self.name = name
        self.xp = xp
        self.yp = yp
        self.widthp = widthp
        self.heightp = heightp
        self.text = text
        self.text_scale = 1


class Layout():
    def __init__(self) -> None:
        self._rects: dict[str, Rect] = {}

    def add_rect(self, xp: int = 0, yp: int = 0,
                 widthp: int = 0, heightp: int = 0,
                 name: str = "", text: str = "") -> None:
        if name == "":
            name = str(len(self._rects))
        self._rects[name] = Rect(name, xp, yp, widthp, heightp)

    def replace_rect(self, xp: int = 0, yp: int = 0,
                     name: str = "") -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.xp = xp
        rect.yp = yp

    def resize_rect(self, widthp: int = 0, heightp: int = 0,
                    name: str = "") -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.widthp = widthp
        rect.heightp = heightp

    def change_text_rect(self, text: str, name: str = "") -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.text = text

    def center_rect_x(self, name: str) -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.xp = (100 - rect.widthp) // 2

    def center_rect_y(self, name: str) -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.yp = (100 - rect.heightp) // 2

    def get_rect(self, name: str) -> Rect | None:
        rect = self._rects.get(name)
        return copy(rect) if rect is not None else None

    def get_rect_absolute(self, name: str, width: int,
                          height: int) -> dict | None:
        rect = self._rects.get(name)
        if rect is None:
            return None
        text = self._calculate_text(rect, width, height)
        return {
            "x": rect.xp * width // 100,
            "y": rect.yp * height // 100,
            "width": rect.widthp * width // 100,
            "height": rect.heightp * height // 100,
            "text": text
        }

    def _calculate_text(
        self,
        rect: Rect,
        window_width: int,
        window_height: int,
        spacing: int = 1,
    ) -> dict | None:
        if not rect.text:
            return None

        char_width = 5
        char_height = 8

        text_width = len(rect.text) * (char_width + spacing) - spacing
        text_height = char_height

        rect_width = rect.widthp * window_width // 100
        rect_height = rect.heightp * window_height // 100

        scale_x = rect_width // text_width
        scale_y = rect_height // text_height

        scale = min(scale_x, scale_y)

        # Text must have at least scale 1.
        # If the rectangle is too small, it will overflow rather than disappear.
        scale = max(1, scale)

        scaled_width = text_width * scale
        scaled_height = text_height * scale

        rect_x = rect.xp * window_width // 100
        rect_y = rect.yp * window_height // 100

        text_x = rect_x + (rect_width - scaled_width) // 2
        text_y = rect_y + (rect_height - scaled_height) // 2

        return {
            "text": rect.text,
            "x": text_x,
            "y": text_y,
            "scale": scale,
        }

    def get_all_rects(self) -> list[Rect]:
        return [copy(rect) for rect in self._rects.values()]

    def get_rect_names(self) -> list:
        return list(self._rects.keys())
