import pygame
from .src.colors import TRANSPARENT, BLACK
from .src.font_map import FONT_MAP


class Image:
    """Store an image as a mutable matrix of packed pixel colors."""

    def __init__(self, width: int, height: int) -> None:
        """Allocate a transparent pixel matrix with the given dimensions."""
        self.width = width
        self.height = height
        self.matrix = [[TRANSPARENT for _ in range(0, self.width)]
                       for _ in range(0, self.height)]

    def set_pixel(self, x: int, y: int, color: int) -> None:
        """Set the pixel color, ignoring coordinates outside the image."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        self.matrix[y][x] = color


class Graphics:
    """Handle the game's graphical window."""

    def __init__(self, width: int, height: int) -> None:
        """Create the game window."""
        pygame.init()

        self.window = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Pac-Man")

    def get_events(self) -> list[pygame.event.Event]:
        """Return the events currently in the event queue."""
        return pygame.event.get()

    def create_image(self, width: int, height: int) -> Image:
        """Return a transparent image with the requested pixel dimensions."""
        return Image(width=width, height=height)

    def put_image(self, image: Image, x: int, y: int,
                  background_color: int = BLACK) -> None:
        """Blit the image using background_color for transparent pixels."""
        surface = pygame.Surface((image.width, image.height))
        for iy in range(image.height):
            for ix in range(image.width):
                color = image.matrix[iy][ix]
                if color == TRANSPARENT:
                    color = background_color
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
                surface.set_at((ix, iy), (r, g, b))
        self.window.blit(surface, (x, y))

    def clear(self, color: int) -> None:
        """Fill the window with the RGB channels of the packed color."""
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        self.window.fill((r, g, b))

    def draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
    ) -> None:
        """Draw a filled rectangle with the given pixel bounds and color."""
        rect_image = self.create_image(width=width, height=height)
        for iy in range(rect_image.height):
            for ix in range(rect_image.width):
                rect_image.set_pixel(x=ix, y=iy, color=color)
        self.put_image(image=rect_image, x=x, y=y)

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: int,
        background_color: int,
        spacing: int = 1,
        scale: int = 1
    ) -> None:
        """Blit scaled bitmap text with pixel spacing and background color."""
        char_width = 5
        char_height = 8

        char_width *= scale
        char_height *= scale

        image_width = len(text) * (char_width + spacing) - spacing
        image = self.create_image(width=image_width, height=char_height)
        for char_index, char in enumerate(text):
            bitmap = FONT_MAP.get(char)
            if bitmap is None:
                continue
            offset_x = char_index * (char_width + spacing)
            for iy, row in enumerate(bitmap):
                for ix, pixel in enumerate(row):
                    if pixel != "1":
                        continue
                    for dy in range(scale):
                        for dx in range(scale):
                            image.set_pixel(
                                x=offset_x + ix * scale + dx,
                                y=iy * scale + dy,
                                color=color,
                            )
        self.put_image(image=image, x=x, y=y,
                       background_color=background_color)

    def get_window_size(self) -> tuple[int, int]:
        """Return the current window width and height."""
        return self.window.get_size()

    def refresh(self) -> None:
        """Present the current window contents by flipping the display."""
        pygame.display.flip()

    def quit(self) -> None:
        """Shut down the initialized Pygame modules."""
        pygame.quit()
