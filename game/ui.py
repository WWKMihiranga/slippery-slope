# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
UI widgets for the polished interface.

Includes pill-style buttons with smooth hover/press feedback, an icon
button for the hamburger trigger, and a slide-out panel that eases in
and out so the options never clutter the play area.
"""

import pygame

from game.easing import Tween, ease_out_cubic, ease_out_back, lerp_color


class Button:
    """A rounded 'pill' button with animated hover and press states."""

    def __init__(self, rect, label, callback, kind="primary"):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.kind = kind          # "primary", "ghost", "danger"
        self.enabled = True
        self._hover = 0.0         # 0..1 hover blend
        self._press = 0.0         # 0..1 press pop
        self._press_tween = None

    def handle_event(self, event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._press_tween = Tween(1.0, 0.0, 0.28, ease_out_back)
                self.callback()

    def update(self, dt, mouse_pos):
        """Advance hover/press animations toward their targets."""
        hovering = self.enabled and self.rect.collidepoint(mouse_pos)
        target = 1.0 if hovering else 0.0
        self._hover += (target - self._hover) * min(1.0, 12.0 * dt)
        if self._press_tween:
            self._press_tween.update(dt)
            self._press = self._press_tween.value
            if self._press_tween.done:
                self._press_tween = None
                self._press = 0.0

    def draw(self, surface, theme, font):
        dip = int(self._press * 3)
        rect = self.rect.move(0, dip)

        if not self.enabled:
            base = theme["btn_disabled"]
        elif self.kind == "danger":
            base = theme["btn_danger"]
        elif self.kind == "ghost":
            base = theme["btn_ghost"]
        else:
            base = theme["btn_primary"]

        hi = theme.get("btn_primary_hi", base)
        fill = lerp_color(base, hi, self._hover) if self.enabled else base

        radius = rect.height // 2
        pygame.draw.rect(surface, theme["shadow"], rect.move(0, 3),
                         border_radius=radius)
        pygame.draw.rect(surface, fill, rect, border_radius=radius)

        text_color = (theme["btn_text_dim"] if not self.enabled
                      else theme["btn_text"])
        if self.kind == "ghost" and self.enabled:
            text_color = theme["text"]
        text = font.render(self.label, True, text_color)
        surface.blit(text, text.get_rect(center=rect.center))


class IconButton:
    """A small square button drawn with a custom icon (e.g. hamburger)."""

    def __init__(self, rect, icon, callback):
        self.rect = pygame.Rect(rect)
        self.icon = icon          # "menu", "close"
        self.callback = callback
        self._hover = 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def update(self, dt, mouse_pos):
        target = 1.0 if self.rect.collidepoint(mouse_pos) else 0.0
        self._hover += (target - self._hover) * min(1.0, 12.0 * dt)

    def draw(self, surface, theme):
        fill = lerp_color(theme["panel"], theme["btn_primary"], self._hover)
        pygame.draw.rect(surface, theme["shadow"],
                         self.rect.move(0, 2), border_radius=10)
        pygame.draw.rect(surface, fill, self.rect, border_radius=10)

        cx, cy = self.rect.center
        line_color = lerp_color(theme["text"], theme["btn_text"],
                                self._hover)
        if self.icon == "menu":
            for dy in (-6, 0, 6):
                pygame.draw.line(surface, line_color,
                                 (cx - 9, cy + dy), (cx + 9, cy + dy), 3)
        else:  # close
            pygame.draw.line(surface, line_color,
                             (cx - 8, cy - 8), (cx + 8, cy + 8), 3)
            pygame.draw.line(surface, line_color,
                             (cx - 8, cy + 8), (cx + 8, cy - 8), 3)


class SlidePanel:
    """
    An options panel that slides in from the right edge.

    `open()` and `close()` start an eased slide. All buttons inside the
    panel are positioned in 'panel-local' coordinates and translated by
    the panel's current pixel offset on the way to events and drawing,
    so the panel surface and its contents always move together.
    """

    def __init__(self, width):
        self.width = width
        self.is_open = False
        self._offset = 1.0        # 1 = fully hidden, 0 = fully shown
        self._tween = None
        self.buttons = []         # buttons store their base (resting) rect

    def open(self):
        self.is_open = True
        self._tween = Tween(self._offset, 0.0, 0.32, ease_out_cubic)

    def close(self):
        self.is_open = False
        self._tween = Tween(self._offset, 1.0, 0.28, ease_out_cubic)

    def toggle(self):
        self.close() if self.is_open else self.open()

    @property
    def visible(self):
        """True while any part of the panel is on-screen."""
        return self.is_open or self._offset < 1.0

    def add_button(self, button):
        """Register a button. Its rect is treated as the 'panel open' rest position."""
        button._base_rect = button.rect.copy()
        self.buttons.append(button)

    def _slide_px(self):
        """Pixels the panel (and its contents) are translated by right now."""
        return int(self._offset * self.width)

    def _sync_button_rects(self):
        """Move each button's rect to match the panel's current slide offset."""
        dx = self._slide_px()
        for b in self.buttons:
            base = getattr(b, "_base_rect", None)
            if base is not None:
                b.rect = base.move(dx, 0)

    def update(self, dt, mouse_pos):
        if self._tween:
            self._tween.update(dt)
            self._offset = self._tween.value
            if self._tween.done:
                self._tween = None
        # Always keep button rects synced - even when fully open, this is
        # a single source of truth so they cannot drift apart from the panel.
        self._sync_button_rects()
        if self.visible:
            for b in self.buttons:
                b.update(dt, mouse_pos)

    def panel_rect(self, win_w, win_h):
        """Current on-screen rectangle of the panel."""
        return pygame.Rect(win_w - self.width + self._slide_px(),
                           0, self.width, win_h)

    def handle_event(self, event):
        """Returns True if the event was consumed by the panel."""
        if not self.visible:
            return False
        # Make sure button rects reflect the panel's current position
        # before testing collisions.
        self._sync_button_rects()
        for b in self.buttons:
            b.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            win = pygame.display.get_surface()
            if self.panel_rect(*win.get_size()).collidepoint(event.pos):
                return True
        return False
