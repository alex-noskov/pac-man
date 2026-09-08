from copy import copy
import math


class Circle:
    def __init__(
        self,
        name: str,
        xp: float = 0,
        yp: float = 0,
        radiusp: float = 0,
    ) -> None:
        self.name = name
        self.xp = xp
        self.yp = yp
        self.radiusp = radiusp

    def contains(self, px: float, py: float) -> bool:
        dx = px - self.xp
        dy = py - self.yp
        return dx * dx + dy * dy <= self.radiusp * self.radiusp


class AbsoluteCircle:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        radius: int,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius
        self.color = -1

    def contains(self, x: int, y: int) -> bool:
        dx = x - self.x
        dy = y - self.y
        return dx * dx + dy * dy <= self.radius * self.radius


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

    def contains(self, x: int, y: int) -> bool:
        return (
            self.x <= x < self.x + self.width
            and self.y <= y < self.y + self.height
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
        self._circles: dict[str, Circle] = {}

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

    def add_circle(
        self,
        xp: float = 0,
        yp: float = 0,
        radiusp: float = 0,
        name: str = "",
    ) -> None:
        if name == "":
            name = str(len(self._circles))

        self._circles[name] = Circle(
            name,
            xp,
            yp,
            radiusp,
        )

    def replace_rect(self, name: str, xp: float = 0, yp: float = 0) -> None:
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.xp = xp
        rect.yp = yp

    def replace_circle(
        self,
        name: str,
        xp: float = 0,
        yp: float = 0,
    ) -> None:
        circle = self._circles.get(name)
        if circle is None:
            return

        circle.xp = xp
        circle.yp = yp

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

    def resize_circle(
        self,
        name: str,
        radiusp: float = 0,
    ) -> None:
        circle = self._circles.get(name)
        if circle is None:
            return

        circle.radiusp = radiusp

    def change_text_rect(self, name: str, text: str) -> None:
        rect = self._rects.get(name)
        if rect is None:
            # print(f"NIGGER for {name}")
            return
        # print(f"{name} rect's text: '{rect.text}' -> '{text}'")
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

    def get_circle(self, name: str) -> Circle | None:
        circle = self._circles.get(name)
        return copy(circle) if circle is not None else None

    def get_rect_absolute(
        self,
        name: str,
        width: int,
        height: int,
        scale: int = 0,
    ) -> AbsoluteRect | None:
        rect = self._rects.get(name)
        if rect is None:
            return None

        abs_text = self._calculate_text(
            rect,
            width,
            height,
            rect.text_spacing,
            scale,
        )

        x1 = rect.xp * width / 100
        y1 = rect.yp * height / 100

        x2 = (rect.xp + rect.widthp) * width / 100
        y2 = (rect.yp + rect.heightp) * height / 100

        return AbsoluteRect(
            rect.name,
            int(math.ceil(x1)),
            int(math.ceil(y1)),
            int(math.ceil(x2 - x1)),
            int(math.ceil(y2 - y1)),
            abs_text,
        )

    def get_circle_absolute(
        self,
        name: str,
        width: int,
        height: int,
    ) -> AbsoluteCircle | None:
        circle = self._circles.get(name)
        if circle is None:
            return None

        return AbsoluteCircle(
            circle.name,
            int(math.ceil(circle.xp * width / 100)),
            int(math.ceil(circle.yp * height / 100)),
            int(math.ceil(circle.radiusp * min(width, height) / 100)),
        )

    def get_all_rects_absolute(self, width: int, height: int,
                               scale: int = 0) -> list[AbsoluteRect]:
        rects = []
        for rect in self._rects.values():
            absolute_rect = self.get_rect_absolute(
                rect.name, width, height, scale)
            if absolute_rect is not None:
                rects.append(absolute_rect)
        return rects

    def get_all_circles_absolute(
        self,
        width: int,
        height: int,
    ) -> list[AbsoluteCircle]:
        circles = []

        for circle in self._circles.values():
            absolute_circle = self.get_circle_absolute(
                circle.name,
                width,
                height,
            )

            if absolute_circle is not None:
                circles.append(absolute_circle)

        return circles

    def _calculate_text(
        self,
        rect: Rect,
        window_width: int,
        window_height: int,
        spacing: int = 1,
        scale: int = 0,
    ) -> AbsoluteText | None:
        if not rect.text:
            return None

        char_width = 5
        char_height = 8
        character_count = len(rect.text)

        text_width = (
            character_count * char_width
            + max(0, character_count - 1) * spacing
        )
        text_height = char_height

        # Rectangle in pixels.
        rect_x = rect.xp * window_width / 100
        rect_y = rect.yp * window_height / 100
        rect_width = rect.widthp * window_width / 100
        rect_height = rect.heightp * window_height / 100

        # Offsets are percentages of the rectangle.
        offset_x = rect.x_offsetp * rect_width / 100
        offset_y = rect.y_offsetp * rect_height / 100
        offset_x_rev = rect.x_offsetp_rev * rect_width / 100
        offset_y_rev = rect.y_offsetp_rev * rect_height / 100

        text_area_x = rect_x + offset_x
        text_area_y = rect_y + offset_y
        text_area_width = rect_width - offset_x - offset_x_rev
        text_area_height = rect_height - offset_y - offset_y_rev

        if text_area_width <= 0 or text_area_height <= 0:
            return None

        if scale == 0:
            scale_x = text_area_width / text_width
            scale_y = text_area_height / text_height

            # Largest integer scale that fits.
            scale = max(1, int(math.floor(min(scale_x, scale_y))))

        scaled_width = text_width * scale
        scaled_height = text_height * scale
        scaled_spacing = spacing * scale

        text_x = text_area_x + (text_area_width - scaled_width) / 2
        text_y = text_area_y + (text_area_height - scaled_height) / 2

        return AbsoluteText(
            rect.text,
            int(math.ceil(text_x)),
            int(math.ceil(text_y)),
            scaled_spacing,
            scale,
        )

    def get_all_rects(self) -> list[Rect]:
        return [copy(rect) for rect in self._rects.values()]

    def get_rect_names(self) -> list:
        return list(self._rects.keys())

    def get_circle_names(self) -> list:
        return list(self._circles.keys())

    def get_all_circles(self) -> list[Circle]:
        return [copy(circle) for circle in self._circles.values()]
