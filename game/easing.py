# ID: 20221341 / w1956364
# Name: Kavindu Mihiranga

"""
Easing functions and small animation helpers.

Easing makes motion feel natural: instead of moving at a constant speed,
things accelerate and decelerate the way real objects do. These are
pure functions of a progress value t in [0, 1]; no external library is
needed.
"""


def clamp01(t):
    """Clamp a value into the [0, 1] range."""
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def ease_in_out_quad(t):
    """Smooth start and end - the workhorse for sprite movement."""
    t = clamp01(t)
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2


def ease_out_cubic(t):
    """Fast start, gentle settle - good for panels and pop-ins."""
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_out_back(t):
    """Slight overshoot then settle - playful, for button presses."""
    t = clamp01(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def lerp(a, b, t):
    """Linear interpolation between a and b by fraction t."""
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    """Interpolate between two RGB colours."""
    t = clamp01(t)
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


class Tween:
    """
    A single animated value that eases from `start` to `end`.

    Call `update(dt)` each frame and read `value`. `done` becomes True
    once the duration has elapsed.
    """

    def __init__(self, start, end, duration, ease=ease_in_out_quad):
        self.start = start
        self.end = end
        self.duration = max(duration, 1e-6)
        self.ease = ease
        self.elapsed = 0.0

    @property
    def done(self):
        return self.elapsed >= self.duration

    @property
    def value(self):
        t = self.ease(clamp01(self.elapsed / self.duration))
        return lerp(self.start, self.end, t)

    def update(self, dt):
        self.elapsed = min(self.elapsed + dt, self.duration)
        return self.value
