# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Renderer for the polished sliding-puzzle game.

The board fills the whole frame (no permanent side panel). The path is
not drawn as a line - instead each ice tile the path crosses *lights up*
its colour, and the renderer fills those tiles in smoothly, one brick
at a time, as the player advances. Sprites are loaded from
assets/sprites; if any are missing the renderer falls back to shapes.
"""

import os
import math

import pygame

from core.map_parser import ROCK
from game.easing import lerp_color, ease_out_cubic, clamp01

SPRITE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "sprites")


class Renderer:
    """Owns layout maths and all board drawing for one frame."""

    def __init__(self, screen):
        self.screen = screen
        self._fonts = {}
        self._sprites_raw = self._load_sprites()
        self._sprite_cache = {}   # (name, size) -> scaled Surface
        self._bg_cache = None     # (size, theme_id) -> gradient Surface

    # --- fonts -----------------------------------------------------------
    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont(
                "Arial Rounded MT Bold,Arial", size, bold=bold)
        return self._fonts[key]

    # --- sprites ---------------------------------------------------------
    def _load_sprites(self):
        sprites = {}
        for name in ("ice", "rock", "start", "finish", "player"):
            for ext in (".png", ".jpg"):
                path = os.path.join(SPRITE_DIR, name + ext)
                if os.path.exists(path):
                    try:
                        sprites[name] = pygame.image.load(path).convert_alpha()
                    except pygame.error:
                        pass
                    break
        return sprites

    def _sprite(self, name, size):
        """Return a sprite scaled to `size` px, cached. None if absent."""
        if name not in self._sprites_raw:
            return None
        key = (name, size)
        if key not in self._sprite_cache:
            self._sprite_cache[key] = pygame.transform.smoothscale(
                self._sprites_raw[name], (size, size))
        return self._sprite_cache[key]

    # --- layout ----------------------------------------------------------
    def board_geometry(self, grid):
        """
        Where the board sits and how big each tile is.

        The board is centred in the whole window (minus a margin and a
        slim bottom bar), so it uses the full frame.
        """
        win_w, win_h = self.screen.get_size()
        margin = 28
        bottom_bar = 86
        avail_w = win_w - 2 * margin
        avail_h = win_h - 2 * margin - bottom_bar
        tile = min(avail_w // grid.width, avail_h // grid.height)
        tile = max(tile, 10)
        board_w = tile * grid.width
        board_h = tile * grid.height
        ox = (win_w - board_w) // 2
        oy = margin + (avail_h - board_h) // 2
        return ox, oy, tile

    def cell_rect(self, grid, row, col):
        ox, oy, tile = self.board_geometry(grid)
        return pygame.Rect(ox + col * tile, oy + row * tile, tile, tile)

    def cell_at(self, grid, pos):
        ox, oy, tile = self.board_geometry(grid)
        x, y = pos
        if x < ox or y < oy:
            return None
        col = (x - ox) // tile
        row = (y - oy) // tile
        if 0 <= row < grid.height and 0 <= col < grid.width:
            return int(row), int(col)
        return None

    def tile_center(self, grid, row, col):
        ox, oy, tile = self.board_geometry(grid)
        return (ox + col * tile + tile // 2, oy + row * tile + tile // 2)

    # --- background ------------------------------------------------------
    def draw_background(self, theme):
        """A soft vertical gradient, cached per size + theme."""
        size = self.screen.get_size()
        theme_id = id(theme)
        if not self._bg_cache or self._bg_cache[0] != (size, theme_id):
            surf = pygame.Surface(size)
            top, bot = theme["bg"], theme["bg_accent"]
            for y in range(size[1]):
                t = y / max(size[1] - 1, 1)
                pygame.draw.line(surf, lerp_color(top, bot, t),
                                 (0, y), (size[0], y))
            self._bg_cache = ((size, theme_id), surf)
        self.screen.blit(self._bg_cache[1], (0, 0))

    # --- board -----------------------------------------------------------
    def draw_board(self, grid, theme, path_fill=None):
        """
        Draw the ice tiles and rocks.

        `path_fill` maps (row, col) -> fill fraction in [0, 1]; those
        tiles are blended toward the path-glow colour by that amount,
        which is how the trail 'lights up brick by brick'.
        """
        ox, oy, tile = self.board_geometry(grid)
        path_fill = path_fill or {}
        ice_sprite = self._sprite("ice", tile)

        for r in range(grid.height):
            for c in range(grid.width):
                rect = pygame.Rect(ox + c * tile, oy + r * tile, tile, tile)
                if grid.grid[r][c] == ROCK:
                    self._draw_tile_base(rect, theme, ice_sprite, r, c)
                    self._draw_rock(rect, theme, tile)
                    continue

                glow = path_fill.get((r, c), 0.0)
                self._draw_tile_base(rect, theme, ice_sprite, r, c)
                if glow > 0:
                    self._draw_glow(rect, theme, glow)

    def _draw_tile_base(self, rect, theme, ice_sprite, r, c):
        """Draw one ice tile (sprite if available, else a shaded square)."""
        if ice_sprite is not None:
            self.screen.blit(ice_sprite, rect)
        else:
            shade = theme["ice_a"] if (r + c) % 2 == 0 else theme["ice_b"]
            pygame.draw.rect(self.screen, shade, rect)
            pygame.draw.rect(self.screen, theme["ice_edge"], rect, 1)

    def _draw_glow(self, rect, theme, amount):
        """
        Gently highlight a traversed ice tile.

        The effect is a soft tint of the floor toward the path colour -
        not an opaque fill - so the ice texture still reads through and
        the trail looks like lit footsteps rather than painted squares.
        """
        amount = clamp01(amount)
        eased = ease_out_cubic(amount)
        inset = rect.inflate(-max(3, rect.width // 8),
                             -max(3, rect.height // 8))
        # Light, semi-transparent tint.
        glow = pygame.Surface(inset.size, pygame.SRCALPHA)
        color = theme["path_glow"]
        glow.fill((*color, int(95 * eased)))
        self.screen.blit(glow, inset)
        # A small bright core marks the centre of each footstep.
        radius = int(rect.width * 0.12 * eased)
        if radius > 1:
            core = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(core, (*theme["path_core"], 160),
                               (radius, radius), radius)
            self.screen.blit(core, (rect.centerx - radius,
                                    rect.centery - radius))

    def _draw_rock(self, rect, theme, tile):
        sprite = self._sprite("rock", tile)
        if sprite is not None:
            self.screen.blit(sprite, rect)
            return
        pad = max(2, tile // 8)
        inner = rect.inflate(-2 * pad, -2 * pad)
        pygame.draw.circle(self.screen, theme["rock"], inner.center,
                           inner.width // 2)

    # --- route line ------------------------------------------------------
    def draw_route(self, grid, path, theme, reveal=1.0):
        """
        Draw a soft connecting line through the path's tile centres.

        `reveal` in [0, 1] controls how much of the route is drawn, so
        the line can be traced out in step with the player.
        """
        if not path or len(path) < 2:
            return
        pts = [self.tile_center(grid, r, c) for r, c in path]
        # How many full segments to draw, plus a partial one.
        total_seg = len(pts) - 1
        shown = clamp01(reveal) * total_seg
        full = int(shown)
        frac = shown - full

        draw_pts = pts[:full + 1]
        if full < total_seg and frac > 0:
            a, b = pts[full], pts[full + 1]
            draw_pts.append((int(a[0] + (b[0] - a[0]) * frac),
                             int(a[1] + (b[1] - a[1]) * frac)))
        if len(draw_pts) < 2:
            return
        ox, oy, tile = self.board_geometry(grid)
        width = max(3, tile // 9)
        pygame.draw.lines(self.screen, theme["path_core"], False,
                          draw_pts, width)
        # Round the joints.
        for p in draw_pts:
            pygame.draw.circle(self.screen, theme["path_core"], p,
                               width // 2)

    # --- markers ---------------------------------------------------------
    def draw_markers(self, grid, theme):
        self._draw_marker(grid, grid.start, theme, "start", "S")
        self._draw_marker(grid, grid.finish, theme, "finish", "F")

    def _draw_marker(self, grid, pos, theme, key, letter):
        rect = self.cell_rect(grid, *pos)
        sprite = self._sprite(key, rect.width)
        if sprite is not None:
            self.screen.blit(sprite, rect)
            return
        pad = max(3, rect.width // 6)
        inner = rect.inflate(-2 * pad, -2 * pad)
        pygame.draw.rect(self.screen, theme[key], inner, border_radius=8)
        label = self.font(max(12, rect.width // 2), bold=True).render(
            letter, True, theme["btn_text"])
        self.screen.blit(label, label.get_rect(center=rect.center))

    # --- player ----------------------------------------------------------
    def draw_player(self, grid, pixel_pos, theme, bob=0.0):
        """Draw the player sprite; `bob` adds a gentle vertical hover."""
        ox, oy, tile = self.board_geometry(grid)
        size = int(tile * 0.78)
        x = pixel_pos[0] - size // 2
        y = pixel_pos[1] - size // 2 + int(bob)
        # Soft shadow that shrinks as the sprite bobs up.
        shadow_w = int(size * (0.62 - bob * 0.01))
        shadow = pygame.Surface((shadow_w, shadow_w // 3), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), shadow.get_rect())
        self.screen.blit(shadow, (pixel_pos[0] - shadow_w // 2,
                                  pixel_pos[1] + size // 3))
        sprite = self._sprite("player", size)
        if sprite is not None:
            self.screen.blit(sprite, (x, y))
        else:
            pygame.draw.circle(self.screen, theme["player"],
                               (pixel_pos[0], pixel_pos[1] + int(bob)),
                               size // 2)
