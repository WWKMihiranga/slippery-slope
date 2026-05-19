# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Main application: window, game loop, state machine and animation.

UX design:
  * The board fills the whole frame. No options permanently clutter it.
  * A slim bottom bar holds the four most-used actions
    (Start, Reset, Load Map, Editor).
  * A hamburger button opens a slide-out panel for everything else
    (themes, music, window size, speed, save map). The panel eases in
    and out and dims the board behind it.
  * The player slides with eased motion; the solution trail lights up
    the ice tile-by-tile, smoothly, as the player passes over it.

States:
  PLAY    - a map is loaded; press Start to solve and watch.
  SOLVING - the player is animating along the shortest path.
  EDIT    - the map editor is active.
"""

import os

import pygame

from core.map_parser import parse_file, MapParseError
from core.grid import Grid
from core.solver import solve
from game.settings import Settings
from game.audio import AudioManager
from game.renderer import Renderer
from game.ui import Button, IconButton, SlidePanel
from game.editor import MapEditor, TOOLS
from game.easing import (Tween, ease_in_out_quad, ease_out_cubic,
                         clamp01, lerp)

MAPS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "maps")

# Seconds the player takes to cross one tile (scaled by the speed setting).
SECONDS_PER_TILE = 0.085
PANEL_WIDTH = 320
BAR_HEIGHT = 86


class Game:
    """The application object: owns the window, state and main loop."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Sliding Puzzle Pathfinder")
        self.settings = Settings()
        self.screen = pygame.display.set_mode(
            self.settings.window_size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.audio = AudioManager()

        self.grid = None
        self._picker_mode = False
        self.result = None
        self.state = "PLAY"
        self.editor = MapEditor()
        self.toast = Toast()

        # Animation state.
        self._seg = 0             # current path segment index
        self._seg_tween = None    # eased progress 0..1 along the segment
        self._path_fill = {}      # (r,c) -> glow fraction, for the trail
        self._bob_t = 0.0         # player hover bob phase
        self._win_t = 0.0         # finish celebration timer

        self.panel = SlidePanel(PANEL_WIDTH)
        self.bar_buttons = []
        self.menu_icon = None
        self._build_ui()

        example = os.path.join(MAPS_DIR, "example.txt")
        if os.path.exists(example):
            self._load_map_file(example, announce=False)
        self.toast.show("Press Start to watch the shortest path.")

        if self.settings.music_on:
            self.audio.play(self.settings.music_name)

    # --- UI construction -------------------------------------------------
    def _build_ui(self):
        """Lay out the bottom bar, hamburger icon and slide-panel."""
        self._build_bar()
        self._build_panel_buttons()
        self._refresh_ui_state()

    def _build_bar(self):
        """
        Build the bottom bar.

        Two layouts: in PLAY/SOLVING the bar holds the four main actions
        (Start, Reset, Load, Editor); in EDIT it switches to a contextual
        editor toolbar (the tool picker + Save + Done). The hamburger
        icon stays in either layout.
        """
        win_w, win_h = self.screen.get_size()
        pad = 16
        bar_y = win_h - BAR_HEIGHT
        usable = win_w - 2 * pad - 64   # reserve space for hamburger icon
        bh = 50
        by = bar_y + (BAR_HEIGHT - bh) // 2

        if self.state == "EDIT":
            # Editor toolbar: tools as small toggles + Save + Done.
            actions = [
                ("Rock", lambda: self._set_tool("rock"), "ghost"),
                ("Start tile", lambda: self._set_tool("start"), "ghost"),
                ("Finish tile", lambda: self._set_tool("finish"), "ghost"),
                ("Erase", lambda: self._set_tool("erase"), "ghost"),
                ("Save Map", self.on_save, "ghost"),
                ("Done editing", self.on_toggle_editor, "primary"),
            ]
        else:
            actions = [
                ("Start", self.on_start, "primary"),
                ("Reset", self.on_reset, "ghost"),
                ("Load Map", self.on_load, "ghost"),
                ("Editor", self.on_toggle_editor, "ghost"),
            ]

        n = len(actions)
        bw = (usable - (n - 1) * pad) // n
        self.bar_buttons = []
        for i, (label, cb, kind) in enumerate(actions):
            x = pad + i * (bw + pad)
            self.bar_buttons.append(Button((x, by, bw, bh), label, cb, kind))

        # Hamburger icon at the far right.
        self.menu_icon = IconButton(
            (win_w - pad - 50, by, 50, bh), "menu", self.panel.toggle)

    def _set_tool(self, tool):
        """Choose an editor tool directly (used by the editor toolbar)."""
        if self.state == "EDIT":
            from game.editor import TOOLS
            if tool in TOOLS:
                self.editor.tool_index = TOOLS.index(tool)
                self.toast.show(f"Tool: {tool}")
                self._refresh_ui_state()

    def _build_panel_buttons(self):
        """Create the buttons living inside the slide-out panel."""
        win_w, win_h = self.screen.get_size()
        px = win_w - PANEL_WIDTH       # left edge of the panel when fully open
        x = px + 28
        w = PANEL_WIDTH - 56
        h = 48
        gap = 12
        y = 96
        self.panel.buttons = []

        def add(label, cb, kind="ghost"):
            nonlocal y
            self.panel.add_button(Button((x, y, w, h), label, cb, kind))
            y += h + gap

        # Settings only - context-sensitive editor controls live elsewhere.
        add("Theme", self.on_cycle_theme)
        add("Track", self.on_cycle_music)
        add("Sound", self.on_toggle_music)
        add("Window size", self.on_cycle_size)
        add("Speed", self.on_cycle_speed)

        # Close icon, also registered with the panel so it slides in sync.
        self.panel_close = IconButton(
            (px + PANEL_WIDTH - 28 - 40, 36, 40, 40),
            "close", self.panel.close)
        self.panel.add_button(self.panel_close)

    def _refresh_ui_state(self):
        """
        Enable/disable buttons for the current state, and highlight the
        active editor tool when in EDIT mode.
        """
        for b in self.bar_buttons:
            if b.label == "Start":
                b.enabled = (self.state == "PLAY" and self.grid is not None)
            elif b.label == "Reset":
                b.enabled = (self.state in ("PLAY", "SOLVING"))
            else:
                b.enabled = True
        # Mark the active editor tool by giving its button the primary look.
        if self.state == "EDIT":
            tool_map = {"rock": "Rock", "start": "Start tile",
                        "finish": "Finish tile", "erase": "Erase"}
            active_label = tool_map.get(self.editor.tool)
            for b in self.bar_buttons:
                if b.label in tool_map.values():
                    b.kind = "primary" if b.label == active_label else "ghost"

    def _switch_state(self, new_state):
        """Change top-level state and rebuild the bar so its contents match."""
        self.state = new_state
        self._build_bar()
        self._refresh_ui_state()

    # --- button callbacks ------------------------------------------------
    def on_start(self):
        if self.grid is None or self.state != "PLAY":
            return
        self.result = solve(self.grid)
        if not self.result.found:
            self.toast.show("No path exists for this map.", error=True)
            return
        self._seg = 0
        self._path_fill = {}
        self._start_segment()
        moves = len(self.result.steps) - 2
        self.toast.show(f"Solving - {moves} moves, "
                        f"{self.result.nodes_expanded} nodes explored.")
        self._switch_state("SOLVING")

    def on_reset(self):
        self.result = None
        self._path_fill = {}
        self._seg_tween = None
        self._win_t = 0.0
        self.toast.show("Reset. Press Start to solve again.")
        self._switch_state("PLAY")

    def on_load(self):
        path = self._ask_open_file()
        if path:
            self._load_map_file(path)

    def on_save(self):
        if self.state != "EDIT":
            return
        path = self._ask_save_file()
        if path:
            ok = self.editor.save(path)
            self.toast.show(self.editor.message, error=not ok)

    def on_toggle_editor(self):
        if self.state == "EDIT":
            try:
                self.grid = self.editor.to_grid()
                self.result = None
                self._path_fill = {}
                self.toast.show("Map ready - press Start.")
                self._switch_state("PLAY")
            except MapParseError as exc:
                self.toast.show(f"Fix map first: {exc}", error=True)
                return
        else:
            if self.grid is not None:
                self.editor.load_from_grid(self.grid)
            self.result = None
            self._path_fill = {}
            self.toast.show(
                "Editor: pick a tool below, then click the board.")
            self._switch_state("EDIT")

    def on_cycle_theme(self):
        self.settings.cycle_theme()
        self.renderer._bg_cache = None
        self.toast.show(f"Theme: {self.settings.theme_name}")

    def on_cycle_music(self):
        self.settings.cycle_music()
        if self.settings.music_on:
            self.audio.play(self.settings.music_name)
        self.toast.show(f"Music: {self.settings.music_name}")

    def on_toggle_music(self):
        self.settings.music_on = not self.settings.music_on
        if self.settings.music_on:
            self.audio.play(self.settings.music_name)
        else:
            self.audio.stop()
        self.toast.show(f"Music {'on' if self.settings.music_on else 'off'}.")

    def on_cycle_size(self):
        self.settings.cycle_size()
        self.screen = pygame.display.set_mode(
            self.settings.window_size, pygame.RESIZABLE)
        self.renderer._bg_cache = None
        self._build_ui()
        self.toast.show(f"Window size: {self.settings.size_name}")

    def on_cycle_speed(self):
        self.settings.cycle_speed()
        self.toast.show(f"Animation speed: {self.settings.speed_name}")

    # --- file dialogs ----------------------------------------------------
    def _ask_open_file(self):
        """Pick a map from the maps/ folder via an in-game picker (no OS dialog)."""
        self._open_map_picker()
        return None  # picking is async; the picker will call _load_map_file itself

    def _ask_save_file(self):
        """Auto-name a saved map inside the maps/ folder."""
        import time
        os.makedirs(MAPS_DIR, exist_ok=True)
        return os.path.join(MAPS_DIR, f"custom_{int(time.time())}.txt")

    def _open_map_picker(self):
        """Build the slide-out panel as a temporary 'choose a map' list."""
        try:
            files = sorted(f for f in os.listdir(MAPS_DIR)
                           if f.endswith(".txt"))
        except OSError:
            files = []
        if not files:
            self.toast.show("No .txt maps found in the maps/ folder.",
                            error=True)
            return

        # Rebuild the panel's button list with one button per map.
        win_w, _ = self.screen.get_size()
        px = win_w - PANEL_WIDTH
        x = px + 28
        w = PANEL_WIDTH - 56
        h = 44
        gap = 8
        y = 96
        self.panel.buttons = []

        def pick(path):
            return lambda: self._pick_map_from_panel(path)

        for name in files:
            full = os.path.join(MAPS_DIR, name)
            self.panel.add_button(Button((x, y, w, h), name, pick(full)))
            y += h + gap

        # Close icon, and a Cancel that restores the settings panel.
        self.panel_close = IconButton(
            (px + PANEL_WIDTH - 28 - 40, 36, 40, 40),
            "close", self._close_map_picker)
        self.panel.add_button(self.panel_close)
        self._picker_mode = True
        self.panel.open()

    def _pick_map_from_panel(self, path):
        """Called when the user clicks a map name in the picker panel."""
        self._close_map_picker()
        self._load_map_file(path)

    def _close_map_picker(self):
        """Restore the normal settings panel."""
        self._picker_mode = False
        self.panel.close()
        # Rebuild settings buttons for next time the menu opens.
        self._build_panel_buttons()

    def _load_map_file(self, path, announce=True):
        try:
            self.grid = Grid(parse_file(path))
            self.result = None
            self._path_fill = {}
            if announce:
                self.toast.show(
                    f"Loaded {os.path.basename(path)} "
                    f"({self.grid.width}x{self.grid.height}).")
            self._switch_state("PLAY")
        except MapParseError as exc:
            self.toast.show(f"Could not load map: {exc}", error=True)
            self._refresh_ui_state()

    # --- animation -------------------------------------------------------
    def _start_segment(self):
        """Begin the eased slide for the current path segment."""
        path = self.result.path
        if self._seg >= len(path) - 1:
            self._seg_tween = None
            return
        a, b = path[self._seg], path[self._seg + 1]
        tiles = abs(a[0] - b[0]) + abs(a[1] - b[1])
        duration = max(tiles, 1) * SECONDS_PER_TILE / self.settings.anim_speed
        self._seg_tween = Tween(0.0, 1.0, duration, ease_in_out_quad)

    def _update_animation(self, dt):
        """Advance the player and light up the trail tile-by-tile."""
        self._bob_t += dt * 4.0  # gentle idle/move bob

        if self.state == "SOLVING" and self.result:
            self._advance_solving(dt)

        # The trail tiles ease toward full glow even after arriving.
        for cell, val in list(self._path_fill.items()):
            if val < 1.0:
                self._path_fill[cell] = min(1.0, val + dt * 6.0)

        if self.state == "PLAY" and self.result and self.result.found:
            self._win_t += dt

    def _advance_solving(self, dt):
        path = self.result.path
        if self._seg_tween is None:
            self._start_segment()
            if self._seg_tween is None:  # nothing left
                self.toast.show("Done! Shortest path shown.")
                self._switch_state("PLAY")
                return

        self._seg_tween.update(dt)
        # Light up every tile the slide has passed over so far.
        self._fill_segment_trail()

        if self._seg_tween.done:
            self._seg += 1
            if self._seg >= len(path) - 1:
                self._seg_tween = None
                self._win_t = 0.0
                self.toast.show("Done! Shortest path shown.")
                self._switch_state("PLAY")
            else:
                self._start_segment()

    def _fill_segment_trail(self):
        """Mark tiles under the current slide as lit, up to player pos."""
        path = self.result.path
        a, b = path[self._seg], path[self._seg + 1]
        prog = self._seg_tween.value  # eased 0..1
        # Number of whole tiles covered so far on this segment.
        total = abs(a[0] - b[0]) + abs(a[1] - b[1])
        covered = prog * total
        d_row = (b[0] - a[0])
        d_col = (b[1] - a[1])
        step_r = (0 if d_row == 0 else (1 if d_row > 0 else -1))
        step_c = (0 if d_col == 0 else (1 if d_col > 0 else -1))
        for k in range(int(covered) + 1):
            cell = (a[0] + step_r * k, a[1] + step_c * k)
            # Newly touched tiles start mid-glow then ease to full.
            self._path_fill.setdefault(cell, 0.35)

    def _route_reveal(self):
        """Fraction of the route line to draw, tracking the player."""
        if not self.result or not self.result.path:
            return 0.0
        total = len(self.result.path) - 1
        if total <= 0:
            return 1.0
        if self.state == "PLAY":
            return 1.0
        # Mid-solve: completed segments plus the current eased fraction.
        frac = self._seg_tween.value if self._seg_tween else 0.0
        return clamp01((self._seg + frac) / total)

    def _player_pixel(self):
        """Current eased pixel position of the player sprite."""
        path = self.result.path
        seg = min(self._seg, len(path) - 1)
        a = path[seg]
        b = path[min(seg + 1, len(path) - 1)]
        t = self._seg_tween.value if self._seg_tween else 1.0
        ax, ay = self.renderer.tile_center(self.grid, *a)
        bx, by = self.renderer.tile_center(self.grid, *b)
        return (int(lerp(ax, bx, t)), int(lerp(ay, by, t)))

    # --- drawing ---------------------------------------------------------
    def _draw(self):
        theme = self.settings.theme
        dt_mouse = pygame.mouse.get_pos()
        self.renderer.draw_background(theme)

        active_grid = self.grid
        if self.state == "EDIT":
            try:
                active_grid = self.editor.to_grid()
            except MapParseError:
                active_grid = None

        if active_grid is not None:
            self.renderer.draw_board(active_grid, theme,
                                     path_fill=self._path_fill)
            # Trace the route line in step with the player's progress.
            if (self.result and self.result.found
                    and self.state in ("SOLVING", "PLAY")):
                reveal = self._route_reveal()
                self.renderer.draw_route(active_grid, self.result.path,
                                         theme, reveal=reveal)
            self.renderer.draw_markers(active_grid, theme)
            if self.state == "SOLVING":
                import math
                bob = math.sin(self._bob_t) * 3.0
                self.renderer.draw_player(
                    active_grid, self._player_pixel(), theme, bob=bob)
            elif (self.state == "PLAY" and self.result
                  and self.result.found):
                # Rest the player on the finish after solving.
                fc = self.renderer.tile_center(active_grid,
                                               *self.grid.finish)
                import math
                bob = math.sin(self._bob_t) * 2.0
                self.renderer.draw_player(active_grid, fc, theme, bob=bob)
        else:
            self._draw_centered_message(
                theme, "Map has no start/finish yet - "
                       "use the editor tools.")

        self._draw_bottom_bar(theme)
        self._draw_panel(theme)
        self.toast.draw(self.screen, theme, self.renderer)
        pygame.display.flip()

    def _draw_centered_message(self, theme, msg):
        font = self.renderer.font(20)
        text = font.render(msg, True, theme["text_dim"])
        win_w, win_h = self.screen.get_size()
        self.screen.blit(text, text.get_rect(
            center=(win_w // 2, (win_h - BAR_HEIGHT) // 2)))

    def _draw_bottom_bar(self, theme):
        """The slim action bar at the bottom of the window."""
        win_w, win_h = self.screen.get_size()
        bar = pygame.Rect(0, win_h - BAR_HEIGHT, win_w, BAR_HEIGHT)
        pygame.draw.rect(self.screen, theme["panel"], bar)
        pygame.draw.line(self.screen, theme["panel_edge"],
                         (0, bar.y), (win_w, bar.y), 2)
        font = self.renderer.font(17, bold=True)
        for b in self.bar_buttons:
            b.draw(self.screen, theme, font)
        self.menu_icon.draw(self.screen, theme)

    def _draw_panel(self, theme):
        """The slide-out options panel and the dimmer behind it."""
        if not self.panel.visible:
            return
        win_w, win_h = self.screen.get_size()
        rect = self.panel.panel_rect(win_w, win_h)

        # Dim the board behind the panel, proportional to how open it is.
        openness = 1.0 - (rect.x - (win_w - PANEL_WIDTH)) / PANEL_WIDTH
        dim = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        dim.fill((10, 14, 22, int(110 * clamp01(openness))))
        self.screen.blit(dim, (0, 0))

        # Panel body.
        pygame.draw.rect(self.screen, theme["panel"], rect)
        pygame.draw.line(self.screen, theme["panel_edge"],
                         (rect.x, 0), (rect.x, win_h), 2)

        # Title slides with the panel.
        title = self.renderer.font(22, bold=True).render(
            "Options", True, theme["text"])
        self.screen.blit(title, (rect.x + 28, 40))

        font = self.renderer.font(15, bold=True)
        small = self.renderer.font(13, bold=True)
        for b in self.panel.buttons:
            # IconButton uses a different draw signature; dispatch by type.
            if isinstance(b, Button):
                b.draw(self.screen, theme, font)
                value = self._panel_value_for(b.label)
                if value:
                    self._draw_value_chip(b.rect, value, small, theme)
            else:
                b.draw(self.screen, theme)

        # Footer hint also slides with the panel.
        hint = small.render("Settings only - actions stay on the bar.",
                            True, theme["text_dim"])
        self.screen.blit(hint, (rect.x + 28, win_h - 48))

    def _draw_value_chip(self, button_rect, value, font, theme):
        """A small rounded chip with the current setting value, inside a button."""
        vt = font.render(value, True, theme["btn_text"])
        pad = 10
        chip_w = vt.get_width() + 2 * pad
        chip_h = vt.get_height() + 6
        chip_x = button_rect.right - chip_w - 10
        chip_y = button_rect.centery - chip_h // 2
        chip = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
        pygame.draw.rect(chip, (*theme["path_core"], 210),
                         chip.get_rect(), border_radius=chip_h // 2)
        chip.blit(vt, (pad, 3))
        self.screen.blit(chip, (chip_x, chip_y))

    def _panel_value_for(self, label):
        """The current setting value shown inside a panel button."""
        s = self.settings
        return {
            "Theme": s.theme_name,
            "Track": s.music_name,
            "Sound": "On" if s.music_on else "Off",
            "Window size": s.size_name,
            "Speed": s.speed_name,
        }.get(label, "")

    # --- events ----------------------------------------------------------
    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(
                (max(event.w, 760), max(event.h, 560)), pygame.RESIZABLE)
            self.renderer._bg_cache = None
            self._build_ui()
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.panel.is_open:
                self.panel.close()
            return True

        # The panel, when open, gets first refusal on events.
        if self.panel.visible:
            consumed = self.panel.handle_event(event)
            if consumed:
                return True
            # A click on the dimmed board closes the panel.
            if (event.type == pygame.MOUSEBUTTONDOWN
                    and self.panel.is_open):
                self.panel.close()
                return True

        self.menu_icon.handle_event(event)
        for b in self.bar_buttons:
            b.handle_event(event)

        # Editor: clicking the board edits a tile.
        if (self.state == "EDIT"
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and not self.panel.visible):
            cell = self._editor_cell_at(event.pos)
            if cell is not None:
                self.editor.apply(*cell)
        return True

    def _editor_cell_at(self, pos):
        class _Geo:
            width = self.editor.width
            height = self.editor.height
        return self.renderer.cell_at(_Geo(), pos)

    # --- main loop -------------------------------------------------------
    def _update(self, dt):
        mouse = pygame.mouse.get_pos()
        for b in self.bar_buttons:
            b.update(dt, mouse)
        self.menu_icon.update(dt, mouse)
        self.panel.update(dt, mouse)
        self._update_animation(dt)
        self.toast.update(dt)

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            for event in pygame.event.get():
                if not self._handle_event(event):
                    running = False
            self._update(dt)
            self._draw()
        pygame.quit()


class Toast:
    """A small status message that fades in at the top of the screen."""

    def __init__(self):
        self.text = ""
        self.error = False
        self._life = 0.0
        self._alpha = 0.0

    def show(self, text, error=False):
        self.text = text
        self.error = error
        self._life = 4.0

    def update(self, dt):
        if self._life > 0:
            self._life -= dt
            self._alpha = min(1.0, self._alpha + dt * 6.0)
        else:
            self._alpha = max(0.0, self._alpha - dt * 4.0)

    def draw(self, surface, theme, renderer):
        if self._alpha <= 0.01 or not self.text:
            return
        font = renderer.font(15, bold=True)
        text = font.render(self.text, True, theme["btn_text"])
        pad_x, pad_y = 18, 10
        w = text.get_width() + 2 * pad_x
        h = text.get_height() + 2 * pad_y
        win_w = surface.get_size()[0]
        x = (win_w - w) // 2
        # Slide down slightly as it fades in.
        y = int(lerp(-10, 22, ease_out_cubic(self._alpha)))

        chip = pygame.Surface((w, h), pygame.SRCALPHA)
        base = theme["btn_danger"] if self.error else theme["btn_primary"]
        a = int(235 * self._alpha)
        pygame.draw.rect(chip, (*base, a), chip.get_rect(),
                         border_radius=h // 2)
        chip.blit(text, (pad_x, pad_y))
        chip.set_alpha(int(255 * self._alpha))
        surface.blit(chip, (x, y))
