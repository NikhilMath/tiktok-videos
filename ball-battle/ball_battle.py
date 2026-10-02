#!/usr/bin/env python3
"""Ball Battle: two weapon-wielding balls fight inside a circular arena.

Renders a vertical 1080x1920, 60 fps MP4 for TikTok, with sound effects that are
generated in code and mixed in at the moment each bounce, hit and clash happens.
Frames are drawn off-screen with pygame and piped straight into ffmpeg, so a
video renders faster than real time and no window ever opens.

Usage:
    python ball_battle.py                  # render the episode described in CONFIG
    python ball_battle.py --seed 42        # same episode, different seed (different fight)
    python ball_battle.py --find-seed      # search for seeds with a 30-60 s fight and a close finish

Everything you'd change between episodes lives in CONFIG below.
"""
import argparse
import math
import os
import random
import subprocess
import sys
import tempfile
import time
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")          # draw off-screen, no window
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import imageio_ffmpeg  # noqa: E402
import numpy as np     # noqa: E402
import pygame          # noqa: E402
from pygame import gfxdraw  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# CONFIG: everything you need to make a new episode
# ============================================================================
CONFIG = {
    # --- Episode ------------------------------------------------------------
    "title": "SWORD vs SPEAR — who wins?",   # text after "—" goes on a smaller second line
    "winner_text": "{name} WINS!",           # {name} = the winning team's name
    "seed": 24,                              # same seed = same fight, every time (24: spear wins on 1 HP)

    # Each team: display name, ball color (R, G, B), weapon (a key of "weapons"
    # below), optional "weapon_overrides" (e.g. {"damage": 12}), and optional
    # "image": a PNG path used as the ball's face (it's cropped to a circle).
    "teams": [
        {"name": "SWORD", "color": (255, 51, 102), "weapon": "sword", "image": None},
        {"name": "SPEAR", "color": (40, 170, 255), "weapon": "spear", "image": None},
    ],

    # --- Weapons --------------------------------------------------------------
    # length/thickness in pixels, spin in turns per second, damage per hit.
    "weapons": {
        "sword":  {"length": 150, "thickness": 18, "spin": 0.55, "damage": 9},     # sword vs spear tested
        "spear":  {"length": 210, "thickness": 12, "spin": 0.44, "damage": 8.5},   # at ~50/50 over 160 seeds
        "axe":    {"length": 135, "thickness": 26, "spin": 0.45, "damage": 13},
        "dagger": {"length": 105, "thickness": 14, "spin": 0.80, "damage": 6},
        "hammer": {"length": 145, "thickness": 30, "spin": 0.35, "damage": 15},
        "scythe": {"length": 185, "thickness": 18, "spin": 0.50, "damage": 9},
    },

    # --- Battle rules ---------------------------------------------------------
    "start_hp": 100,
    "ball_radius": 70,
    "start_speed": 430,            # pixels per second
    "speedup_per_bounce": 1.05,    # +5% speed every wall bounce...
    "max_speed": 1250,             # ...capped so it stays watchable
    "hit_cooldown": 0.45,          # seconds before the same weapon can hit again
    "clash_cooldown": 0.25,
    "knockback": 0.6,              # how much a hit shoves the target (0 = none)
    "max_seconds": 75,             # safety stop: if nobody is down, higher HP wins

    # --- Video ----------------------------------------------------------------
    "width": 1080,
    "height": 1920,
    "fps": 60,
    "substeps": 4,                 # physics steps per frame (more = more precise)
    "winner_freeze_seconds": 2.0,
    "arena_center": (500, 1110),   # shifted left, away from TikTok's right-side buttons
    "arena_radius": 400,           # bottom edge at y=1510, above TikTok's bottom 20%
    "background": ((10, 8, 24), (24, 10, 40)),   # top and bottom colors
    "output_dir": os.path.join(HERE, "..", "renders"),
    "crf": 19,                     # video quality (lower = better and bigger)

    # --- find_seed mode -------------------------------------------------------
    "find_seed": {
        "start": 1,                # first seed to try
        "tries": 400,              # how many seeds to test
        "min_seconds": 30,         # the fight has to last at least this long...
        "max_seconds": 60,         # ...and at most this long
        "max_winner_hp": 20,       # close finish: the winner has less HP than this
        "show": 12,                # how many matches to print
    },
}

TAU = math.tau


# ============================================================================
# SIMULATION (deterministic: the same seed always gives the same fight)
# ============================================================================
class Ball:
    def __init__(self, team, weapon, x, y, vx, vy, angle, spin_dir, cfg):
        self.team = team
        self.weapon = weapon
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.r = cfg["ball_radius"]
        self.speed = math.hypot(vx, vy)
        self.hp = float(cfg["start_hp"])
        self.angle = angle
        self.spin = spin_dir * weapon["spin"] * TAU    # radians per second
        self.hit_cd = 0.0
        self.flash = 0.0
        self.alive = True

    def weapon_segment(self):
        """The weapon is a line segment from just outside the ball to its tip."""
        c, s = math.cos(self.angle), math.sin(self.angle)
        base = self.r + 4
        tip = self.r + self.weapon["length"]
        return (self.x + c * base, self.y + s * base), (self.x + c * tip, self.y + s * tip)


def closest_on_segment(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return ax + dx * t, ay + dy * t


def segment_distance(p1, p2, q1, q2):
    """Closest distance between two segments and the point halfway between them."""
    best = None
    for p, (a, b) in ((p1, (q1, q2)), (p2, (q1, q2)), (q1, (p1, p2)), (q2, (p1, p2))):
        c = closest_on_segment(p, a, b)
        d = math.hypot(p[0] - c[0], p[1] - c[1])
        if best is None or d < best[0]:
            best = (d, ((p[0] + c[0]) / 2, (p[1] + c[1]) / 2))
    # proper crossing (the endpoint checks above miss an X-shaped overlap)
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    o1, o2 = orient(p1, p2, q1), orient(p1, p2, q2)
    o3, o4 = orient(q1, q2, p1), orient(q1, q2, p2)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
        t = o1 / (o1 - o2)
        best = (0.0, (q1[0] + (q2[0] - q1[0]) * t, q1[1] + (q2[1] - q1[1]) * t))
    return best


def set_speed(ball, speed):
    v = math.hypot(ball.vx, ball.vy) or 1.0
    ball.vx *= speed / v
    ball.vy *= speed / v


class Battle:
    """One fight. step() advances one frame; events are recorded for sound/effects."""

    def __init__(self, cfg, seed):
        self.cfg = cfg
        self.rng = random.Random(seed)
        self.t = 0.0
        self.events = []          # (time, kind, strength, x, y)
        self.winner = None
        self.clash_cd = 0.0
        cx, cy = cfg["arena_center"]
        R = cfg["arena_radius"]
        self.balls = []
        for i, team in enumerate(cfg["teams"]):
            weapon = dict(cfg["weapons"][team["weapon"]])
            weapon.update(team.get("weapon_overrides") or {})
            weapon["kind"] = team["weapon"]
            side = -1 if i == 0 else 1
            x = cx + side * self.rng.uniform(R * 0.3, R * 0.45)
            y = cy + self.rng.uniform(-R * 0.35, R * 0.35)
            a = self.rng.uniform(0, TAU)
            sp = cfg["start_speed"]
            self.balls.append(Ball(team, weapon, x, y, math.cos(a) * sp, math.sin(a) * sp,
                                   self.rng.uniform(0, TAU), self.rng.choice((-1, 1)), cfg))

    def event(self, kind, strength, x, y):
        self.events.append((self.t, kind, strength, x, y))

    def step_frame(self):
        cfg = self.cfg
        dt = 1.0 / (cfg["fps"] * cfg["substeps"])
        for _ in range(cfg["substeps"]):
            if self.winner is not None:
                return
            self.substep(dt)
            self.t += dt

    def substep(self, dt):
        cfg = self.cfg
        cx, cy = cfg["arena_center"]
        R = cfg["arena_radius"]
        a, b = self.balls

        for ball in self.balls:
            ball.x += ball.vx * dt
            ball.y += ball.vy * dt
            ball.angle += ball.spin * dt
            ball.hit_cd = max(0.0, ball.hit_cd - dt)
            ball.flash = max(0.0, ball.flash - dt)
            # Arena wall: bounce, and get 5% faster each time (capped)
            dx, dy = ball.x - cx, ball.y - cy
            d = math.hypot(dx, dy)
            if d > R - ball.r:
                nx, ny = dx / d, dy / d
                ball.x, ball.y = cx + nx * (R - ball.r), cy + ny * (R - ball.r)
                vn = ball.vx * nx + ball.vy * ny
                if vn > 0:
                    ball.vx -= 2 * vn * nx
                    ball.vy -= 2 * vn * ny
                    ball.speed = min(ball.speed * cfg["speedup_per_bounce"], cfg["max_speed"])
                    set_speed(ball, ball.speed)
                    self.event("bounce", ball.speed / cfg["max_speed"], ball.x + nx * ball.r, ball.y + ny * ball.r)
        self.clash_cd = max(0.0, self.clash_cd - dt)

        # Ball vs ball: equal-mass elastic bounce
        dx, dy = b.x - a.x, b.y - a.y
        d = math.hypot(dx, dy) or 0.001
        if d < a.r + b.r:
            nx, ny = dx / d, dy / d
            push = (a.r + b.r - d) / 2
            a.x -= nx * push; a.y -= ny * push
            b.x += nx * push; b.y += ny * push
            rv = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
            if rv < 0:
                a.vx += rv * nx; a.vy += rv * ny
                b.vx -= rv * nx; b.vy -= rv * ny
                set_speed(a, a.speed); set_speed(b, b.speed)
                self.event("bump", 0.5, (a.x + b.x) / 2, (a.y + b.y) / 2)

        # Weapon vs weapon: clash. Both balls bounce apart and both weapons reverse spin.
        sa, sb = a.weapon_segment(), b.weapon_segment()
        if self.clash_cd <= 0:
            dist, point = segment_distance(sa[0], sa[1], sb[0], sb[1])
            if dist < (a.weapon["thickness"] + b.weapon["thickness"]) / 2:
                self.clash_cd = cfg["clash_cooldown"]
                for me, other in ((a, b), (b, a)):
                    nx, ny = other.x - me.x, other.y - me.y
                    n = math.hypot(nx, ny) or 1.0
                    nx, ny = nx / n, ny / n
                    vn = me.vx * nx + me.vy * ny
                    if vn > 0:                      # moving toward the other ball: send it away
                        me.vx -= 2 * vn * nx
                        me.vy -= 2 * vn * ny
                    me.vx -= nx * me.speed * 0.35
                    me.vy -= ny * me.speed * 0.35
                    set_speed(me, me.speed)
                    me.spin = -me.spin
                self.event("clash", 1.0, *point)

        # Weapon vs ball: damage, white flash, knockback (with a cooldown)
        for attacker, target, seg in ((a, b, sa), (b, a, sb)):
            if attacker.hit_cd > 0 or not target.alive:
                continue
            px, py = closest_on_segment((target.x, target.y), seg[0], seg[1])
            if math.hypot(target.x - px, target.y - py) < target.r + attacker.weapon["thickness"] / 2:
                attacker.hit_cd = cfg["hit_cooldown"]
                target.hp = max(0.0, target.hp - attacker.weapon["damage"])
                target.flash = 0.15
                kx, ky = target.x - px, target.y - py
                k = math.hypot(kx, ky) or 1.0
                target.vx += kx / k * target.speed * cfg["knockback"]
                target.vy += ky / k * target.speed * cfg["knockback"]
                set_speed(target, target.speed)
                self.event("hit", attacker.weapon["damage"] / 15, px, py)
                if target.hp <= 0:
                    target.alive = False
                    self.winner = attacker
                    self.event("ko", 1.0, target.x, target.y)
                    return

        if self.t >= cfg["max_seconds"]:                # time limit: higher HP wins
            self.winner = max(self.balls, key=lambda x: x.hp)
            self.event("ko", 0.6, self.winner.x, self.winner.y)


def simulate(cfg, seed):
    """Run a whole fight without drawing. Returns (seconds, winner index, winner HP)."""
    battle = Battle(cfg, seed)
    max_frames = int(cfg["max_seconds"] * cfg["fps"]) + 2
    for _ in range(max_frames):
        battle.step_frame()
        if battle.winner is not None:
            break
    return battle.t, battle.balls.index(battle.winner), battle.winner.hp


def find_seed(cfg):
    fs = cfg["find_seed"]
    print(f"Searching seeds {fs['start']}–{fs['start'] + fs['tries'] - 1} for a "
          f"{fs['min_seconds']}–{fs['max_seconds']} s fight where the winner ends under {fs['max_winner_hp']} HP…")
    matches = []
    t0 = time.time()
    for seed in range(fs["start"], fs["start"] + fs["tries"]):
        secs, w, hp = simulate(cfg, seed)
        if fs["min_seconds"] <= secs <= fs["max_seconds"] and 0 < hp < fs["max_winner_hp"]:
            matches.append((hp, secs, seed, w))
            print(f"  seed {seed:5d}: {secs:5.1f} s, {cfg['teams'][w]['name']} wins with {hp:.0f} HP")
            if len(matches) >= fs["show"]:
                break
    print(f"Done in {time.time() - t0:.1f} s. {len(matches)} match(es).")
    if matches:
        best = min(matches)
        print(f"Closest finish: seed {best[2]} ({best[1]:.1f} s, winner on {best[0]:.0f} HP). "
              f"Put it in CONFIG['seed'] or run: python ball_battle.py --seed {best[2]}")


# ============================================================================
# DRAWING
# ============================================================================
def radial(size, color, falloff=2.2, strength=1.0):
    """An RGB surface with a soft radial glow (for additive blending)."""
    n = size
    y, x = np.mgrid[0:n, 0:n]
    d = np.hypot(x - n / 2 + 0.5, y - n / 2 + 0.5) / (n / 2)
    k = np.clip(1 - d, 0, 1) ** falloff * strength
    arr = np.zeros((n, n, 3), dtype=np.uint8)
    for i in range(3):
        arr[..., i] = np.clip(color[i] * k, 0, 255).astype(np.uint8).T
    return pygame.surfarray.make_surface(arr)


def font(size):
    for name in ("arialblack", "impact", "helveticaneue", "arial"):
        path = pygame.font.match_font(name, bold=True)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def outlined(text, size, color, outline=(0, 0, 0), width=6):
    """Bold text with a thick outline (readable on any background)."""
    f = font(size)
    base = f.render(text, True, color)
    out = f.render(text, True, outline)
    w, h = base.get_width() + width * 2, base.get_height() + width * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx in range(-width, width + 1, 2):
        for dy in range(-width, width + 1, 2):
            if dx * dx + dy * dy <= width * width:
                surf.blit(out, (dx + width, dy + width))
    surf.blit(base, (width, width))
    return surf


def fit(surf, max_w):
    if surf.get_width() <= max_w:
        return surf
    k = max_w / surf.get_width()
    return pygame.transform.smoothscale(surf, (int(surf.get_width() * k), int(surf.get_height() * k)))


def lighten(c, k):
    return tuple(min(255, int(v + (255 - v) * k)) for v in c)


def darken(c, k):
    return tuple(int(v * (1 - k)) for v in c)


class Renderer:
    SAFE_LEFT, SAFE_RIGHT = 60, 920      # keep clear of TikTok's right-side buttons
    SAFE_TOP = 200                       # below TikTok's top bar

    def __init__(self, cfg):
        pygame.init()
        self.cfg = cfg
        W, H = cfg["width"], cfg["height"]
        self.W, self.H = W, H
        self.frame = pygame.Surface((W, H))
        self.cx, self.cy = cfg["arena_center"]
        self.R = cfg["arena_radius"]
        self.build_background()
        self.build_title()
        self.particles = []
        self.trails = {0: [], 1: []}
        self.shown_hp = [float(cfg["start_hp"])] * 2      # HP bars ease toward the real value
        self.ghost_hp = [float(cfg["start_hp"])] * 2      # white "damage chip" behind the bar
        r = cfg["ball_radius"]
        self.faces = []
        self.glows, self.trail_dots = [], []
        for team in cfg["teams"]:
            c = team["color"]
            self.glows.append(radial(int(r * 3.4), c, 1.8, 0.85))
            self.trail_dots.append([radial(int(r * 1.6), c, 1.6, 0.06 + 0.05 * i) for i in range(8)])
            self.faces.append(self.load_face(team.get("image"), r))
        self.flash_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        gfxdraw.filled_circle(self.flash_surf, r + 1, r + 1, r, (255, 255, 255, 255))

    # --- static layers ---------------------------------------------------------
    def build_background(self):
        W, H, R, cx, cy = self.W, self.H, self.R, self.cx, self.cy
        top, bottom = (np.array(c, dtype=np.float32) for c in self.cfg["background"])
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        k = (y / H)[..., None]
        img = top * (1 - k) + bottom * k
        d = np.hypot(x - cx, y - cy)
        inside = (d < R)[..., None]
        img = np.where(inside, img * 0.55 + np.array([6, 10, 22], np.float32), img)   # darker arena floor
        ring = np.exp(-((d - R) / 16.0) ** 2)[..., None] * np.array([120, 200, 255], np.float32)
        img = np.clip(img + ring, 0, 255).astype(np.uint8)
        self.background = pygame.surfarray.make_surface(img.transpose(1, 0, 2))
        for rr in (R * 0.33, R * 0.66):                   # faint rings on the arena floor
            gfxdraw.aacircle(self.background, cx, cy, int(rr), (40, 50, 90))
        # The same background with a hole where the arena is: drawn on top each frame
        # so weapons/particles never poke outside the arena.
        self.outside = self.background.convert_alpha() if pygame.display.get_init() and pygame.display.get_surface() else None
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.blit(self.background, (0, 0))
        alpha = pygame.surfarray.pixels_alpha(overlay)
        alpha[...] = np.where(np.hypot(x - cx, y - cy).T < R - 1, 0, 255).astype(np.uint8)
        del alpha
        self.outside = overlay

    def build_title(self):
        cfg = self.cfg
        title = cfg["title"]
        main, _, sub = title.partition("—")
        main, sub = main.strip(), sub.strip()
        names = [t["name"] for t in cfg["teams"]]
        parts = main.split(" vs ")
        if len(parts) == 2:                               # color each team's name
            pieces = [(parts[0], cfg["teams"][0]["color"]), (" vs ", (255, 255, 255)),
                      (parts[1], cfg["teams"][1]["color"])]
        else:
            pieces = [(main, (255, 255, 255))]
        surfs = [outlined(text, 112, lighten(color, 0.15), width=7) for text, color in pieces]
        w = sum(s.get_width() for s in surfs) - 14 * (len(surfs) - 1)
        h = max(s.get_height() for s in surfs)
        line = pygame.Surface((w, h), pygame.SRCALPHA)
        x = 0
        for s in surfs:
            line.blit(s, (x, 0))
            x += s.get_width() - 14
        self.title_main = fit(line, self.SAFE_RIGHT - self.SAFE_LEFT)
        self.title_sub = fit(outlined(sub, 66, (255, 230, 120), width=6), self.SAFE_RIGHT - self.SAFE_LEFT) if sub else None
        self.names = [outlined(n, 40, lighten(t["color"], 0.2), width=4) for n, t in zip(names, cfg["teams"])]

    def load_face(self, path, r):
        """Optional PNG face, scaled and cropped to a circle."""
        if not path:
            return None
        if not os.path.isabs(path):
            path = os.path.join(HERE, path)
        img = pygame.image.load(path)
        img = pygame.transform.smoothscale(img, (r * 2, r * 2)).convert_alpha() if pygame.display.get_surface() else \
            pygame.transform.smoothscale(img.convert_alpha() if False else img, (r * 2, r * 2))
        face = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        face.blit(img, (0, 0))
        mask = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        gfxdraw.filled_circle(mask, r, r, r - 6, (255, 255, 255, 255))
        face.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return face

    # --- effects -------------------------------------------------------------------
    def spawn(self, x, y, color, n, speed, life=0.6, size=(3, 7), gravity=0.0):
        rng = random.Random(len(self.particles) * 7919 + int(x * 13 + y * 31))
        for _ in range(n):
            a = rng.uniform(0, TAU)
            s = rng.uniform(speed * 0.3, speed)
            L = rng.uniform(life * 0.6, life)
            self.particles.append([x, y, math.cos(a) * s, math.sin(a) * s, L, L, color,
                                   rng.uniform(*size), gravity])

    def on_events(self, events, battle):
        for t, kind, strength, x, y in events:
            if kind == "clash":
                self.spawn(x, y, (255, 240, 150), 26, 700, 0.5, (2, 5))
                self.spawn(x, y, (255, 255, 255), 10, 400, 0.3, (2, 4))
            elif kind == "hit":
                target = min(battle.balls, key=lambda bl: math.hypot(bl.x - x, bl.y - y))
                self.spawn(x, y, lighten(target.team["color"], 0.3), 20, 520, 0.6, (3, 7))
            elif kind == "bounce":
                self.spawn(x, y, (150, 210, 255), 5, 220, 0.35, (2, 4))
            elif kind == "ko":
                loser = [bl for bl in battle.balls if bl is not battle.winner][0]
                self.spawn(loser.x, loser.y, loser.team["color"], 70, 900, 1.2, (4, 10))
                self.spawn(loser.x, loser.y, (255, 255, 255), 30, 600, 0.8, (3, 6))

    def update_particles(self, dt):
        alive = []
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.93
            p[3] = p[3] * 0.93 + p[8] * dt
            p[4] -= dt
            if p[4] > 0:
                alive.append(p)
        self.particles = alive

    # --- drawing -------------------------------------------------------------------
    def draw_weapon(self, ball):
        w = ball.weapon
        kind = w["kind"]
        c, s = math.cos(ball.angle), math.sin(ball.angle)
        px, py = -s, c                                    # perpendicular
        r = ball.r

        def P(d, side=0.0):
            return (ball.x + c * d + px * side, ball.y + s * d + py * side)

        def poly(points, fill, outline=(15, 15, 25)):
            pts = [(int(x), int(y)) for x, y in points]
            gfxdraw.filled_polygon(self.frame, pts, fill)
            gfxdraw.aapolygon(self.frame, pts, outline)

        L, T = w["length"], w["thickness"]
        steel, edge, wood, gold = (215, 225, 240), (250, 252, 255), (150, 95, 50), (240, 190, 60)
        if kind in ("sword", "dagger"):
            poly([P(r - 6, -T * 0.25), P(r + 8, -T * 0.25), P(r + 8, T * 0.25), P(r - 6, T * 0.25)], wood)      # grip
            poly([P(r + 6, -T * 1.1), P(r + 14, -T * 1.1), P(r + 14, T * 1.1), P(r + 6, T * 1.1)], gold)        # guard
            poly([P(r + 14, -T / 2), P(r + L - T, -T / 2), P(r + L, 0), P(r + L - T, T / 2), P(r + 14, T / 2)], steel)
            pygame.draw.aaline(self.frame, edge, P(r + 16, 0), P(r + L - 4, 0))
        elif kind == "spear":
            poly([P(r - 4, -T * 0.3), P(r + L - 40, -T * 0.3), P(r + L - 40, T * 0.3), P(r - 4, T * 0.3)], wood)
            poly([P(r + L - 52, 0), P(r + L - 36, -T * 1.0), P(r + L, 0), P(r + L - 36, T * 1.0)], steel)
        elif kind == "axe":
            poly([P(r - 4, -T * 0.18), P(r + L, -T * 0.18), P(r + L, T * 0.18), P(r - 4, T * 0.18)], wood)
            poly([P(r + L - 46, T * 0.15), P(r + L - 56, T * 1.6), P(r + L - 20, T * 2.1),
                  P(r + L + 6, T * 1.4), P(r + L - 6, T * 0.15)], steel)
        elif kind == "hammer":
            poly([P(r - 4, -T * 0.15), P(r + L - 30, -T * 0.15), P(r + L - 30, T * 0.15), P(r - 4, T * 0.15)], wood)
            poly([P(r + L - 40, -T * 0.9), P(r + L, -T * 0.9), P(r + L, T * 0.9), P(r + L - 40, T * 0.9)], (120, 125, 140))
        else:                                              # scythe
            poly([P(r - 4, -T * 0.18), P(r + L, -T * 0.18), P(r + L, T * 0.18), P(r - 4, T * 0.18)], wood)
            poly([P(r + L, 0), P(r + L + 10, T * 1.0), P(r + L - 20, T * 3.4), P(r + L - 30, T * 3.2),
                  P(r + L - 6, T * 1.2)], steel)

    def draw_ball(self, i, ball, opponent):
        color = ball.team["color"]
        x, y, r = int(ball.x), int(ball.y), ball.r
        glow = self.glows[i]
        self.frame.blit(glow, (x - glow.get_width() // 2, y - glow.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)
        gfxdraw.filled_circle(self.frame, x, y, r, darken(color, 0.45))
        gfxdraw.filled_circle(self.frame, x, y, r - 7, color)
        gfxdraw.aacircle(self.frame, x, y, r, darken(color, 0.6))
        gfxdraw.filled_circle(self.frame, x - r // 3, y - r // 3, r // 4, lighten(color, 0.55))   # gloss
        face = self.faces[i]
        if face is not None:
            self.frame.blit(face, (x - r, y - r))
        else:
            # Default face: two eyes glaring at the opponent, angry brows
            ang = math.atan2(opponent.y - ball.y, opponent.x - ball.x)
            for side in (-1, 1):
                ex, ey = x + side * r * 0.34, y - r * 0.08
                gfxdraw.filled_circle(self.frame, int(ex), int(ey), int(r * 0.22), (255, 255, 255))
                gfxdraw.aacircle(self.frame, int(ex), int(ey), int(r * 0.22), (20, 20, 30))
                gfxdraw.filled_circle(self.frame, int(ex + math.cos(ang) * r * 0.09), int(ey + math.sin(ang) * r * 0.09),
                                      int(r * 0.11), (15, 15, 25))
                bx1, by1 = ex - side * r * 0.2, ey - r * 0.32
                bx2, by2 = ex + side * r * 0.22, ey - r * 0.22
                pygame.draw.line(self.frame, (20, 20, 30), (bx1, by2), (bx2, by1), 7)
        if ball.flash > 0:                                 # white hit flash
            self.flash_surf.set_alpha(int(255 * min(1, ball.flash / 0.15)))
            self.frame.blit(self.flash_surf, (x - r - 1, y - r - 1))

    def draw_hp_bars(self, battle, dt):
        cfg = self.cfg
        x0, x1 = self.SAFE_LEFT + 10, self.SAFE_RIGHT - 10
        for i, ball in enumerate(battle.balls):
            y = 470 + i * 86
            self.shown_hp[i] += (ball.hp - self.shown_hp[i]) * min(1, dt * 14)
            self.ghost_hp[i] = max(self.shown_hp[i], self.ghost_hp[i] - dt * 30)
            name = self.names[i]
            self.frame.blit(name, (x0, y - name.get_height() // 2))
            bx, bw, bh = x0 + 230, x1 - (x0 + 230), 44
            rect = pygame.Rect(bx, y - bh // 2, bw, bh)
            pygame.draw.rect(self.frame, (20, 20, 35), rect.inflate(8, 8), border_radius=14)
            pygame.draw.rect(self.frame, (45, 45, 70), rect, border_radius=12)
            frac_g = max(0.0, self.ghost_hp[i] / cfg["start_hp"])
            frac = max(0.0, self.shown_hp[i] / cfg["start_hp"])
            if frac_g > 0:
                pygame.draw.rect(self.frame, (255, 255, 255), (bx, rect.y, int(bw * frac_g), bh), border_radius=12)
            if frac > 0:
                pygame.draw.rect(self.frame, ball.team["color"], (bx, rect.y, int(bw * frac), bh), border_radius=12)
                pygame.draw.rect(self.frame, lighten(ball.team["color"], 0.4), (bx + 8, rect.y + 6, max(0, int(bw * frac) - 16), 8),
                                 border_radius=4)
            hp_txt = outlined(f"{math.ceil(ball.hp)} HP", 30, (255, 255, 255), width=3)
            self.frame.blit(hp_txt, (bx + bw - hp_txt.get_width() - 12, y - hp_txt.get_height() // 2))

    def draw_frame(self, battle, dt, freeze_t=None):
        f = self.frame
        f.blit(self.background, (0, 0))
        # motion trails
        for i, ball in enumerate(battle.balls):
            if not ball.alive:
                continue
            trail = self.trails[i]
            trail.append((ball.x, ball.y))
            del trail[:-8]
            for k, (tx, ty) in enumerate(trail[:-1]):
                dot = self.trail_dots[i][k]
                f.blit(dot, (int(tx) - dot.get_width() // 2, int(ty) - dot.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)
        a, b = battle.balls
        for ball in battle.balls:
            if ball.alive:
                self.draw_weapon(ball)
        for i, (ball, opp) in enumerate(((a, b), (b, a))):
            if ball.alive:
                self.draw_ball(i, ball, opp)
        if freeze_t is None:
            self.draw_particles()
        f.blit(self.outside, (0, 0))                        # hide anything outside the arena
        gfxdraw.aacircle(f, self.cx, self.cy, self.R, (170, 225, 255))
        gfxdraw.aacircle(f, self.cx, self.cy, self.R - 1, (170, 225, 255))

        # title and HP bars
        ty = self.SAFE_TOP + 10
        mid = (self.SAFE_LEFT + self.SAFE_RIGHT) // 2
        f.blit(self.title_main, (mid - self.title_main.get_width() // 2, ty))
        if self.title_sub:
            f.blit(self.title_sub, (mid - self.title_sub.get_width() // 2, ty + self.title_main.get_height() - 8))
        self.draw_hp_bars(battle, dt)

        if freeze_t is not None:                            # winner screen
            self.draw_winner(battle, freeze_t)

    def draw_particles(self):
        for p in self.particles:                            # sparks and bursts
            k = max(0.0, p[4] / p[5])
            col = tuple(int(c * k + 10 * (1 - k)) for c in p[6])
            gfxdraw.filled_circle(self.frame, int(p[0]), int(p[1]), max(1, int(p[7] * (0.5 + 0.5 * k))), col)

    def draw_winner(self, battle, t):
        """Freeze-frame winner screen: banner in the half of the arena away from the
        winner, with the champion and the confetti burst drawn on top."""
        w = battle.winner
        i = battle.balls.index(w)
        loser = [b for b in battle.balls if b is not w][0]
        color = w.team["color"]
        k = min(1.0, t / 0.25)
        band_y = int(self.cy + self.R * 0.45 if w.y < self.cy else self.cy - self.R * 0.45)
        band = pygame.Surface((self.W, 220), pygame.SRCALPHA)
        band.fill((0, 0, 0, int(160 * k)))
        self.frame.blit(band, (0, band_y - 110))
        text = self.cfg["winner_text"].format(name=w.team["name"])
        surf = fit(outlined(text, 120, lighten(color, 0.25), width=8), self.SAFE_RIGHT - self.SAFE_LEFT)
        s = 0.6 + 0.4 * min(1.0, t / 0.18) + 0.06 * math.sin(t * 9) * (t > 0.18)
        surf = pygame.transform.smoothscale(surf, (int(surf.get_width() * s), int(surf.get_height() * s)))
        mid = (self.SAFE_LEFT + self.SAFE_RIGHT) // 2
        self.draw_weapon(w)
        self.draw_ball(i, w, loser)
        self.draw_particles()
        self.frame.blit(surf, (mid - surf.get_width() // 2, band_y - surf.get_height() // 2))


# ============================================================================
# SOUND (generated with numpy, mixed at each event's exact time)
# ============================================================================
SR = 44100


def _env(n, decay):
    return np.exp(-np.arange(n) / SR * decay)


def _tone(freq, dur, decay, wave_kind="sine", vol=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if wave_kind == "sine":
        w = np.sin(TAU * freq * t)
    elif wave_kind == "square":
        w = np.sign(np.sin(TAU * freq * t)) * 0.5
    else:                                                   # triangle
        w = 2 * np.abs(2 * ((freq * t) % 1) - 1) - 1
    return w * _env(n, decay) * vol


def _noise(dur, decay, smooth=1, vol=1.0, seed=0):
    n = int(dur * SR)
    w = np.random.default_rng(seed).uniform(-1, 1, n)
    if smooth > 1:
        w = np.convolve(w, np.ones(smooth) / smooth, mode="same")
    return w * _env(n, decay) * vol


def _mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def sound_for(kind, strength):
    if kind == "bounce":
        return _tone(380 + 520 * strength, 0.09, 40, "triangle", 0.30)
    if kind == "bump":
        return _tone(180, 0.12, 30, "sine", 0.35)
    if kind == "hit":
        return _mix(_tone(120, 0.28, 16, "sine", 0.9), _noise(0.14, 35, 6, 0.55), _tone(240, 0.1, 40, "square", 0.15))
    if kind == "clash":
        return _mix(*[_tone(f, 0.55, 8 + i * 2, "sine", 0.16) for i, f in enumerate((1180, 1730, 2390, 3310))],
                    _noise(0.05, 90, 1, 0.45))
    if kind == "ko":
        return _mix(_tone(70, 0.9, 4, "sine", 1.0), _noise(0.7, 6, 12, 0.5))
    if kind == "win":
        notes = [(523.25, 0.0), (659.25, 0.12), (783.99, 0.24), (1046.5, 0.36)]
        parts = []
        for f, start in notes:
            tone = _tone(f, 0.35, 6, "square", 0.22)
            parts.append(np.concatenate([np.zeros(int(start * SR)), tone]))
        chord = [np.concatenate([np.zeros(int(0.5 * SR)), _tone(f, 1.4, 2.2, "triangle", 0.25)]) for f in (261.63, 329.63, 392.0, 523.25)]
        return _mix(*parts, *chord)
    return np.zeros(1)


def build_audio(events, total_seconds, path):
    buf = np.zeros(int(total_seconds * SR) + SR)
    last = {}
    for t, kind, strength, _x, _y in events:
        if kind == "bounce" and t - last.get(kind, -1) < 0.03:   # don't stack identical clicks
            continue
        last[kind] = t
        s = sound_for(kind, strength)
        i = int(t * SR)
        j = min(len(buf), i + len(s))
        buf[i:j] += s[:j - i]
    buf = np.tanh(buf * 1.1) * 0.9                          # soft limiter
    pcm = (buf * 32767).astype(np.int16)
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


# ============================================================================
# RENDER
# ============================================================================
def frame_bytes(surface):
    if hasattr(pygame.image, "tobytes"):
        return pygame.image.tobytes(surface, "RGB")
    return pygame.image.tostring(surface, "RGB")


def render(cfg, seed):
    fps = cfg["fps"]
    secs, w, hp = simulate(cfg, seed)                       # preview the outcome first
    winner_name = cfg["teams"][w]["name"]
    print(f"Seed {seed}: {secs:.1f} s fight, {winner_name} wins with {hp:.0f} HP. Rendering…")

    os.makedirs(cfg["output_dir"], exist_ok=True)
    slug = "-vs-".join(t["name"].lower().replace(" ", "-") for t in cfg["teams"])
    out_path = os.path.abspath(os.path.join(cfg["output_dir"], f"ball-battle-{slug}-seed{seed}.mp4"))
    tmp = tempfile.mkdtemp(prefix="ball-battle-")
    video_path = os.path.join(tmp, "video.mp4")
    audio_path = os.path.join(tmp, "audio.wav")

    renderer = Renderer(cfg)
    battle = Battle(cfg, seed)
    writer = imageio_ffmpeg.write_frames(
        video_path, (cfg["width"], cfg["height"]), fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", quality=None, macro_block_size=1,
        ffmpeg_log_level="error", output_params=["-preset", "veryfast", "-crf", str(cfg["crf"])],
    )
    writer.send(None)

    dt = 1.0 / fps
    frames = 0
    t0 = time.time()
    seen = 0
    while battle.winner is None:
        battle.step_frame()
        new = battle.events[seen:]
        seen = len(battle.events)
        renderer.on_events(new, battle)
        renderer.update_particles(dt)
        for ball in battle.balls:
            if not ball.alive:
                renderer.trails[battle.balls.index(ball)].clear()
        renderer.draw_frame(battle, dt)
        writer.send(frame_bytes(renderer.frame))
        frames += 1
        if frames % (fps * 5) == 0:
            print(f"  {frames / fps:5.1f} s rendered ({frames / (time.time() - t0):.0f} fps)", flush=True)

    # Winner screen: freeze the action, keep the burst and banner animating
    end_t = battle.t
    battle.events.append((end_t + 0.15, "win", 1.0, battle.winner.x, battle.winner.y))
    renderer.spawn(battle.winner.x, battle.winner.y, battle.winner.team["color"], 60, 950, 1.6, (4, 9))
    renderer.spawn(battle.winner.x, battle.winner.y, (255, 220, 90), 40, 800, 1.6, (3, 7))
    freeze_frames = int(cfg["winner_freeze_seconds"] * fps)
    for k in range(freeze_frames):
        renderer.update_particles(dt)
        renderer.draw_frame(battle, dt, freeze_t=k * dt)
        writer.send(frame_bytes(renderer.frame))
        frames += 1
    writer.close()

    total = frames / fps
    build_audio(battle.events, total, audio_path)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", video_path, "-i", audio_path,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out_path], check=True)
    print(f"Saved {out_path}")
    print(f"{total:.1f} s video, {frames} frames, rendered in {time.time() - t0:.0f} s.")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Render a ball battle video for TikTok.")
    parser.add_argument("--seed", type=int, help="override CONFIG['seed']")
    parser.add_argument("--find-seed", action="store_true", help="search for seeds with a good fight instead of rendering")
    args = parser.parse_args()
    cfg = CONFIG
    if args.find_seed:
        find_seed(cfg)
    else:
        render(cfg, args.seed if args.seed is not None else cfg["seed"])


if __name__ == "__main__":
    main()
