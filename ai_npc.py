"""
ai_npc.py  –  Adaptive AI Opponent System
==========================================
Implements a pattern-learning enemy that:
  • Tracks player movement history
  • Builds a direction-frequency model
  • Predicts next player position
  • Scales speed / aggression based on player skill
  • Displays real-time "AI learning" feedback messages

ML Technique: Lightweight Online Frequency-Based Pattern Analysis + Adaptive Difficulty
Dependencies: numpy (no heavy ML framework needed for demo; scikit-learn optional extension)
"""

import math
import random
import numpy as np


# ──────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────
DIRECTIONS = ["UP", "DOWN", "LEFT", "RIGHT", "NONE"]
DIR_VECTORS = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
    "NONE":  (0,  0),
}

LEARNING_MESSAGES = [
    "Enemy analysing your moves...",
    "Enemy is learning your patterns!",
    "AI updated: predicting your path!",
    "Threat level increasing...",
    "Enemy detected escape route!",
    "Pattern recognised – adapting!",
    "AI confidence: RISING",
    "Enemy locked onto your strategy!",
]


# ──────────────────────────────────────────────
#  AdaptiveNPC
# ──────────────────────────────────────────────
class AdaptiveNPC:
    """
    An enemy that observes the player's movement history and adapts its
    pursuit strategy using direction-frequency analysis and skill scoring.
    """

    def __init__(self, x: float, y: float, tile_size: int = 40):
        # ── Position & movement ──
        self.x = float(x)
        self.y = float(y)
        self.tile_size = tile_size

        self.base_speed   = 1.8          # starting movement speed (px/frame)
        self.speed        = self.base_speed
        self.max_speed    = 4.5          # hard cap
        self.vel_x        = 0.0
        self.vel_y        = 0.0

        # ── ML: player history ──
        self.history_size      = 60           # frames of history retained
        self.direction_counts  = np.zeros(5)  # UP/DOWN/LEFT/RIGHT/NONE
        self.position_history  = []           # list of (px, py) tuples
        self.reaction_times    = []           # frames between direction changes
        self.last_dir          = "NONE"
        self.frames_in_dir     = 0

        # ── Skill / difficulty tracking ──
        self.player_skill_score = 0.0   # 0 = novice, 1 = expert
        self.escapes_detected   = 0     # times player evaded successfully
        self.hits_landed        = 0     # times NPC caught player
        self.observation_frames = 0

        # ── Prediction state ──
        self.predicted_target   = None   # (x, y) predicted next position
        self.prediction_weight  = 0.0   # how much to trust prediction vs direct chase
        self.last_dominant_dir  = "NONE"

        # ── Learning UI ──
        self.learning_msg         = ""
        self.learning_msg_timer   = 0
        self.learning_msg_duration = 180   # frames to show message
        self._msg_cooldown         = 0

        # ── Behaviour state ──
        self.state = "CHASE"   # CHASE | PREDICT | FLANK
        self.flank_offset = (0, 0)

    # ─────────────────────────────
    #  Public API called each frame
    # ─────────────────────────────
    def update(self, player_x: float, player_y: float,
               player_direction: str, walls: list, dt: float = 1.0):
        """
        Main update method. Call once per game frame.

        Parameters
        ----------
        player_x / player_y : current player centre position
        player_direction     : string from DIRECTIONS
        walls                : list of pygame.Rect objects (obstacles)
        dt                   : delta-time multiplier (default 1.0 at 60 fps)
        """
        self.observation_frames += 1

        # 1. Record player data
        self._record_player_data(player_x, player_y, player_direction)

        # 2. Update ML model every 30 frames
        if self.observation_frames % 30 == 0:
            self._update_model()

        # 3. Decide behaviour state
        self._update_behaviour_state()

        # 4. Compute target position
        target_x, target_y = self._compute_target(player_x, player_y)

        # 5. Move toward target (with basic wall avoidance)
        self._move_toward(target_x, target_y, walls, dt)

        # 6. Tick UI message timer
        if self.learning_msg_timer > 0:
            self.learning_msg_timer -= 1
        if self._msg_cooldown > 0:
            self._msg_cooldown -= 1

    # ─────────────────────────────
    #  Private helpers
    # ─────────────────────────────
    def _record_player_data(self, px: float, py: float, direction: str):
        """Append latest player data to history buffers."""
        # Position history (capped)
        self.position_history.append((px, py))
        if len(self.position_history) > self.history_size:
            self.position_history.pop(0)

        # Direction frequency
        idx = DIRECTIONS.index(direction) if direction in DIRECTIONS else 4
        self.direction_counts[idx] += 1

        # Reaction time (frames spent in same direction)
        if direction == self.last_dir:
            self.frames_in_dir += 1
        else:
            if self.frames_in_dir > 0:
                self.reaction_times.append(self.frames_in_dir)
                if len(self.reaction_times) > 30:
                    self.reaction_times.pop(0)
            self.frames_in_dir = 1
            self.last_dir = direction

    def _update_model(self):
        """
        Recompute ML-derived metrics and adjust NPC behaviour.
        This is the core 'learning' step.
        """
        total = self.direction_counts.sum()
        if total < 10:
            return  # Not enough data yet

        # Normalise direction frequencies → probability distribution
        probs = self.direction_counts / total

        # Dominant direction the player favours
        dominant_idx = int(np.argmax(probs[:4]))   # exclude NONE
        self.last_dominant_dir = DIRECTIONS[dominant_idx]

        # Prediction weight grows as NPC accumulates observations
        self.prediction_weight = min(0.85, total / 300.0)

        # Player skill: high skill → many direction changes, long survival
        if self.reaction_times:
            avg_reaction = np.mean(self.reaction_times)
            # Short reaction time = quick changes = higher skill
            skill_from_reaction = 1.0 - min(1.0, avg_reaction / 90.0)
        else:
            skill_from_reaction = 0.0

        survival_bonus = min(0.5, self.observation_frames / 1800.0)
        self.player_skill_score = min(1.0, skill_from_reaction * 0.6
                                      + survival_bonus * 0.4)

        # Adapt speed based on skill
        new_speed = self.base_speed + self.player_skill_score * (self.max_speed - self.base_speed)
        # Smooth speed transition
        self.speed += (new_speed - self.speed) * 0.1
        self.speed  = max(self.base_speed, min(self.max_speed, self.speed))

        # Emit a learning message periodically
        self._maybe_emit_message()

    def _update_behaviour_state(self):
        """Switch between CHASE / PREDICT / FLANK based on observation depth."""
        obs = self.observation_frames
        skill = self.player_skill_score

        if obs < 120 or skill < 0.2:
            self.state = "CHASE"
        elif skill < 0.55:
            self.state = "PREDICT"
        else:
            # High-skill player: try flanking
            self.state = "FLANK" if random.random() < 0.3 else "PREDICT"

    def _compute_target(self, px: float, py: float):
        """
        Return (target_x, target_y) based on current behaviour state.
        """
        if self.state == "CHASE" or len(self.position_history) < 5:
            return px, py

        if self.state == "PREDICT":
            return self._predict_position(px, py)

        # FLANK: aim for a position perpendicular to player's dominant direction
        return self._flank_position(px, py)

    def _predict_position(self, px: float, py: float):
        """
        Weighted prediction: blend direct chase with extrapolated player motion.
        """
        if len(self.position_history) < 5:
            return px, py

        # Average recent velocity
        recent = self.position_history[-5:]
        dx = (recent[-1][0] - recent[0][0]) / 4.0
        dy = (recent[-1][1] - recent[0][1]) / 4.0

        look_ahead = 15  # frames ahead
        pred_x = px + dx * look_ahead
        pred_y = py + dy * look_ahead

        # Blend prediction with direct position
        w = self.prediction_weight
        target_x = w * pred_x + (1 - w) * px
        target_y = w * pred_y + (1 - w) * py
        return target_x, target_y

    def _flank_position(self, px: float, py: float):
        """
        Aim for a position offset perpendicular to the player's dominant direction,
        to cut off escape routes.
        """
        dom = self.last_dominant_dir
        flank_dist = self.tile_size * 3

        offsets = {
            "UP":    (flank_dist, 0),
            "DOWN":  (-flank_dist, 0),
            "LEFT":  (0, flank_dist),
            "RIGHT": (0, -flank_dist),
            "NONE":  (0, 0),
        }
        ox, oy = offsets.get(dom, (0, 0))

        # Alternate flank side each time to be unpredictable
        if self.observation_frames % 240 < 120:
            ox, oy = -ox, -oy

        return px + ox, py + oy

    def _move_toward(self, tx: float, ty: float, walls: list, dt: float):
        """Steer NPC toward (tx, ty) with simple collision response."""
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)

        if dist < 1:
            self.vel_x = self.vel_y = 0.0
            return

        # Normalise and scale
        speed = self.speed * dt
        self.vel_x = (dx / dist) * speed
        self.vel_y = (dy / dist) * speed

        # Try full move
        new_x = self.x + self.vel_x
        new_y = self.y + self.vel_y

        # Axis-split collision (allows sliding along walls)
        half = self.tile_size * 0.4   # collision radius
        from pygame import Rect
        npc_rect_x = Rect(new_x - half, self.y - half, half * 2, half * 2)
        npc_rect_y = Rect(self.x - half, new_y - half, half * 2, half * 2)

        blocked_x = any(npc_rect_x.colliderect(w) for w in walls)
        blocked_y = any(npc_rect_y.colliderect(w) for w in walls)

        if not blocked_x:
            self.x = new_x
        else:
            # Nudge horizontally
            self.vel_x = -self.vel_x * 0.3

        if not blocked_y:
            self.y = new_y
        else:
            self.vel_y = -self.vel_y * 0.3

    # ─────────────────────────────
    #  Learning message
    # ─────────────────────────────
    def _maybe_emit_message(self):
        if self._msg_cooldown > 0:
            return
        # Chance increases with skill score
        chance = 0.1 + self.player_skill_score * 0.4
        if random.random() < chance:
            self.learning_msg       = random.choice(LEARNING_MESSAGES)
            self.learning_msg_timer = self.learning_msg_duration
            self._msg_cooldown      = 200  # min gap between messages

    # ─────────────────────────────
    #  External event hooks
    # ─────────────────────────────
    def notify_player_escaped(self):
        """Call when player successfully creates distance."""
        self.escapes_detected += 1
        if self.escapes_detected % 3 == 0:
            self.base_speed = min(self.base_speed + 0.15, 3.5)
        self._force_message("Pattern detected – increasing aggression!")

    def notify_player_caught(self):
        """Call when NPC collides with player."""
        self.hits_landed += 1

    def reset_for_level(self, new_x: float, new_y: float, level: int):
        """Re-position NPC and scale base speed for new level."""
        self.x = float(new_x)
        self.y = float(new_y)
        self.base_speed = min(1.8 + (level - 1) * 0.25, 3.5)
        self.speed      = self.base_speed
        self.state      = "CHASE"
        self.observation_frames = 0

    def _force_message(self, msg: str):
        self.learning_msg       = msg
        self.learning_msg_timer = self.learning_msg_duration
        self._msg_cooldown      = 300

    # ─────────────────────────────
    #  Read-only properties
    # ─────────────────────────────
    @property
    def rect(self):
        """Pygame Rect for collision detection."""
        from pygame import Rect
        half = self.tile_size * 0.4
        return Rect(self.x - half, self.y - half, half * 2, half * 2)

    @property
    def skill_label(self) -> str:
        s = self.player_skill_score
        if s < 0.25:  return "Novice"
        if s < 0.50:  return "Intermediate"
        if s < 0.75:  return "Advanced"
        return "Expert"

    @property
    def threat_level(self) -> int:
        """0–5 threat level for HUD display."""
        return min(5, int(self.player_skill_score * 5) + 1)

    @property
    def learning_progress(self) -> float:
        """0–1 float for progress bar."""
        return min(1.0, self.observation_frames / 600.0)

    def get_stats_dict(self) -> dict:
        """Return stats for debug / report overlay."""
        return {
            "State":       self.state,
            "Speed":       f"{self.speed:.2f}",
            "Skill score": f"{self.player_skill_score:.2f}",
            "Pred weight": f"{self.prediction_weight:.2f}",
            "Dom dir":     self.last_dominant_dir,
            "Observations": self.observation_frames,
        }
