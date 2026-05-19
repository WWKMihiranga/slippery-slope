# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Game settings: colour themes, window sizes, and music selection.

Three of each, per the brief. The theme palettes are richer than a
basic foreground/background pair so the polished UI (pill buttons,
slide panel, path glow) can pull consistent colours from one place.
"""

# --- Colour themes -------------------------------------------------------
THEMES = {
    "Ice": {
        "bg": (224, 236, 244),
        "bg_accent": (205, 226, 240),
        "panel": (255, 255, 255),
        "panel_edge": (210, 224, 236),
        "shadow": (180, 198, 212),
        "ice_a": (210, 238, 248),
        "ice_b": (188, 228, 242),
        "ice_edge": (235, 248, 252),
        "path_glow": (120, 200, 250),
        "path_core": (90, 170, 235),
        "rock": (120, 130, 140),
        "start": (90, 150, 220),
        "finish": (70, 110, 200),
        "player": (235, 95, 110),
        "text": (44, 60, 74),
        "text_dim": (120, 140, 154),
        "btn_primary": (74, 150, 222),
        "btn_primary_hi": (104, 176, 244),
        "btn_danger": (224, 96, 108),
        "btn_ghost": (236, 244, 250),
        "btn_disabled": (206, 216, 224),
        "btn_text": (255, 255, 255),
        "btn_text_dim": (150, 162, 172),
    },
    "Sunset": {
        "bg": (250, 238, 230),
        "bg_accent": (244, 226, 214),
        "panel": (255, 250, 246),
        "panel_edge": (238, 222, 210),
        "shadow": (224, 200, 184),
        "ice_a": (255, 226, 198),
        "ice_b": (252, 210, 178),
        "ice_edge": (255, 240, 224),
        "path_glow": (255, 178, 120),
        "path_core": (245, 140, 80),
        "rock": (138, 110, 96),
        "start": (230, 150, 70),
        "finish": (210, 96, 70),
        "player": (208, 70, 120),
        "text": (78, 54, 46),
        "text_dim": (162, 134, 122),
        "btn_primary": (236, 142, 72),
        "btn_primary_hi": (250, 166, 96),
        "btn_danger": (214, 84, 96),
        "btn_ghost": (250, 236, 226),
        "btn_disabled": (224, 208, 198),
        "btn_text": (255, 255, 255),
        "btn_text_dim": (176, 154, 142),
    },
    "Midnight": {
        "bg": (26, 30, 42),
        "bg_accent": (32, 37, 52),
        "panel": (40, 46, 62),
        "panel_edge": (54, 62, 82),
        "shadow": (16, 19, 28),
        "ice_a": (58, 68, 92),
        "ice_b": (48, 56, 78),
        "ice_edge": (74, 86, 114),
        "path_glow": (110, 200, 255),
        "path_core": (90, 160, 240),
        "rock": (98, 106, 124),
        "start": (96, 174, 234),
        "finish": (130, 200, 255),
        "player": (255, 120, 142),
        "text": (228, 234, 244),
        "text_dim": (138, 148, 168),
        "btn_primary": (86, 132, 214),
        "btn_primary_hi": (110, 158, 238),
        "btn_danger": (216, 92, 110),
        "btn_ghost": (52, 60, 80),
        "btn_disabled": (58, 64, 80),
        "btn_text": (255, 255, 255),
        "btn_text_dim": (120, 130, 148),
    },
}
THEME_ORDER = ["Ice", "Sunset", "Midnight"]

# --- Window sizes --------------------------------------------------------
WINDOW_SIZES = {
    "Small": (960, 680),
    "Medium": (1160, 820),
    "Large": (1360, 940),
}
SIZE_ORDER = ["Small", "Medium", "Large"]

# --- Music ---------------------------------------------------------------
MUSIC_TRACKS = ["Calm", "Upbeat", "Mystery"]

# --- Animation speed -----------------------------------------------------
SPEED_NAMES = ["Slow", "Normal", "Fast"]
SPEED_VALUES = {"Slow": 0.55, "Normal": 1.0, "Fast": 1.9}


class Settings:
    """Mutable container for the player's chosen options."""

    def __init__(self):
        self.theme_name = "Ice"
        self.size_name = "Medium"
        self.music_name = "Calm"
        self.music_on = True
        self.speed_name = "Normal"

    @property
    def theme(self):
        return THEMES[self.theme_name]

    @property
    def window_size(self):
        return WINDOW_SIZES[self.size_name]

    @property
    def anim_speed(self):
        return SPEED_VALUES[self.speed_name]

    def cycle_theme(self):
        i = THEME_ORDER.index(self.theme_name)
        self.theme_name = THEME_ORDER[(i + 1) % len(THEME_ORDER)]

    def cycle_size(self):
        i = SIZE_ORDER.index(self.size_name)
        self.size_name = SIZE_ORDER[(i + 1) % len(SIZE_ORDER)]

    def cycle_music(self):
        i = MUSIC_TRACKS.index(self.music_name)
        self.music_name = MUSIC_TRACKS[(i + 1) % len(MUSIC_TRACKS)]

    def cycle_speed(self):
        i = SPEED_NAMES.index(self.speed_name)
        self.speed_name = SPEED_NAMES[(i + 1) % len(SPEED_NAMES)]
