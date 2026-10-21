import math
from collections.abc import Iterable


BLACK = 0xFF000000
WHITE = 0xFFFFFFFF
YELLOW = 0xFFFFFF00
PURPLE = 0xFF800080
BLUE = 0xFF0000FF
ORANGE = 0xFFFFA500
GREEN = 0xFF00FF00
LIGHT_GREEN = 0xFF66FF66
GRAY = 0xFF808080
PINK = 0xFFFF69B4
LIGHT_RED = 0xFFFF4444
LIGHT_PINK = 0xFFFF99CC
CYAN = 0xFF44FFFF
LIGHT_ORANGE = 0xFFFFAA44
GOLD = 0xFFFFD700
DARK_ORANGE = 0xFFFF8C00
LIGHT_GRAY = 0xFFD3D3D3

GAME_BACKGROUND = 0xFF101018
PAUSE_BACKGROUND = 0xFF000000
WALLS_COLOR = LIGHT_GRAY
COLOR_42 = PURPLE

GLYPH_WIDTH = 5
GLYPH_HEIGHT = 8


def percent_rect(
    width: int,
    height: int,
    xp: float,
    yp: float,
    widthp: float,
    heightp: float,
) -> tuple[int, int, int, int]:
    """Convert percentage geometry to an integer pixel rectangle."""
    x1 = int(round(xp * width / 100))
    y1 = int(round(yp * height / 100))
    x2 = int(round((xp + widthp) * width / 100))
    y2 = int(round((yp + heightp) * height / 100))

    return (
        x1,
        y1,
        max(1, x2 - x1),
        max(1, y2 - y1),
    )


def text_pixel_width(
    text: str,
    scale: int,
    spacing: int | None = None,
) -> int:
    """Return the exact bitmap width for text at the given scale."""
    if spacing is None:
        spacing = scale

    return (
        len(text) * GLYPH_WIDTH * scale
        + max(0, len(text) - 1) * spacing
    )


def fit_text_scale(
    text: str,
    box_width: int,
    box_height: int,
    padding_xp: float = 0,
    padding_yp: float = 0,
    spacing_units: int = 1,
) -> int:
    """Return the largest bitmap scale that fits a padded box."""
    if not text:
        return 1

    padding_x = box_width * padding_xp / 100
    padding_y = box_height * padding_yp / 100
    inner_width = max(1.0, box_width - 2 * padding_x)
    inner_height = max(1.0, box_height - 2 * padding_y)
    base_width = (
        len(text) * GLYPH_WIDTH
        + max(0, len(text) - 1) * spacing_units
    )

    width_scale = int(inner_width // max(1, base_width))
    height_scale = int(inner_height // GLYPH_HEIGHT)

    return max(1, min(width_scale, height_scale))


def fit_text_group_scale(
    texts: Iterable[str],
    box_width: int,
    box_height: int,
    padding_xp: float = 0,
    padding_yp: float = 0,
    spacing_units: int = 1,
) -> int:
    """Return one fitted scale shared by every text in a box group."""
    scales = [
        fit_text_scale(
            text,
            box_width,
            box_height,
            padding_xp,
            padding_yp,
            spacing_units,
        )
        for text in texts
        if text
    ]

    return min(scales) if scales else 1


def text_box_layout(
    text: str,
    box_x: int,
    box_y: int,
    box_width: int,
    box_height: int,
    padding_xp: float = 0,
    padding_yp: float = 0,
    spacing_units: int = 1,
    scale: int | None = None,
) -> tuple[int, int, int, int]:
    """Return centered text position, scale, and spacing for a box."""
    maximum_scale = fit_text_scale(
        text,
        box_width,
        box_height,
        padding_xp,
        padding_yp,
        spacing_units,
    )
    actual_scale = (
        maximum_scale
        if scale is None
        else max(1, min(scale, maximum_scale))
    )
    spacing = spacing_units * actual_scale
    text_width = text_pixel_width(text, actual_scale, spacing)
    text_height = GLYPH_HEIGHT * actual_scale
    x = box_x + (box_width - text_width) // 2
    y = box_y + (box_height - text_height) // 2

    return x, y, actual_scale, spacing


class AbsoluteText:
    """Store text with pixel placement, glyph scale, spacing, and color."""

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        spacing: int,
        scale: int,
    ) -> None:
        """Store text, pixel origin, character spacing, and glyph scale."""
        self.text = text
        self.x = x
        self.y = y
        self.color = -1
        self.spacing = spacing
        self.scale = scale


class AbsoluteRect:
    """Represent a named pixel rectangle with optional positioned text."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        text: AbsoluteText | None = None,
    ) -> None:
        """Store pixel bounds and optional text for the named rectangle."""
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = -1


class Rect:
    """Represent percentage bounds with text and relative text-area insets."""

    def __init__(
        self,
        name: str,
        xp: float = 0,
        yp: float = 0,
        widthp: float = 0,
        heightp: float = 0,
        text: str = "",
        text_spacing: int = 1,
        x_offsetp: float = 0,
        y_offsetp: float = 0,
        x_offsetp_rev: float = 0,
        y_offsetp_rev: float = 0,
    ) -> None:
        """Store bounds and left/top/right/bottom text-area insets.

        x_offsetp/y_offsetp are left/top; their _rev versions are right/bottom.
        Insets are percentages of this rectangle, not of the window.
        """
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


class Layout:
    """Manage named percentage rectangles and convert them to pixels."""

    def __init__(self) -> None:
        """Initialize the named menu rectangles."""
        self._rects: dict[str, Rect] = {}

    def add_rect(
        self,
        xp: float = 0,
        yp: float = 0,
        widthp: float = 0,
        heightp: float = 0,
        name: str = "",
        text: str = "",
        text_spacing: int = 1,
        x_offsetp: float = 0,
        y_offsetp: float = 0,
        x_offsetp_rev: float = 0,
        y_offsetp_rev: float = 0,
    ) -> None:
        """Register a rectangle with rectangle-relative text insets.

        x_offsetp/y_offsetp are left/top; their _rev versions are right/bottom.
        An omitted name is generated from the number of registered rectangles.
        """
        if name == "":
            name = str(len(self._rects))
        self._rects[name] = Rect(
            name=name,
            xp=xp,
            yp=yp,
            widthp=widthp,
            heightp=heightp,
            text=text,
            text_spacing=text_spacing,
            x_offsetp=x_offsetp,
            y_offsetp=y_offsetp,
            x_offsetp_rev=x_offsetp_rev,
            y_offsetp_rev=y_offsetp_rev,
        )

    def center_rect_x(
        self,
        name: str,
    ) -> None:
        """Center the named rectangle horizontally in percentage space."""
        rect = self._rects.get(name)
        if rect is None:
            return
        rect.xp = (100 - rect.widthp) / 2

    def get_rect_absolute(
        self,
        name: str,
        width: int,
        height: int,
        scale: int = 0,
    ) -> AbsoluteRect | None:
        """Return pixel bounds and fitted text for a named rectangle."""
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
        x, y, rect_width, rect_height = percent_rect(
            width,
            height,
            rect.xp,
            rect.yp,
            rect.widthp,
            rect.heightp,
        )

        return AbsoluteRect(
            rect.name,
            x,
            y,
            rect_width,
            rect_height,
            abs_text,
        )

    def get_shared_text_scale(
        self,
        names: Iterable[str],
        width: int,
        height: int,
    ) -> int:
        """Return one auto-fitted scale shared by named layout rectangles."""
        scales: list[int] = []

        for name in names:
            rect = self._rects.get(name)
            if rect is None or not rect.text:
                continue
            text = self._calculate_text(
                rect,
                width,
                height,
                rect.text_spacing,
                0,
            )
            if text is not None:
                scales.append(text.scale)

        return min(scales) if scales else 1

    def _calculate_text(
        self,
        rect: Rect,
        window_width: int,
        window_height: int,
        spacing: int = 1,
        scale: int = 0,
    ) -> AbsoluteText | None:
        """Return centered fitted text, or None for empty text or area."""
        if not rect.text:
            return None

        rect_x, rect_y, rect_width, rect_height = percent_rect(
            window_width,
            window_height,
            rect.xp,
            rect.yp,
            rect.widthp,
            rect.heightp,
        )

        left_inset = rect.x_offsetp * rect_width / 100
        top_inset = rect.y_offsetp * rect_height / 100
        right_inset = rect.x_offsetp_rev * rect_width / 100
        bottom_inset = rect.y_offsetp_rev * rect_height / 100
        text_area_width = rect_width - left_inset - right_inset
        text_area_height = rect_height - top_inset - bottom_inset

        if text_area_width <= 0 or text_area_height <= 0:
            return None

        base_width = (
            len(rect.text) * GLYPH_WIDTH
            + max(0, len(rect.text) - 1) * spacing
        )
        scale_x = text_area_width / max(1, base_width)
        scale_y = text_area_height / GLYPH_HEIGHT
        maximum_scale = max(
            1,
            int(math.floor(min(scale_x, scale_y))),
        )
        actual_scale = (
            maximum_scale
            if scale == 0
            else max(1, min(scale, maximum_scale))
        )
        scaled_spacing = spacing * actual_scale
        scaled_width = text_pixel_width(
            rect.text,
            actual_scale,
            scaled_spacing,
        )
        scaled_height = GLYPH_HEIGHT * actual_scale
        text_area_x = rect_x + left_inset
        text_area_y = rect_y + top_inset
        text_x = text_area_x + (text_area_width - scaled_width) / 2
        text_y = text_area_y + (text_area_height - scaled_height) / 2

        return AbsoluteText(
            rect.text,
            int(math.ceil(text_x)),
            int(math.ceil(text_y)),
            scaled_spacing,
            actual_scale,
        )

    def get_rect_names(self) -> list[str]:
        """Return registered rectangle names in insertion order."""
        return list(self._rects.keys())
