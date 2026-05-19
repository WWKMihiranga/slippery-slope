# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Generates pixel-art sprites for the icy theme and saves them as PNGs.

Run once to populate assets/sprites/. The game loads these if present
and falls back to drawn shapes otherwise. Producing them as real files
keeps the renderer simple and lets the art be swapped freely later.
"""

import os
import pygame

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "assets", "sprites")
S = 64  # sprite canvas size in pixels


def _surf():
    return pygame.Surface((S, S), pygame.SRCALPHA)


def _px(surf, x, y, color, size=1):
    """Draw a chunky 'pixel' block for a pixel-art look."""
    pygame.draw.rect(surf, color, (x, y, size, size))


def make_ice():
    """A frosted ice tile: pale blue with cracks, like the screenshot."""
    surf = _surf()
    base = (198, 236, 246)
    light = (224, 246, 252)
    edge = (150, 214, 232)
    surf.fill(base)
    # Rounded-ish darker border.
    pygame.draw.rect(surf, edge, (0, 0, S, S), 3, border_radius=10)
    # A couple of crack lines for texture.
    pygame.draw.line(surf, light, (14, 8), (22, 30), 3)
    pygame.draw.line(surf, light, (40, 18), (52, 44), 3)
    pygame.draw.line(surf, edge, (10, 46), (30, 54), 2)
    # Sparkle highlights.
    for sx, sy in ((46, 12), (18, 40), (52, 50)):
        _px(surf, sx, sy, (255, 255, 255), 3)
    return surf


def make_rock():
    """A rounded grey boulder with a pale rim."""
    surf = _surf()
    body = (120, 130, 140)
    dark = (88, 96, 105)
    light = (170, 180, 190)
    pygame.draw.circle(surf, dark, (S // 2, S // 2 + 2), 26)
    pygame.draw.circle(surf, body, (S // 2, S // 2), 24)
    # Top-left highlight.
    pygame.draw.circle(surf, light, (S // 2 - 7, S // 2 - 8), 8)
    # A few speckles.
    for sx, sy in ((40, 36), (26, 44), (44, 22)):
        _px(surf, sx, sy, dark, 4)
    return surf


def make_igloo():
    """The start marker: a small white-blue igloo."""
    surf = _surf()
    dome = (236, 246, 253)
    shade = (200, 222, 240)
    line = (150, 178, 210)
    door = (74, 108, 158)
    cx, cy = S // 2, S // 2 + 4

    # Solid dome: a filled half-circle sitting on a flat base.
    pygame.draw.circle(surf, dome, (cx, cy), 22)
    # Clip the bottom by painting transparent below the base line.
    base_y = cy + 8
    pygame.draw.rect(surf, (0, 0, 0, 0), (0, base_y, S, S - base_y))
    pygame.draw.rect(surf, dome, (cx - 22, cy - 2, 44, base_y - (cy - 2)))
    # Soft shading along the right side.
    pygame.draw.circle(surf, shade, (cx + 8, cy + 2), 14)
    pygame.draw.circle(surf, dome, (cx - 2, cy - 2), 18)
    # Outline.
    pygame.draw.circle(surf, line, (cx, cy), 22, 2)
    pygame.draw.line(surf, line, (cx - 22, base_y), (cx + 22, base_y), 2)
    # Two curved snow-brick rows.
    for r in (0, 1):
        y = cy - 6 + r * 9
        pygame.draw.arc(surf, line, (cx - 20, y - 4, 40, 26), 3.4, 6.0, 2)
    # Arched entrance tunnel.
    pygame.draw.circle(surf, door, (cx, base_y), 10)
    pygame.draw.rect(surf, door, (cx - 10, base_y, 20, 6))
    pygame.draw.circle(surf, dome, (cx, base_y + 1), 6)
    pygame.draw.rect(surf, dome, (cx - 6, base_y + 1, 12, 7))
    return surf


def make_castle():
    """The finish marker: a small blue castle with a flag."""
    surf = _surf()
    wall = (150, 200, 235)
    dark = (90, 140, 190)
    snow = (255, 255, 255)
    flag = (220, 70, 90)
    # Snow base.
    pygame.draw.ellipse(surf, snow, (8, S - 22, S - 16, 16))
    # Main keep.
    pygame.draw.rect(surf, wall, (20, 24, 24, 26))
    pygame.draw.rect(surf, dark, (20, 24, 24, 26), 2)
    # Side towers.
    pygame.draw.rect(surf, wall, (10, 30, 12, 20))
    pygame.draw.rect(surf, wall, (42, 30, 12, 20))
    # Battlements.
    for x in (10, 16, 20, 26, 32, 38, 42, 48):
        pygame.draw.rect(surf, wall, (x, 20, 5, 6))
    # Gate.
    pygame.draw.rect(surf, dark, (28, 36, 8, 14))
    pygame.draw.circle(surf, dark, (32, 36), 4)
    # Flag pole + flag.
    pygame.draw.line(surf, dark, (32, 8), (32, 22), 2)
    pygame.draw.polygon(surf, flag, [(32, 8), (44, 12), (32, 16)])
    return surf


def make_player():
    """The travelling marker: a warm red rounded token with a face hint."""
    surf = _surf()
    body = (235, 95, 110)
    dark = (180, 55, 70)
    light = (255, 160, 170)
    pygame.draw.circle(surf, dark, (S // 2, S // 2 + 2), 20)
    pygame.draw.circle(surf, body, (S // 2, S // 2), 18)
    pygame.draw.circle(surf, light, (S // 2 - 6, S // 2 - 6), 6)
    # Eyes.
    pygame.draw.circle(surf, (255, 255, 255), (S // 2 - 6, S // 2), 4)
    pygame.draw.circle(surf, (255, 255, 255), (S // 2 + 6, S // 2), 4)
    pygame.draw.circle(surf, dark, (S // 2 - 5, S // 2 + 1), 2)
    pygame.draw.circle(surf, dark, (S // 2 + 7, S // 2 + 1), 2)
    return surf


def generate_all():
    """Create all sprite PNGs (idempotent)."""
    pygame.init()
    os.makedirs(OUT, exist_ok=True)
    sprites = {
        "ice": make_ice(),
        "rock": make_rock(),
        "start": make_igloo(),
        "finish": make_castle(),
        "player": make_player(),
    }
    for name, surf in sprites.items():
        pygame.image.save(surf, os.path.join(OUT, name + ".png"))
    pygame.quit()
    return list(sprites)


if __name__ == "__main__":
    print("Generated:", generate_all())
