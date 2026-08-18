Exactly. No abstraction lecture. Just the two pipelines side by side.

### Create image

| Your API             | MLX                        | Pygame                   |
| -------------------- | -------------------------- | ------------------------ |
| `create_image(w, h)` | `mlx_new_image(mlx, w, h)` | `pygame.Surface((w, h))` |

### Access image pixels

| Your API                       | MLX                                   | Pygame                        |
| ------------------------------ | ------------------------------------- | ----------------------------- |
| `image.set_pixel(x, y, color)` | write to `mlx_get_data_addr()` buffer | `surface.set_at((x, y), rgb)` |

### Put image on window

| Your API                          | MLX                            | Pygame                         |
| --------------------------------- | ------------------------------ | ------------------------------ |
| `graphics.put_image(image, x, y)` | `mlx_put_image_to_window(...)` | `window.blit(surface, (x, y))` |

### Show frame

| Your API | MLX                                   | Pygame                  |
| -------- | ------------------------------------- | ----------------------- |
| —        | MLX handles window display/event loop | `pygame.display.flip()` |

So the pipeline is:

```text
MLX
──────────────────────────────────────
mlx_new_image()
       ↓
mlx_get_data_addr()
       ↓
write pixels
       ↓
mlx_put_image_to_window()
       ↓
window


Pygame
──────────────────────────────────────
pygame.Surface()
       ↓
surface.set_at()
       ↓
write pixels
       ↓
window.blit()
       ↓
pygame.display.flip()
       ↓
window
```

And **your API sits over the common parts**:

```text
                 YOUR API
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
        MLX                 Pygame
   mlx_new_image()      Surface()
   pixel buffer         set_at()
   put_image()          blit()
```

That's the parallel we're after.


layout system