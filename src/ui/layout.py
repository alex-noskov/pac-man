import math


BLACK = 0xFF000000
WHITE = 0xFFFFFFFF
RED = 0xFFFF0000
YELLOW = 0xFFFFFF00
PURPLE = 0xFF800080
BLUE = 0xFF0000FF
ORANGE = 0xFFFFA500
GREEN = 0xFF00FF00
LIGHT_GREEN = 0xFF66FF66
GRAY = 0xFF808080
PINK = 0xFFFF69B4
TRANSPARENT = 0x00000000
LIGHT_RED = 0xFFFF4444
LIGHT_PINK = 0xFFFF99CC
CYAN = 0xFF44FFFF
LIGHT_ORANGE = 0xFFFFAA44
NAVY = 0xFF000080
TEAL = 0xFF008080
DARK_RED = 0xFF8B0000
GOLD = 0xFFFFD700
GREEN = 0xFF00FF00
DARK_ORANGE = 0xFFFF8C00
LIGHT_GRAY = 0xFFD3D3D3

GAME_BACKGROUND = 0xFF101018
PAUSE_BACKGROUND = 0xFF000000
WALLS_COLOR = LIGHT_GRAY
COLOR_42 = PURPLE

# Fixed bitmap magnification: base glyphs are 5 pixels wide, 8 high.
NORMAL_TEXT_SCALE = 2
TITLE_TEXT_SCALE = 3
HUD_TEXT_SCALE = 2

AUTO_CONTINUE_DELAY = 3.0


def responsive_scale(
    width: int,
    height: int,
    base_scale: int,
) -> int:
    """Scale text smoothly from the 1280x800 reference window."""
    width_ratio = width / 1280
    height_ratio = height / 800
    ratio = min(width_ratio, height_ratio)

    return max(
        base_scale,
        int(base_scale * ratio + 0.5),
    )


def responsive_px(
    width: int,
    height: int,
    value: int,
) -> int:
    """Scale a pixel value proportionally from the 1280x800 reference."""
    width_ratio = width / 1280
    height_ratio = height / 800
    ratio = min(width_ratio, height_ratio)

    return max(1, int(value * ratio + 0.5))


def text_pixel_width(
    text: str,
    scale: int,
    spacing: int | None = None,
) -> int:
    """Return the exact bitmap width for text at the given scale."""
    if spacing is None:
        spacing = scale

    return (
        len(text) * 5 * scale
        + max(0, len(text) - 1) * spacing
    )


def fit_text_scale(
    text: str,
    box_width: int,
    box_height: int,
    preferred_scale: int,
    padding_x: int = 0,
    padding_y: int = 0,
    spacing_units: int = 1,
) -> int:
    """Return a scale that fits text inside a padded pixel box."""
    inner_width = max(1, box_width - 2 * padding_x)
    inner_height = max(1, box_height - 2 * padding_y)
    base_width = (
        len(text) * 5
        + max(0, len(text) - 1) * spacing_units
    )

    if not text:
        return max(1, preferred_scale)

    width_scale = inner_width // max(1, base_width)
    height_scale = inner_height // 8
    maximum = max(1, min(width_scale, height_scale))

    return max(1, min(preferred_scale, maximum))


def text_box_layout(
    text: str,
    box_x: int,
    box_y: int,
    box_width: int,
    box_height: int,
    preferred_scale: int,
    padding_x: int = 0,
    padding_y: int = 0,
    spacing_units: int = 1,
) -> tuple[int, int, int, int]:
    """Return centered text x/y, scale, and spacing for a pixel box."""
    scale = fit_text_scale(
        text,
        box_width,
        box_height,
        preferred_scale,
        padding_x,
        padding_y,
        spacing_units,
    )
    spacing = spacing_units * scale
    text_width = text_pixel_width(text, scale, spacing)
    text_height = 8 * scale
    x = box_x + (box_width - text_width) // 2
    y = box_y + (box_height - text_height) // 2

    return x, y, scale, spacing


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
        """Return pixel bounds and scaled text, or None for an unknown name."""
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

    def _calculate_text(
        self,
        rect: Rect,
        window_width: int,
        window_height: int,
        spacing: int = 1,
        scale: int = 0,
    ) -> AbsoluteText | None:
        """Return centered scaled text, or None for empty text or area."""
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
        left_inset = rect.x_offsetp * rect_width / 100
        top_inset = rect.y_offsetp * rect_height / 100
        right_inset = rect.x_offsetp_rev * rect_width / 100
        bottom_inset = rect.y_offsetp_rev * rect_height / 100

        text_area_x = rect_x + left_inset
        text_area_y = rect_y + top_inset
        text_area_width = rect_width - left_inset - right_inset
        text_area_height = rect_height - top_inset - bottom_inset

        if text_area_width <= 0 or text_area_height <= 0:
            return None

        scale_x = text_area_width / text_width
        scale_y = text_area_height / text_height
        maximum_scale = max(
            1,
            int(math.floor(min(scale_x, scale_y))),
        )

        if scale == 0:
            scale = maximum_scale
        else:
            scale = max(1, min(scale, maximum_scale))

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

    def get_rect_names(self) -> list[str]:
        """Return registered rectangle names in insertion order."""
        return list(self._rects.keys())
