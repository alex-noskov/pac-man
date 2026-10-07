import math

BLACK = 0xFF000000
WHITE = 0xFFFFFFFF
RED = 0xFFFF0000
YELLOW = 0xFFFFFF00
PURPLE = 0xFF800080
BLUE = 0xFF0000FF
ORANGE = 0xFFFFA500
GREEN = 0xFF00FF00
PINK = 0xFFFF69B4
TRANSPARENT = 0x00000000

# Fixed bitmap magnification: base glyphs are 5 pixels wide, 8 high.
NORMAL_TEXT_SCALE = 2
TITLE_TEXT_SCALE = 3
HUD_TEXT_SCALE = 2


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


class Rect():
    """Represent percentage bounds with text and relative text-area insets."""

    def __init__(self, name: str, xp: float = 0, yp: float = 0,
                 widthp: float = 0, heightp: float = 0, text: str = "",
                 text_spacing: int = 1,
                 x_offsetp: float = 0, y_offsetp: float = 0,
                 x_offsetp_rev: float = 0, y_offsetp_rev: float = 0) -> None:
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


class Layout():
    """Manage named percentage rectangles and convert them to pixels."""

    def __init__(self) -> None:
        """Initialize the named menu rectangles."""
        self._rects: dict[str, Rect] = {}

    def add_rect(self, xp: float = 0, yp: float = 0,
                 widthp: float = 0, heightp: float = 0,
                 name: str = "", text: str = "",
                 text_spacing: int = 1,
                 x_offsetp: float = 0, y_offsetp: float = 0,
                 x_offsetp_rev: float = 0, y_offsetp_rev: float = 0) -> None:
        """Register a rectangle with rectangle-relative text insets.

        x_offsetp/y_offsetp are left/top; their _rev versions are right/bottom.
        An omitted name is generated from the number of registered rectangles.
        """
        if name == "":
            name = str(len(self._rects))
        self._rects[name] = Rect(
            name=name, xp=xp, yp=yp, widthp=widthp, heightp=heightp,
            text=text, text_spacing=text_spacing,
            x_offsetp=x_offsetp, y_offsetp=y_offsetp,
            x_offsetp_rev=x_offsetp_rev, y_offsetp_rev=y_offsetp_rev)

    def center_rect_x(self, name: str) -> None:
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

    def get_rect_names(self) -> list[str]:
        """Return registered rectangle names in insertion order."""
        return list(self._rects.keys())
