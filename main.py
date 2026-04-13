"""
main.py  –  Adaptive AI Opponent System for Dynamic Gaming Experience
=====================================================================
Entry point: handles pygame init, loading screen, main menu, and
game loop integration.

Run:
    python main.py

Controls:
    Arrow keys / WASD  →  move player
    P                  →  pause / resume
    R                  →  restart
    ESC                →  quit to menu
"""

import pygame
import sys
import math
import random
import time

from game import GameSession, C_BG, C_WALL, C_ACCENT, C_TEXT, C_DANGER, C_PLAYER, C_ENEMY, TILE


# ─────────────────────────────────────────────────────────
#  Window settings
# ─────────────────────────────────────────────────────────
SCREEN_W = 800
SCREEN_H = 600
FPS      = 60
TITLE    = "Adaptive AI Opponent  |  B.Tech CSE (AI & ML) Special Project"


# ─────────────────────────────────────────────────────────
#  Colour helpers (local)
# ─────────────────────────────────────────────────────────
C_WHITE  = (255, 255, 255)
C_DARK   = (8,   8,  20)
C_NEON_B = (0,  200, 255)
C_NEON_G = (0,  255, 160)
C_NEON_R = (255,  60,  60)
C_GOLD   = (255, 200,  50)
C_GRID   = (15,  15,  35)


# ─────────────────────────────────────────────────────────
#  Utility – draw glowing text
# ─────────────────────────────────────────────────────────
def draw_glow_text(surface, font, text, x, y, color, glow_color=None,
                   glow_passes=3, center=False):
    if glow_color is None:
        glow_color = tuple(min(255, c//2) for c in color)

    base = font.render(text, True, color)
    glow = font.render(text, True, glow_color)

    if center:
        x -= base.get_width() // 2

    for dx in range(-glow_passes, glow_passes + 1):
        for dy in range(-glow_passes, glow_passes + 1):
            if dx != 0 or dy != 0:
                gs = pygame.Surface(glow.get_size(), pygame.SRCALPHA)
                gs.blit(glow, (0, 0))
                gs.set_alpha(40)
                surface.blit(gs, (x + dx, y + dy))
    surface.blit(base, (x, y))


# ─────────────────────────────────────────────────────────
#  Star field (background decoration)
# ─────────────────────────────────────────────────────────
class Stars:
    def __init__(self, n=120):
        self.stars = [(random.randint(0, SCREEN_W),
                       random.randint(0, SCREEN_H),
                       random.uniform(0.3, 1.5)) for _ in range(n)]

    def draw(self, surface, t):
        for (sx, sy, speed) in self.stars:
            bright = int(128 + 80 * math.sin(t * speed + sx))
            r = max(1, int(speed))
            pygame.draw.circle(surface, (bright, bright, bright+40), (sx, sy), r)


# ─────────────────────────────────────────────────────────
#  Loading screen
# ─────────────────────────────────────────────────────────
def loading_screen(screen, fonts, clock):
    steps = [
        "Initialising game engine...",
        "Loading assets...",
        "Building AI neural pathfinder...",
        "Calibrating pattern analyser...",
        "Spawning enemy AI...",
        "Ready!",
    ]
    stars = Stars(80)
    for i, step in enumerate(steps):
        progress = (i + 1) / len(steps)

        screen.fill(C_DARK)

        t = time.time()
        stars.draw(screen, t)

        # Title
        draw_glow_text(screen, fonts["xl"], "ADAPTIVE AI OPPONENT",
                       SCREEN_W//2, 140, C_NEON_B, center=True)
        draw_glow_text(screen, fonts["sm"], "B.Tech CSE (AI & ML)  –  Special Project",
                       SCREEN_W//2, 192, C_TEXT, center=True)

        # Progress bar
        bar_w, bar_h = 500, 22
        bx = (SCREEN_W - bar_w) // 2
        by = 300
        pygame.draw.rect(screen, (20, 20, 50), (bx, by, bar_w, bar_h), border_radius=8)
        fill_w = int(bar_w * progress)
        pygame.draw.rect(screen, C_NEON_B, (bx, by, fill_w, bar_h), border_radius=8)
        pygame.draw.rect(screen, C_TEXT,   (bx, by, bar_w, bar_h), 1, border_radius=8)

        # Percentage
        pct_txt = fonts["sm"].render(f"{int(progress*100)}%", True, C_TEXT)
        screen.blit(pct_txt, (SCREEN_W//2 - pct_txt.get_width()//2, by + 30))

        # Step text
        step_surf = fonts["sm"].render(step, True, C_ACCENT)
        screen.blit(step_surf, (SCREEN_W//2 - step_surf.get_width()//2, by + 58))

        pygame.display.flip()
        clock.tick(10)

        # Flush events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        pygame.time.delay(160 if i < len(steps)-1 else 500)


# ─────────────────────────────────────────────────────────
#  Main menu
# ─────────────────────────────────────────────────────────
class MainMenu:
    OPTIONS = ["START GAME", "INSTRUCTIONS", "EXIT"]

    def __init__(self, screen, fonts, clock):
        self.screen = screen
        self.fonts  = fonts
        self.clock  = clock
        self.selected = 0
        self.stars    = Stars(120)
        self.t        = 0.0
        # Floating particles for aesthetics
        self.ptcls = [(random.randint(0, SCREEN_W),
                       random.randint(0, SCREEN_H),
                       random.uniform(-0.4, 0.4),
                       random.uniform(-0.8, -0.2)) for _ in range(40)]

    def run(self) -> str:
        """Block until user selects an option. Returns one of OPTIONS."""
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.t += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.selected = (self.selected - 1) % len(self.OPTIONS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected = (self.selected + 1) % len(self.OPTIONS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return self.OPTIONS[self.selected]
                    elif event.key == pygame.K_ESCAPE:
                        return "EXIT"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for i, opt in enumerate(self.OPTIONS):
                        oy = 310 + i * 64
                        if oy - 20 < my < oy + 20 and abs(mx - SCREEN_W//2) < 160:
                            return opt

            self._draw()

    def _draw(self):
        surf = self.screen
        surf.fill(C_DARK)

        # Grid
        for x in range(0, SCREEN_W, TILE):
            pygame.draw.line(surf, C_GRID, (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, TILE):
            pygame.draw.line(surf, C_GRID, (0, y), (SCREEN_W, y))

        self.stars.draw(surf, self.t)

        # Floating particles
        for i, (px, py, vx, vy) in enumerate(self.ptcls):
            self.ptcls[i] = ((px + vx) % SCREEN_W, (py + vy) % SCREEN_H, vx, vy)
            alpha = int(80 + 60 * math.sin(self.t * 1.5 + px))
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_NEON_B, alpha), (2, 2), 2)
            surf.blit(s, (int(px), int(py)))

        # Animated title
        wave = int(4 * math.sin(self.t * 2))
        draw_glow_text(surf, self.fonts["xl"], "ADAPTIVE AI OPPONENT",
                       SCREEN_W//2, 80 + wave, C_NEON_B, center=True, glow_passes=4)

        subtitle_col = (
            int(128 + 127 * math.sin(self.t * 1.2)),
            200,
            int(128 + 127 * math.sin(self.t * 1.2 + 2)),
        )
        draw_glow_text(surf, self.fonts["sm"], "Dynamic Gaming Experience using Machine Learning",
                       SCREEN_W//2, 136, subtitle_col, center=True)

        # Divider line
        line_prog = min(1.0, self.t / 1.0)
        lw = int(600 * line_prog)
        pygame.draw.line(surf, C_NEON_B,
                         (SCREEN_W//2 - lw//2, 170),
                         (SCREEN_W//2 + lw//2, 170), 1)

        # Menu options
        for i, opt in enumerate(self.OPTIONS):
            oy = 310 + i * 64
            selected = (i == self.selected)

            if selected:
                # Highlight box
                bw = 280
                pulse = int(2 * math.sin(self.t * 4))
                hbox = pygame.Surface((bw + pulse*2, 44), pygame.SRCALPHA)
                pygame.draw.rect(hbox, (*C_NEON_B, 30), (0, 0, bw+pulse*2, 44), border_radius=8)
                pygame.draw.rect(hbox, C_NEON_B, (0, 0, bw+pulse*2, 44), 2, border_radius=8)
                surf.blit(hbox, (SCREEN_W//2 - (bw+pulse*2)//2, oy - 14))

            color = C_NEON_B if selected else C_TEXT
            glow  = (0, 80, 120) if selected else (60, 60, 80)
            draw_glow_text(surf, self.fonts["md"], opt,
                           SCREEN_W//2, oy - 6, color, glow, center=True,
                           glow_passes=2 if selected else 1)

        # Enemy mini preview (animated)
        ex = 100 + int(30 * math.sin(self.t))
        ey = 480 + int(8 * math.sin(self.t * 1.3))
        pygame.draw.circle(surf, C_NEON_R, (ex, ey), 16)
        pygame.draw.circle(surf, (255, 120, 0), (ex, ey), 16, 2)

        px = SCREEN_W - 100 + int(20 * math.sin(self.t + 2))
        py = 480 + int(8 * math.sin(self.t * 1.3 + 1))
        pygame.draw.circle(surf, C_NEON_G, (px, py), 14)
        pygame.draw.circle(surf, C_WHITE, (px, py), 14, 1)

        # Controls hint
        ctrl = self.fonts["xs"].render("↑↓ Navigate   ENTER Select   ESC Quit", True, (100, 130, 160))
        surf.blit(ctrl, (SCREEN_W//2 - ctrl.get_width()//2, SCREEN_H - 28))

        pygame.display.flip()


# ─────────────────────────────────────────────────────────
#  Instructions screen
# ─────────────────────────────────────────────────────────
def instructions_screen(screen, fonts, clock):
    lines = [
        ("OBJECTIVE",          (0, 220, 255)),
        ("  Collect all glowing dots to advance levels.", (200, 240, 255)),
        ("  Avoid the red AI enemy — it learns your moves!", (200, 240, 255)),
        ("", None),
        ("CONTROLS",           (0, 220, 255)),
        ("  Arrow Keys / WASD  →  Move player", (200, 240, 255)),
        ("  P                 →  Pause / Resume", (200, 240, 255)),
        ("  R                 →  Restart game", (200, 240, 255)),
        ("  ESC               →  Back to menu", (200, 240, 255)),
        ("", None),
        ("AI BEHAVIOUR",       (0, 220, 255)),
        ("  ▸ CHASE   : direct pursuit (early game)", (200, 240, 255)),
        ("  ▸ PREDICT : extrapolates your trajectory", (200, 240, 255)),
        ("  ▸ FLANK   : cuts off your escape routes", (200, 240, 255)),
        ("", None),
        ("  Watch the 'AI THREAT' bar grow over time!", (255, 200, 60)),
        ("", None),
        ("         Press any key to return to menu", (120, 160, 200)),
    ]

    stars = Stars(80)
    t = 0.0
    while True:
        dt = clock.tick(FPS) / 1000.0
        t += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return

        screen.fill(C_DARK)
        for x in range(0, SCREEN_W, TILE):
            pygame.draw.line(screen, C_GRID, (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, TILE):
            pygame.draw.line(screen, C_GRID, (0, y), (SCREEN_W, y))
        stars.draw(screen, t)

        draw_glow_text(screen, fonts["lg"], "INSTRUCTIONS",
                       SCREEN_W//2, 30, C_NEON_B, center=True)
        pygame.draw.line(screen, C_NEON_B,
                         (SCREEN_W//2 - 200, 74), (SCREEN_W//2 + 200, 74), 1)

        y = 90
        for text, col in lines:
            if text == "":
                y += 10
                continue
            if col:
                surf_t = fonts["sm"].render(text, True, col)
                screen.blit(surf_t, (SCREEN_W//2 - 280, y))
            y += 22

        pygame.display.flip()


# ─────────────────────────────────────────────────────────
#  Main game loop
# ─────────────────────────────────────────────────────────
def game_loop(screen, fonts, clock):
    session = GameSession(screen, fonts)
    restart_pending = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return   # back to menu
                if event.key == pygame.K_p:
                    if session.state == "PLAYING":
                        session.state = "PAUSED"
                    elif session.state == "PAUSED":
                        session.state = "PLAYING"
                if event.key == pygame.K_r:
                    session = GameSession(screen, fonts)

        keys = pygame.key.get_pressed()
        session.update(keys)
        session.draw()
        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────────────────
#  Bootstrap
# ─────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()

    # Font loading (falls back to system font)
    def load_font(size, bold=False):
        try:
            return pygame.font.SysFont("consolas", size, bold=bold)
        except Exception:
            return pygame.font.Font(None, size)

    fonts = {
        "xs": load_font(16),
        "sm": load_font(20),
        "md": load_font(26, bold=True),
        "lg": load_font(36, bold=True),
        "xl": load_font(48, bold=True),
    }

    # Loading screen
    loading_screen(screen, fonts, clock)

    # App loop
    menu = MainMenu(screen, fonts, clock)
    while True:
        choice = menu.run()

        if choice == "START GAME":
            game_loop(screen, fonts, clock)
        elif choice == "INSTRUCTIONS":
            instructions_screen(screen, fonts, clock)
        elif choice == "EXIT":
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    main()
