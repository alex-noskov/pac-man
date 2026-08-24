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
        self.color = -1
        self.spacing = spacing
        self.scale = scale


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
                 text_spacing: int = 1,
                 x_offsetp: float = 0, y_offsetp: float = 0,
                 x_offsetp_rev: float = 0, y_offsetp_rev: float = 0) -> None:
        self.name = name
        self.xp = xp
        self.yp = yp
        self.widthp = widthp
        self.heightp = heightp
        self.text = text
        self.text_spacing = text_spacing
        self.x_offsetp = x_offsetp
        self.y_offsetp = y_offsetp
        self.x_offsetp_rev = x_offsetp_rev
        self.y_offsetp_rev = y_offsetp_rev


class Layout():
    def __init__(self) -> None:
        self._rects: dict[str, Rect] = {}

    def add_rect(self, xp: float = 0, yp: float = 0,
                 widthp: float = 0, heightp: float = 0,
                 name: str = "", text: str = "",
                 text_spacing: int = 1,
                 x_offsetp: float = 0, y_offsetp: float = 0,
                 x_offsetp_rev: float = 0, y_offsetp_rev: float = 0) -> None:
        if name == "":
            name = str(len(self._rects))
        self._rects[name] = Rect(name, xp, yp, widthp,
                                 heightp, text, text_spacing,
                                 x_offsetp, y_offsetp,
                                 x_offsetp_rev, y_offsetp_rev)

    def replace_rect(self, name: str, xp: float = 0, yp: float = 0) -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.xp = xp
        rect.yp = yp

    def resize_rect(self, name: str, widthp: float = 0, heightp: float = 0,
                    x_offsetp: float = 0, y_offsetp: float = 0,
                    x_offsetp_rev: float = 0,
                    y_offsetp_rev: float = 0) -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.widthp = widthp
        rect.heightp = heightp
        rect.x_offsetp = x_offsetp
        rect.y_offsetp = y_offsetp
        rect.x_offsetp_rev = x_offsetp_rev
        rect.y_offsetp_rev = y_offsetp_rev

    def change_text_rect(self, text: str, name: str) -> None:
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
                          height: int, scale: int = 0) -> AbsoluteRect | None:
        rect = self._rects.get(name)
        if rect is None:
            return None
        abs_text = self._calculate_text(
            rect, width, height, rect.text_spacing, scale)
        return AbsoluteRect(rect.name,
                            int(rect.xp * width / 100),
                            int(rect.yp * height / 100),
                            int(rect.widthp * width / 100),
                            int(rect.heightp * height / 100),
                            abs_text)

    def get_all_rects_absolute(self, width: int, height: int,
                               scale: int = 0) -> list[AbsoluteRect]:
        rects = []
        for rect in self._rects.values():
            absolute_rect = self.get_rect_absolute(
                rect.name, width, height, scale)
            if absolute_rect is not None:
                rects.append(absolute_rect)
        return rects

    def _calculate_text(
        self,
        rect: Rect,
        window_width: int,
        window_height: int,
        spacing: int = 1,
        scale: int = 0
    ) -> AbsoluteText | None:
        if not rect.text:
            return None

        char_width = 5
        char_height = 8

        character_count = len(rect.text)

        # Calculate the unscaled text dimensions.
        # There is no spacing after the last character.
        text_width = (
            character_count * char_width
            + (character_count - 1) * spacing
        )
        text_height = char_height

        # Convert the rectangle from percentages to pixels.
        rect_x = rect.xp * window_width / 100
        rect_y = rect.yp * window_height / 100
        rect_width = rect.widthp * window_width / 100
        rect_height = rect.heightp * window_height / 100

        # Offsets are percentages of the rectangle, not the window.
        offset_x = rect.x_offsetp * rect_width / 100
        offset_y = rect.y_offsetp * rect_height / 100
        offset_x_rev = rect.x_offsetp_rev * rect_width / 100
        offset_y_rev = rect.y_offsetp_rev * rect_height / 100

        # The offsets move the usable text area and therefore affect
        # the amount of space available for scaling the text.
        text_area_x = rect_x + offset_x
        text_area_y = rect_y + offset_y
        text_area_width = rect_width - offset_x - offset_x_rev
        text_area_height = rect_height - offset_y - offset_y_rev

        if scale == 0:
            scale_x = text_area_width / text_width
            scale_y = text_area_height / text_height

            scale = max(1, int(min(scale_x, scale_y)))

        scaled_width = text_width * scale
        scaled_height = text_height * scale
        scaled_spacing = spacing * scale

        # Center the scaled text inside the offset text area.
        text_x = text_area_x + (text_area_width - scaled_width) / 2
        text_y = text_area_y + (text_area_height - scaled_height) / 2

        return AbsoluteText(rect.text, int(text_x), int(text_y),
                            scaled_spacing, scale)

    def get_all_rects(self) -> list[Rect]:
        return [copy(rect) for rect in self._rects.values()]

    def get_rect_names(self) -> list:
        return list(self._rects.keys())
