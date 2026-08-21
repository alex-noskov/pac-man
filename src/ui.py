from copy import copy


class AbsoluteText:
    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        spacing: int,
        scale: int,
    ) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.spacing = spacing
        self.scale = scale
        self.color = -1


class AbsoluteRect:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        text: AbsoluteText | None = None,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = -1

    def contains(self, px: int, py: int) -> bool:
        return (
            self.x <= px <= self.x + self.width
            and self.y <= py <= self.y + self.height
        )


class Rect():
    def __init__(self, name: str, xp: float = 0, yp: float = 0,
                 widthp: float = 0, heightp: float = 0, text: str = "",
                 text_spacing: int = 1) -> None:
        self.name = name
        self.xp = xp
        self.yp = yp
        self.widthp = widthp
        self.heightp = heightp
        self.text = text
        self.text_spacing = text_spacing


class Layout():
    def __init__(self) -> None:
        self._rects: dict[str, Rect] = {}

    def add_rect(self, xp: float = 0, yp: float = 0,
                 widthp: float = 0, heightp: float = 0,
                 name: str = "", text: str = "",
                 text_spacing: int = 1) -> None:
        if name == "":
            name = str(len(self._rects))
        self._rects[name] = Rect(name, xp, yp, widthp,
                                 heightp, text, text_spacing)

    def replace_rect(self, xp: float = 0, yp: float = 0,
                     name: str = "") -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.xp = xp
        rect.yp = yp

    def resize_rect(self, widthp: float = 0, heightp: float = 0,
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
        rect.xp = (100 - rect.widthp) / 2

    def center_rect_y(self, name: str) -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.yp = (100 - rect.heightp) / 2

    def get_rect(self, name: str) -> Rect | None:
        rect = self._rects.get(name)
        return copy(rect) if rect is not None else None

    def get_rect_absolute(self, name: str, width: int,
                          height: int) -> AbsoluteRect | None:
        rect = self._rects.get(name)
        if rect is None:
            return None
        abs_text = self._calculate_text(rect, width, height, rect.text_spacing)
        return AbsoluteRect(rect.name,
                            int(rect.xp * width / 100),
                            int(rect.yp * height / 100),
                            int(rect.widthp * width / 100),
                            int(rect.heightp * height / 100),
                            abs_text)

    def get_all_rects_absolute(self, width: int,
                               height: int) -> list[AbsoluteRect]:
        rects = []
        for rect in self._rects.values():
            absolute_rect = self.get_rect_absolute(rect.name, width, height)
            if absolute_rect is not None:
                rects.append(absolute_rect)
        return rects

    def _calculate_text(
        self,
        rect: Rect,
        window_width: int,
        window_height: int,
        spacing: int = 1,
    ) -> AbsoluteText | None:
        if not rect.text:
            return None

        char_width = 5
        char_height = 8

        text_width = len(rect.text) * (char_width + spacing) - spacing
        text_height = char_height

        rect_width = rect.widthp * window_width / 100
        rect_height = rect.heightp * window_height / 100

        scale_x = rect_width / text_width
        scale_y = rect_height / text_height

        scale = min(scale_x, scale_y)

        # Text must have at least scale 1.
        # If the rectangle is too small, it will overflow and not disappear.
        scale = max(1, scale)

        scaled_width = text_width * scale
        scaled_height = text_height * scale
        scaled_spacing = spacing * scale

        rect_x = rect.xp * window_width / 100
        rect_y = rect.yp * window_height / 100

        text_x = rect_x + (rect_width - scaled_width) / 2
        text_y = rect_y + (rect_height - scaled_height) / 2

        return AbsoluteText(rect.text, int(text_x), int(text_y),
                            int(scaled_spacing), int(scale))

    def get_all_rects(self) -> list[Rect]:
        return [copy(rect) for rect in self._rects.values()]

    def get_rect_names(self) -> list:
        return list(self._rects.keys())
