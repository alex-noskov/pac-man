# X11 event types used by MLX 2.2.
#
# These values come from the X11/XCB protocol.

KEY_PRESS = 2
KEY_RELEASE = 3

BUTTON_PRESS = 4
BUTTON_RELEASE = 5

MOTION_NOTIFY = 6

EXPOSE = 12

DESTROY_NOTIFY = 17

CLIENT_MESSAGE = 33


# X11 event masks.
#
# These are bit masks used with mlx_hook().
KEY_PRESS_MASK = 1
KEY_RELEASE_MASK = 2
