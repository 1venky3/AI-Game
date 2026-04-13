# 🎮 Adaptive AI Opponent System for Dynamic Gaming Experience
### B.Tech CSE (AI & ML) — Special Project

---

## 📋 Project Overview

A **2D maze-chase survival game** built in Python where an intelligent AI enemy
**learns the player's behaviour in real-time** and dynamically adapts its pursuit
strategy. This project demonstrates core AI/ML concepts — pattern analysis,
online learning, adaptive difficulty — in an interactive gaming context.

---

## 🚀 Quick Start (VS Code)

### 1. Install Python (≥ 3.9)
Download from https://www.python.org/downloads/

### 2. Open folder in VS Code
```
File → Open Folder → select adaptive_ai_game/
```

### 3. Install dependencies
Open VS Code terminal (`Ctrl + `` `) and run:
```bash
pip install -r requirements.txt
```

### 4. Run the game
```bash
python main.py
```

---

## 🎯 Controls

| Key              | Action            |
|------------------|-------------------|
| Arrow keys / WASD | Move player       |
| P                | Pause / Resume    |
| R                | Restart           |
| ESC              | Back to main menu |

---

## 📁 File Structure

```
adaptive_ai_game/
│
├── main.py          ← Entry point: menu, loading screen, game loop
├── game.py          ← Game world, player, rendering, HUD, score system
├── ai_npc.py        ← Adaptive AI enemy (ML pattern analysis)
├── requirements.txt ← Python dependencies
├── README.md        ← This file
└── scores.json      ← Auto-created; stores high score
```

---

## 🤖 AI / ML Logic Explained

### Core Technique: Online Direction-Frequency Analysis

The enemy (`AdaptiveNPC` in `ai_npc.py`) uses **real-time pattern analysis**:

1. **Data Collection** — Every frame, the NPC records:
   - Player's current direction (UP/DOWN/LEFT/RIGHT)
   - Player's position (x, y)
   - How many frames the player holds each direction

2. **Frequency Model** (using NumPy)
   ```python
   self.direction_counts  # shape (5,) — UP/DOWN/LEFT/RIGHT/NONE
   probs = self.direction_counts / total  # probability distribution
   ```

3. **Skill Score Computation**
   ```python
   # Short average reaction time → high skill
   skill = 1 - min(1, avg_reaction_frames / 90)
   ```

4. **Behaviour States**
   | State    | When               | Action                            |
   |----------|--------------------|-----------------------------------|
   | CHASE    | < 120 obs / low skill | Direct pursuit                |
   | PREDICT  | Medium skill       | Extrapolates trajectory ahead     |
   | FLANK    | High skill         | Cuts off dominant escape direction|

5. **Speed Adaptation**
   ```python
   speed = base_speed + skill_score × (max_speed - base_speed)
   ```

6. **Prediction Formula**
   ```python
   # Average recent velocity over last 5 frames
   predicted_pos = current_pos + avg_velocity × 15_frames_ahead
   target = prediction_weight × predicted + (1 - w) × direct
   ```

### Why No Heavy ML Library Needed
The frequency-based online model updates every 30 frames and runs in O(1),
making it suitable for real-time gaming without GPU or heavy frameworks.
`scikit-learn` is listed as an optional dependency for students who want to
extend it with a proper classifier (e.g., KNN on direction sequences).

---

## 🏆 Game Features

- ✅ Main menu with animated neon UI
- ✅ Loading screen with progress bar
- ✅ 4 levels of increasing complexity
- ✅ Adaptive enemy AI (3 behaviour modes)
- ✅ Score counter (survival time + dot collection)
- ✅ Health bar with damage flash + invincibility frames
- ✅ AI threat meter (5-level)
- ✅ "Enemy is learning" on-screen messages
- ✅ Learning progress bar
- ✅ Particle effects (hits, collection)
- ✅ Player trail animation
- ✅ High score persistence (scores.json)
- ✅ Pause / restart support
- ✅ Game over & win screens

---

## 🔧 Extending the Project

| Extension             | File to modify          |
|-----------------------|-------------------------|
| Add new levels        | `game.py → _make_level()`|
| Change AI aggression  | `ai_npc.py → max_speed` |
| Add a second enemy    | Create another `AdaptiveNPC`|
| Sound effects         | Add `pygame.mixer` calls|
| Scikit-learn KNN      | `ai_npc.py → _update_model()`|

---

## 📊 Sample AI Output (Console Debug)

```
Observation  30 : State=CHASE   Speed=1.80  Skill=0.00
Observation  60 : State=CHASE   Speed=1.84  Skill=0.05
Observation 120 : State=PREDICT Speed=2.10  Skill=0.23
Observation 300 : State=PREDICT Speed=2.80  Skill=0.55
Observation 600 : State=FLANK   Speed=3.50  Skill=0.82
```

---

## 👨‍💻 Project Info

- **Language**: Python 3.9+
- **Libraries**: Pygame, NumPy, (optional) Scikit-learn
- **AI Technique**: Online Frequency Pattern Analysis + Adaptive Difficulty
- **Domain**: Artificial Intelligence × Game Development
- **Category**: B.Tech CSE (AI & ML) Special Project

---

*Built with ❤️ for college demo. Fully runnable in VS Code.*
