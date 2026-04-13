"""
game.py  –  Adaptive AI Opponent – Core Game Module
====================================================
Handles:
  • Game world (tile-based arena with walls)
  • Player logic
  • Level generation
  • HUD / UI rendering (futuristic neon theme)
  • Score, health, pause, restart, game-over screens
  • High-score persistence (scores.json)
"""

import pygame
import math
import json
import os
import random
import time

from ai_npc import AdaptiveNPC

# ─────────────────────────────────────────────────────────
#  Colour palette  (futuristic neon / dark theme)
# ─────────────────────────────────────────────────────────
C_BG          = (8,   8,  20)
C_GRID        = (15,  15,  35)
C_WALL        = (0,  180, 255)
C_WALL_GLOW   = (0,   80, 140)
C_PLAYER      = (0,  255, 160)
C_PLAYER_GLOW = (0,  120,  80)
C_ENEMY       = (255,  60,  60)
C_ENEMY_GLOW  = (120,   0,   0)
C_TEXT        = (200, 240, 255)
C_ACCENT      = (0,   255, 200)
C_WARN        = (255, 200,   0)
C_DANGER      = (255,  60,  60)
C_WHITE       = (255, 255, 255)
C_DARK        = (20,   20,  45)
C_HUD_BG      = (10,   10,  28, 200)
C_SCORE       = (0,   255, 200)
C_HEALTH_HI   = (0,   255, 120)
C_HEALTH_MID  = (255, 200,   0)
C_HEALTH_LO   = (255,  60,  60)
C_LEARN_MSG   = (255, 220,  60)

SCORE_FILE = "scores.json"
TILE       = 40   # pixels per tile


# ─────────────────────────────────────────────────────────
#  Level blueprints  (0 = floor, 1 = wall)
# ─────────────────────────────────────────────────────────
def _make_level(level_num: int) -> list:
    """Return a grid (list of list of int) for the given level."""
    # Shared outer border
    base = [
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,0,1],
        [1,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,1],
        [1,0,0,0,1,0,0,0,0,1,1,0,0,0,1,0,0,0,0,1],
        [1,0,1,0,1,0,1,1,0,0,0,0,1,1,0,1,0,1,0,1],
        [1,0,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,0,1],
        [1,0,1,1,1,0,1,1,1,0,0,1,1,1,0,1,1,1,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,1,1,0,1,1,0,0,1,1,0,0,1,1,0,1,1,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,1,0,1,1,0,1,1,0,0,1,1,0,1,1,0,1,0,1],
        [1,0,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,0,1],
        [1,0,0,0,1,0,0,1,0,0,0,0,1,0,0,1,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    ]

    extra = []
    if level_num >= 2:
        extra = [(5,5),(5,6),(6,5),(12,5),(12,6),(13,5)]
    if level_num >= 3:
        extra += [(3,8),(4,8),(5,8),(14,8),(15,8),(16,8)]
    if level_num >= 4:
        extra += [(8,3),(8,4),(9,3),(10,10),(11,10),(10,11)]

    for (r, c) in extra:
        if 0 < r < len(base)-1 and 0 < c < len(base[0])-1:
            base[r][c] = 1

    return base


# ─────────────────────────────────────────────────────────
#  Particle  (visual effects)
# ─────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, vx, vy, life=40, size=4):
        self.x, self.y = x, y
        self.color = color
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.size = size

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surface):
        alpha = max(0, int(255 * self.life / self.max_life))
        r, g, b = self.color
        col = (r, g, b)
        size = max(1, int(self.size * self.life / self.max_life))
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, alpha), (size, size), size)
        surface.blit(s, (int(self.x)-size, int(self.y)-size))


# ─────────────────────────────────────────────────────────
#  Player
# ─────────────────────────────────────────────────────────
class Player:
    BASE_SPEED = 3.2
    RADIUS     = int(TILE * 0.38)

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed   = self.BASE_SPEED
        self.health  = 100
        self.invincible_timer = 0
        self.direction = "NONE"
        self.trail: list[tuple] = []
        self.blink  = 0     # animation counter

    @property
    def rect(self):
        r = self.RADIUS
        return pygame.Rect(self.x - r, self.y - r, r*2, r*2)

    def handle_input(self, keys, walls):
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1; self.direction = "LEFT"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1; self.direction = "RIGHT"
        elif keys[pygame.K_UP]  or keys[pygame.K_w]: dy -= 1; self.direction = "UP"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1; self.direction = "DOWN"
        else: self.direction = "NONE"

        # Axis-split move
        r = self.RADIUS
        if dx != 0:
            nx = self.x + dx * self.speed
            nr = pygame.Rect(nx - r, self.y - r, r*2, r*2)
            if not any(nr.colliderect(w) for w in walls):
                self.x = nx
        if dy != 0:
            ny = self.y + dy * self.speed
            nr = pygame.Rect(self.x - r, ny - r, r*2, r*2)
            if not any(nr.colliderect(w) for w in walls):
                self.y = ny

        # Clamp to screen
        self.x = max(r, min(800 - r, self.x))
        self.y = max(r, min(600 - r, self.y))

        # Trail
        if dx != 0 or dy != 0:
            self.trail.append((self.x, self.y))
        if len(self.trail) > 12:
            self.trail.pop(0)

        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        self.blink += 1

    def take_damage(self, amount=10):
        if self.invincible_timer > 0:
            return False
        self.health = max(0, self.health - amount)
        self.invincible_timer = 90   # 1.5 s invincibility
        return True

    def draw(self, surface):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha_ratio = i / max(1, len(self.trail))
            size = max(2, int(self.RADIUS * 0.5 * alpha_ratio))
            a = int(100 * alpha_ratio)
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_PLAYER, a), (size, size), size)
            surface.blit(s, (int(tx)-size, int(ty)-size))

        # Blink during invincibility
        if self.invincible_timer > 0 and (self.blink // 5) % 2 == 0:
            return

        # Glow
        glow_r = self.RADIUS + 6
        gs = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*C_PLAYER_GLOW, 80), (glow_r, glow_r), glow_r)
        surface.blit(gs, (int(self.x)-glow_r, int(self.y)-glow_r))

        # Body
        pygame.draw.circle(surface, C_PLAYER, (int(self.x), int(self.y)), self.RADIUS)
        pygame.draw.circle(surface, C_WHITE,  (int(self.x), int(self.y)), self.RADIUS, 1)

        # Eye (facing direction)
        eye_offsets = {
            "UP": (0,-8), "DOWN": (0,8), "LEFT": (-8,0), "RIGHT": (8,0), "NONE": (0,0)
        }
        eo = eye_offsets.get(self.direction, (0,0))
        pygame.draw.circle(surface, C_WHITE,
                           (int(self.x)+eo[0], int(self.y)+eo[1]), 4)


# ─────────────────────────────────────────────────────────
#  GameSession
# ─────────────────────────────────────────────────────────
class GameSession:
    SCREEN_W = 800
    SCREEN_H = 600
    FPS      = 60

    def __init__(self, screen: pygame.Surface, fonts: dict):
        self.screen = screen
        self.fonts  = fonts

        self.level      = 1
        self.score      = 0
        self.state      = "PLAYING"   # PLAYING | PAUSED | GAME_OVER | LEVEL_UP
        self.state_timer = 0

        self.particles: list[Particle] = []
        self.high_score = self._load_high_score()

        # Build level
        self._build_level()

    # ────────────────────
    #  Level construction
    # ────────────────────
    def _build_level(self):
        grid = _make_level(self.level)
        self.walls: list[pygame.Rect] = []
        self.grid = grid

        for row_i, row in enumerate(grid):
            for col_i, cell in enumerate(row):
                if cell == 1:
                    self.walls.append(pygame.Rect(
                        col_i * TILE, row_i * TILE, TILE, TILE))

        rows = len(grid)
        cols = len(grid[0])

        # Player spawn: top-left open cell
        self.player = Player(
            1.5 * TILE + 5,
            1.5 * TILE + 5,
        )

        # Enemy spawn: bottom-right open cell
        npc_x = (cols - 2) * TILE + TILE // 2
        npc_y = (rows - 2) * TILE + TILE // 2
        if not hasattr(self, 'npc'):
            self.npc = AdaptiveNPC(npc_x, npc_y, TILE)
        else:
            self.npc.reset_for_level(npc_x, npc_y, self.level)

        # Collectible dots
        self.dots: list[list] = []   # [cx, cy, collected]
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 0:
                    self.dots.append([c*TILE + TILE//2, r*TILE + TILE//2, False])

        self.score_timer = 0

    # ────────────────────
    #  Main update
    # ────────────────────
    def update(self, keys):
        if self.state == "PAUSED":
            return
        if self.state in ("GAME_OVER", "LEVEL_UP"):
            self.state_timer -= 1
            return

        p = self.player
        npc = self.npc

        # Player input
        p.handle_input(keys, self.walls)

        # NPC update
        npc.update(p.x, p.y, p.direction, self.walls)

        # Particle update
        for part in self.particles[:]:
            part.update()
            if part.life <= 0:
                self.particles.remove(part)

        # Score over time
        self.score_timer += 1
        if self.score_timer >= self.FPS:
            self.score += 1
            self.score_timer = 0

        # Dot collection
        pr = p.rect
        for dot in self.dots:
            if not dot[2]:
                dot_rect = pygame.Rect(dot[0]-6, dot[1]-6, 12, 12)
                if pr.colliderect(dot_rect):
                    dot[2] = True
                    self.score += 5
                    self._spawn_collect_particles(dot[0], dot[1])

        # NPC collision
        if pr.colliderect(npc.rect):
            damaged = p.take_damage(10)
            if damaged:
                npc.notify_player_caught()
                self._spawn_hit_particles(p.x, p.y)
                if p.health <= 0:
                    self._end_game()

        # Escape detection (player far from NPC)
        dist = math.hypot(p.x - npc.x, p.y - npc.y)
        if dist > 300:
            npc.notify_player_escaped()

        # Level complete: all dots collected
        if all(d[2] for d in self.dots):
            self._next_level()

    def _next_level(self):
        if self.level >= 4:
            self._end_game(win=True)
            return
        self.level += 1
        self.score += 50 * self.level
        self.state = "LEVEL_UP"
        self.state_timer = self.FPS * 2
        self._build_level()

    def _end_game(self, win=False):
        self.state = "GAME_OVER"
        self.state_timer = self.FPS * 3
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

    # ────────────────────
    #  Draw
    # ────────────────────
    def draw(self):
        surf = self.screen

        # Background
        surf.fill(C_BG)
        self._draw_grid(surf)
        self._draw_walls(surf)
        self._draw_dots(surf)
        self._draw_particles(surf)
        self.player.draw(surf)
        self._draw_npc(surf)
        self._draw_hud(surf)

        if self.state == "PAUSED":
            self._draw_overlay(surf, "⏸  PAUSED", "Press P to resume")
        elif self.state == "LEVEL_UP":
            self._draw_overlay(surf, f"⬆  LEVEL {self.level}!", "Prepare yourself...")
        elif self.state == "GAME_OVER":
            won = self.player.health > 0
            title = "✔  YOU WIN!" if won else "✖  GAME OVER"
            sub   = f"Score: {self.score}  |  High Score: {self.high_score}  |  Press R to restart"
            self._draw_overlay(surf, title, sub, color=C_ACCENT if won else C_DANGER)

    def _draw_grid(self, surf):
        for x in range(0, self.SCREEN_W, TILE):
            pygame.draw.line(surf, C_GRID, (x, 0), (x, self.SCREEN_H))
        for y in range(0, self.SCREEN_H, TILE):
            pygame.draw.line(surf, C_GRID, (0, y), (self.SCREEN_W, y))

    def _draw_walls(self, surf):
        for wall in self.walls:
            pygame.draw.rect(surf, C_WALL_GLOW, wall.inflate(4, 4))
            pygame.draw.rect(surf, C_WALL, wall)
            pygame.draw.rect(surf, (80, 220, 255), wall, 1)

    def _draw_dots(self, surf):
        t = pygame.time.get_ticks()
        for dot in self.dots:
            if not dot[2]:
                pulse = int(4 + 2 * math.sin(t / 300 + dot[0]))
                pygame.draw.circle(surf, C_ACCENT, (dot[0], dot[1]), pulse)
                pygame.draw.circle(surf, C_WHITE,  (dot[0], dot[1]), pulse - 1)

    def _draw_npc(self, surf):
        npc = self.npc
        r = int(TILE * 0.42)
        t = pygame.time.get_ticks()
        pulse = int(5 + 3 * math.sin(t / 200))

        # Glow
        gs = pygame.Surface(((r+pulse)*2, (r+pulse)*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*C_ENEMY_GLOW, 70), (r+pulse, r+pulse), r+pulse)
        surf.blit(gs, (int(npc.x)-(r+pulse), int(npc.y)-(r+pulse)))

        # Body
        pygame.draw.circle(surf, C_ENEMY, (int(npc.x), int(npc.y)), r)
        pygame.draw.circle(surf, (255, 160, 0), (int(npc.x), int(npc.y)), r, 2)

        # Eyes
        for ex, ey in [(-6, -5), (6, -5)]:
            pygame.draw.circle(surf, C_WHITE,
                               (int(npc.x)+ex, int(npc.y)+ey), 4)
            pygame.draw.circle(surf, C_ENEMY_GLOW,
                               (int(npc.x)+ex, int(npc.y)+ey), 2)

        # Predicted target crosshair (debug / visual flair)
        if npc.state in ("PREDICT", "FLANK") and npc.prediction_weight > 0.2:
            tx, ty = npc._compute_target(self.player.x, self.player.y)
            cross_col = (255, 80, 80, 120)
            cs = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.line(cs, cross_col, (10, 0), (10, 20), 1)
            pygame.draw.line(cs, cross_col, (0, 10), (20, 10), 1)
            surf.blit(cs, (int(tx)-10, int(ty)-10))

        # Learning message
        if npc.learning_msg_timer > 0:
            alpha = min(255, npc.learning_msg_timer * 8)
            msg_surf = self.fonts["sm"].render(npc.learning_msg, True, C_LEARN_MSG)
            msg_surf.set_alpha(alpha)
            mx = max(4, min(self.SCREEN_W - msg_surf.get_width() - 4, int(npc.x) - msg_surf.get_width()//2))
            my = int(npc.y) - r - 24
            surf.blit(msg_surf, (mx, my))

    def _draw_hud(self, surf):
        # Top HUD bar
        hud_h = 40
        hud_surf = pygame.Surface((self.SCREEN_W, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (8, 8, 25, 210), (0, 0, self.SCREEN_W, hud_h))
        surf.blit(hud_surf, (0, 0))
        pygame.draw.line(surf, C_WALL, (0, hud_h), (self.SCREEN_W, hud_h), 1)

        # Score
        score_txt = self.fonts["md"].render(f"SCORE  {self.score:06d}", True, C_SCORE)
        surf.blit(score_txt, (12, 8))

        # High score
        hs_txt = self.fonts["sm"].render(f"BEST {self.high_score:06d}", True, C_TEXT)
        surf.blit(hs_txt, (self.SCREEN_W // 2 - hs_txt.get_width()//2, 12))

        # Level
        lv_txt = self.fonts["md"].render(f"LV {self.level}", True, C_ACCENT)
        surf.blit(lv_txt, (self.SCREEN_W - lv_txt.get_width() - 12, 8))

        # Bottom HUD bar
        bot_y = self.SCREEN_H - 36
        bot_surf = pygame.Surface((self.SCREEN_W, 36), pygame.SRCALPHA)
        pygame.draw.rect(bot_surf, (8, 8, 25, 210), (0, 0, self.SCREEN_W, 36))
        surf.blit(bot_surf, (0, bot_y))
        pygame.draw.line(surf, C_WALL, (0, bot_y), (self.SCREEN_W, bot_y), 1)

        # Health bar
        hp = self.player.health
        hp_pct = hp / 100.0
        if hp_pct > 0.5:  hp_col = C_HEALTH_HI
        elif hp_pct > 0.25: hp_col = C_HEALTH_MID
        else:               hp_col = C_HEALTH_LO

        label = self.fonts["sm"].render("HP", True, C_TEXT)
        surf.blit(label, (12, bot_y + 10))
        bar_x = 40
        pygame.draw.rect(surf, C_DARK,   (bar_x, bot_y+10, 160, 14), border_radius=4)
        pygame.draw.rect(surf, hp_col,   (bar_x, bot_y+10, int(160*hp_pct), 14), border_radius=4)
        pygame.draw.rect(surf, C_TEXT,   (bar_x, bot_y+10, 160, 14), 1, border_radius=4)

        hp_num = self.fonts["sm"].render(f"{hp}%", True, C_TEXT)
        surf.blit(hp_num, (206, bot_y + 10))

        # AI threat meter
        thr = self.npc.threat_level
        thr_label = self.fonts["sm"].render("AI THREAT", True, C_TEXT)
        surf.blit(thr_label, (self.SCREEN_W - 250, bot_y + 10))
        for i in range(5):
            col = C_DANGER if i < thr else C_DARK
            pygame.draw.rect(surf, col, (self.SCREEN_W - 165 + i*26, bot_y+10, 22, 14), border_radius=3)
            if i < thr:
                pygame.draw.rect(surf, C_WHITE, (self.SCREEN_W - 165 + i*26, bot_y+10, 22, 14), 1, border_radius=3)

        # AI behaviour state
        state_txt = self.fonts["xs"].render(
            f"AI: {self.npc.state}  |  P to pause  |  R to restart", True, C_TEXT)
        surf.blit(state_txt, (self.SCREEN_W//2 - state_txt.get_width()//2, bot_y + 12))

        # Learning progress bar
        lp = self.npc.learning_progress
        if lp > 0:
            lp_label = self.fonts["xs"].render("LEARNING", True, C_LEARN_MSG)
            surf.blit(lp_label, (12, bot_y - 18))
            pygame.draw.rect(surf, C_DARK, (12, bot_y - 8, 100, 6), border_radius=3)
            pygame.draw.rect(surf, C_LEARN_MSG, (12, bot_y - 8, int(100*lp), 6), border_radius=3)

    def _draw_overlay(self, surf, title, subtitle, color=C_ACCENT):
        # Dark veil
        veil = pygame.Surface((self.SCREEN_W, self.SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(veil, (0, 0, 0, 160), (0, 0, self.SCREEN_W, self.SCREEN_H))
        surf.blit(veil, (0, 0))

        # Panel
        pw, ph = 520, 140
        px = (self.SCREEN_W - pw) // 2
        py = (self.SCREEN_H - ph) // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 10, 30, 230), (0, 0, pw, ph), border_radius=12)
        pygame.draw.rect(panel, color, (0, 0, pw, ph), 2, border_radius=12)
        surf.blit(panel, (px, py))

        t_surf = self.fonts["lg"].render(title, True, color)
        surf.blit(t_surf, (px + (pw - t_surf.get_width())//2, py + 18))

        s_surf = self.fonts["xs"].render(subtitle, True, C_TEXT)
        surf.blit(s_surf, (px + (pw - s_surf.get_width())//2, py + 80))

    # ────────────────────
    #  Particles
    # ────────────────────
    def _spawn_collect_particles(self, x, y):
        for _ in range(10):
            vx = random.uniform(-2, 2)
            vy = random.uniform(-3, 0)
            self.particles.append(Particle(x, y, C_ACCENT, vx, vy, life=35, size=3))

    def _spawn_hit_particles(self, x, y):
        for _ in range(18):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(1, 4)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(x, y, C_DANGER, vx, vy, life=45, size=5))

    def _draw_particles(self, surf):
        for p in self.particles:
            p.draw(surf)

    # ────────────────────
    #  High score
    # ────────────────────
    def _load_high_score(self) -> int:
        try:
            with open(SCORE_FILE) as f:
                data = json.load(f)
                return int(data.get("high_score", 0))
        except Exception:
            return 0

    def _save_high_score(self):
        try:
            with open(SCORE_FILE, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass
