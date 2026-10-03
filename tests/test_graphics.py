"""Headless MLX contracts using the vendor's 32-bit opacity formats."""
from collections import deque
from typing import Callable, Literal
import unittest
from unittest.mock import patch

from src.events import Event, EventType
from src.mlx_wrapper.mlx_wrapper import ImageLayer, MlxWrapper


class FakeMlx:
    """Memory-backed native boundary with source-over rendering."""

    def __init__(self, *, stride: int = 12, endian: int = 0) -> None:
        self.stride = stride
        self.endian = endian
        self.images: dict[int, bytearray] = {}
        self.destroyed: list[int] = []
        self.calls: list[str] = []
        self.next_image = 0
        self.screen = [0, 0, 0, 0]
        self.loop_callback: Callable[[object], None] | None = None

    def mlx_init(self) -> int:
        return 1

    def mlx_get_screen_size(self, ptr: object) -> tuple[int, int, int]:
        """Expose a finite display so window fitting can be tested."""
        return 0, 1024, 768

    def mlx_new_window(self, *args: object) -> int:
        return 2

    def mlx_new_image(self, ptr: object, w: int, h: int) -> int:
        self.next_image += 1
        self.images[self.next_image] = bytearray(
            [127] * (self.stride * h))
        return self.next_image

    def mlx_get_data_addr(
        self, image: int,
    ) -> tuple[memoryview, int, int, int]:
        return memoryview(self.images[image]), 32, self.stride, self.endian

    def mlx_destroy_image(self, ptr: object, image: int) -> None:
        self.destroyed.append(image)
        del self.images[image]
        self.calls.append("image")

    def mlx_destroy_window(self, *args: object) -> None:
        self.calls.append("window")

    def mlx_release(self, ptr: object) -> None:
        self.calls.append("release")

    def mlx_loop_exit(self, ptr: object) -> None:
        self.calls.append("exit")

    def mlx_key_hook(self, *args: object) -> None:
        pass

    def mlx_mouse_hook(self, *args: object) -> None:
        pass

    def mlx_hook(self, *args: object) -> None:
        pass

    def mlx_loop_hook(self, ptr: object,
                      callback: Callable[[object], None],
                      param: object) -> None:
        self.loop_callback = callback

    def mlx_loop(self, ptr: object) -> None:
        if self.loop_callback is not None:
            self.loop_callback(None)

    def mlx_put_image_to_window(self, ptr: object, win: object,
                                image: int, x: int, y: int) -> None:
        data = self.images[image]
        order: Literal["little", "big"] = (
            "little" if self.endian == 0 else "big")
        for py in range(2):
            for px in range(2):
                offset = py * self.stride + px * 4
                color = int.from_bytes(data[offset:offset + 4], order)
                alpha = color >> 24
                old = self.screen[py * 2 + px]
                result = 0xFF000000
                for shift in (0, 8, 16):
                    channel = (((color >> shift) & 255) * alpha
                               + ((old >> shift) & 255) * (255 - alpha))
                    result |= ((channel + 127) // 255) << shift
                self.screen[py * 2 + px] = result


def make_wrapper(native: FakeMlx,
                 callback: Callable[[deque[Event]], None] = lambda _: None
                 ) -> MlxWrapper:
    with patch("src.mlx_wrapper.mlx_wrapper.Mlx", return_value=native):
        return MlxWrapper(2, 2, callback)


class ImageTests(unittest.TestCase):
    def test_fill_respects_stride_and_format(self) -> None:
        for endian, pixel in ((0, b"\x33\x22\x11\xff"),
                              (1, b"\xff\x11\x22\x33")):
            with self.subTest(endian=endian):
                native = FakeMlx(endian=endian)
                layer = ImageLayer(native, 1, 2, 2)
                layer.fill(0xFF112233)
                self.assertEqual(bytes(layer.data[:8]), pixel * 2)
                self.assertEqual(bytes(layer.data[12:20]), pixel * 2)
                self.assertEqual(len(layer.data), 24)
                layer.put_pixel(1, 1, 0x80112233)
                self.assertEqual(bytes(layer.data[16:20]),
                                 (0x80112233).to_bytes(
                                     4, "little" if endian == 0 else "big"))

    def test_new_layer_and_clear_are_transparent(self) -> None:
        layer = ImageLayer(FakeMlx(), 1, 2, 2)
        self.assertEqual(bytes(layer.data), bytes(24))
        layer.fill(0xFFFFFFFF)
        layer.clear()
        self.assertEqual(bytes(layer.data), bytes(24))

    def test_pixels_and_rectangles_clip_to_surface(self) -> None:
        layer = ImageLayer(FakeMlx(), 1, 2, 2)
        layer.clear()
        layer.put_rectangle(-1, -1, 2, 2, 0xFFFFFFFF)
        layer.put_pixel(2, 1, 0xFFFFFFFF)
        self.assertEqual(bytes(layer.data[:4]), b"\xff" * 4)
        self.assertEqual(bytes(layer.data[4:]), bytes(20))


class ResourceTests(unittest.TestCase):
    def test_oversized_window_is_fitted_to_the_display(self) -> None:
        """All menu items and maze cells must fit on the actual monitor."""
        native = FakeMlx(stride=4000)
        with patch('src.mlx_wrapper.mlx_wrapper.Mlx', return_value=native):
            wrapper = MlxWrapper(900, 2000, lambda _: None)
        self.assertEqual((wrapper.width, wrapper.height), (900, 704))
        self.assertEqual(wrapper.get_layer('main').height, 704)
        wrapper.quit()

    def test_removal_and_quit_destroy_every_image_once_in_order(self) -> None:
        native = FakeMlx()
        wrapper = make_wrapper(native)
        wrapper.create_layer("actor")
        actor = wrapper.get_layer("actor")
        actor_image = actor.image
        wrapper.remove_layer("actor")
        self.assertEqual(native.destroyed, [actor_image])
        wrapper.remove_layer("actor")
        wrapper.stop_loop()
        wrapper.stop_loop()
        wrapper.quit()
        wrapper.quit()
        wrapper.stop_loop()
        self.assertFalse(native.images)
        self.assertEqual(len(set(native.destroyed)), 3)
        self.assertEqual(native.calls.count("exit"), 1)
        self.assertEqual(native.calls[-2:], ["window", "release"])
        with self.assertRaises(RuntimeError):
            actor.put_pixel(0, 0, 0xFFFFFFFF)
        with self.assertRaises(RuntimeError):
            wrapper.create_layer("late")

    def test_layer_omitted_from_order_can_be_removed(self) -> None:
        native = FakeMlx()
        wrapper = make_wrapper(native)
        wrapper.create_layer("hidden")
        wrapper.set_layer_order(["main"])
        wrapper.remove_layer("hidden")
        self.assertFalse(wrapper.has_layer("hidden"))

    def test_partial_initialization_releases_successful_resources(
        self,
    ) -> None:
        for fail_at in (1, 2):
            with self.subTest(fail_at=fail_at):
                native = FakeMlx()
                original = native.mlx_new_image

                def allocate(ptr: object, w: int, h: int) -> int:
                    if native.next_image + 1 == fail_at:
                        return 0
                    return original(ptr, w, h)

                with patch.object(native, "mlx_new_image", allocate):
                    with self.assertRaisesRegex(RuntimeError, "image"):
                        make_wrapper(native)
                self.assertFalse(native.images)
                self.assertEqual(native.calls[-2:], ["window", "release"])

    def test_bad_image_layout_is_destroyed(self) -> None:
        for bpp, stride, fmt in ((24, 12, 0), (32, 4, 0),
                                 (32, 12, 2), (32, 100, 0)):
            with self.subTest(layout=(bpp, stride, fmt)):
                native = FakeMlx()
                with patch.object(native, "mlx_get_data_addr",
                                  return_value=(memoryview(bytearray(24)),
                                                bpp, stride, fmt)):
                    with self.assertRaises(RuntimeError):
                        ImageLayer(native, 1, 2, 2)
                self.assertFalse(native.images)

    def test_get_data_failure_destroys_allocated_image(self) -> None:
        native = FakeMlx()
        with patch.object(native, "mlx_get_data_addr",
                          side_effect=RuntimeError("bad data")):
            with self.assertRaisesRegex(RuntimeError, "bad data"):
                ImageLayer(native, 1, 2, 2)
        self.assertFalse(native.images)

    def test_cleanup_continues_after_destroy_failure(self) -> None:
        native = FakeMlx()
        wrapper = make_wrapper(native)
        original = native.mlx_destroy_image

        def destroy(ptr: object, image: int) -> None:
            original(ptr, image)
            raise RuntimeError("destroy failed")

        with patch.object(native, "mlx_destroy_image", destroy):
            with self.assertRaisesRegex(RuntimeError, "destroy failed"):
                wrapper.quit()
        self.assertFalse(native.images)
        self.assertEqual(native.calls[-2:], ["window", "release"])
        wrapper.quit()


class InputTests(unittest.TestCase):
    def test_arrows_wasd_cheats_and_text_are_separate_events(self) -> None:
        wrapper = make_wrapper(FakeMlx())
        pairs = [(65361, EventType.KEY_LEFT), (65363, EventType.KEY_RIGHT),
                 (65362, EventType.KEY_UP), (65364, EventType.KEY_DOWN),
                 (65293, EventType.KEY_ENTER), (65307, EventType.KEY_ESC),
                 (65288, EventType.KEY_BACKSPACE),
                 (ord("w"), EventType.KEY_UP),
                 (ord("a"), EventType.KEY_LEFT),
                 (ord("s"), EventType.KEY_DOWN),
                 (ord("d"), EventType.KEY_RIGHT)]
        for char, kind in zip("pcinflbv",
                              (EventType.KEY_PAUSE, EventType.KEY_CHEAT,
                               EventType.KEY_INVINCIBLE, EventType.KEY_SKIP,
                               EventType.KEY_FREEZE, EventType.KEY_LIFE,
                               EventType.KEY_SPEED, EventType.KEY_POWER)):
            pairs.append((ord(char), kind))
        for code, kind in pairs:
            with self.subTest(code=code):
                wrapper._event_buffer.clear()
                wrapper.key_pressed(code, None)
                events = list(wrapper._event_buffer)
                expected = [kind]
                if code < 128:
                    expected.append(EventType.TEXT)
                self.assertEqual([e.type for e in events], expected)
                if code < 128:
                    self.assertEqual(events[-1].data, {"text": chr(code)})
        for char in "WASDPCINFLBVxyzXYZ0123456789 ":
            with self.subTest(text=char):
                wrapper._event_buffer.clear()
                wrapper.key_pressed(ord(char), None)
                self.assertEqual(wrapper._event_buffer[-1].type,
                                 EventType.TEXT)
                self.assertEqual(wrapper._event_buffer[-1].data,
                                 {"text": char})
        wrapper._event_buffer.clear()
        for code in (ord("!"), 0, 65505, 0x110000):
            wrapper.key_pressed(code, None)
        self.assertFalse(wrapper._event_buffer)

    def test_mouse_events_and_native_close_are_delivered(self) -> None:
        received: list[Event] = []
        native = FakeMlx()
        wrapper = make_wrapper(native, lambda events: received.extend(events))
        wrapper.mouse_press(1, 8, 9, None)
        wrapper.mouse_move(3, 4, None)
        wrapper.window_closed(None)
        wrapper.loop(None)
        self.assertEqual([e.type for e in received],
                         [EventType.MOUSE_DOWN, EventType.MOUSE_MOVE,
                          EventType.CLOSE])
        self.assertEqual(native.calls, ["exit"])


class CallbackTests(unittest.TestCase):
    def test_callback_failure_is_raised_after_loop_and_resources_released(
        self,
    ) -> None:
        native = FakeMlx()

        def fail(events: deque[Event]) -> None:
            raise ValueError("render failed")

        wrapper = make_wrapper(native, fail)
        with self.assertRaisesRegex(RuntimeError, "render failed"):
            wrapper.start()
        self.assertFalse(native.images)
        self.assertEqual(native.calls[-2:], ["window", "release"])

    def test_no_exception_escapes_any_c_callback(self) -> None:
        for name in ("key", "mouse", "motion", "close"):
            with self.subTest(callback=name):
                native = FakeMlx()
                wrapper = make_wrapper(native)
                wrapper._event_buffer = AnyBuffer()
                actions = {
                    "key": lambda: wrapper.key_pressed(ord("w"), None),
                    "mouse": lambda: wrapper.mouse_press(1, 2, 3, None),
                    "motion": lambda: wrapper.mouse_move(2, 3, None),
                    "close": lambda: wrapper.window_closed(None),
                }
                with patch.object(native, "mlx_loop_exit",
                                  side_effect=RuntimeError("exit failed")):
                    actions[name]()
                self.assertIsNotNone(wrapper._callback_error)
                wrapper.quit()

    def test_base_exception_does_not_escape_loop_callback(self) -> None:
        native = FakeMlx()

        def interrupt(events: deque[Event]) -> None:
            raise KeyboardInterrupt("interrupted")

        wrapper = make_wrapper(native, interrupt)
        wrapper.loop(None)
        self.assertEqual(native.calls, ["exit"])

    def test_quit_inside_callback_defers_release_until_native_loop_returns(
        self,
    ) -> None:
        native = FakeMlx()

        def quit_inside(events: deque[Event]) -> None:
            wrapper.quit()
            self.assertTrue(native.images)
            self.assertNotIn("release", native.calls)

        wrapper = make_wrapper(native, quit_inside)
        wrapper.start()
        self.assertFalse(native.images)
        self.assertEqual(native.calls[-2:], ["window", "release"])

    def test_controls_hook_key_press_not_vendor_key_release(self) -> None:
        native = FakeMlx()
        wrapper = make_wrapper(native)
        with patch.object(native, "mlx_hook", wraps=native.mlx_hook) as hook:
            wrapper.start()
        hook.assert_any_call(2, 2, 1, wrapper.key_pressed, None)
        hook.assert_any_call(2, 33, 0, wrapper.window_closed, None)
        hook.assert_any_call(2, 6, 1 << 6, wrapper.mouse_move, None)

    def test_hook_registration_failure_releases_resources(self) -> None:
        native = FakeMlx()
        wrapper = make_wrapper(native)
        with patch.object(native, "mlx_hook",
                          side_effect=RuntimeError("hook failed")):
            with self.assertRaisesRegex(RuntimeError, "hook failed"):
                wrapper.start()
        self.assertFalse(native.images)
        self.assertEqual(native.calls[-2:], ["window", "release"])


class AnyBuffer(deque[Event]):
    """Exercise an error at the input queue boundary."""

    def append(self, event: Event) -> None:
        raise RuntimeError("queue failed")


class CompositingTests(unittest.TestCase):
    def test_transparent_overlay_preserves_background_and_does_not_trail(
        self,
    ) -> None:
        native = FakeMlx()
        wrapper = make_wrapper(native)
        wrapper.fill_layer("main", 0xFF0000FF)
        wrapper.create_layer("actor")
        wrapper.put_pixel(0, 0, 0xFFFF0000, "actor")
        wrapper.refresh()
        self.assertEqual(native.screen,
                         [0xFFFF0000, 0xFF0000FF, 0xFF0000FF, 0xFF0000FF])
        wrapper.clear_layer("actor")
        wrapper.put_pixel(1, 0, 0xFFFF0000, "actor")
        wrapper.refresh()
        self.assertEqual(native.screen,
                         [0xFF0000FF, 0xFFFF0000, 0xFF0000FF, 0xFF0000FF])
        wrapper.clear_layer("main")
        wrapper.clear_layer("actor")
        wrapper.refresh()
        self.assertEqual(native.screen, [0xFF000000] * 4)

    def test_layer_order_and_partial_opacity(self) -> None:
        native = FakeMlx(endian=1)
        wrapper = make_wrapper(native)
        wrapper.fill_layer("main", 0xFF0000FF)
        wrapper.create_layer("overlay")
        wrapper.fill_layer("overlay", 0x80FF0000)
        wrapper.refresh()
        self.assertEqual(native.screen, [0xFF80007F] * 4)
        wrapper.set_layer_order(["overlay", "main"])
        wrapper.refresh()
        self.assertEqual(native.screen, [0xFF0000FF] * 4)
