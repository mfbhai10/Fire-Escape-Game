"""
Configuration for the Fire Escape AI Game.

This module centralizes all game constants:
- Grid size and cell size (controls window size)
- Game modes: MANUAL, AI_AUTO, CHALLENGE
- Difficulty levels: EASY, MEDIUM, HARD
- Colors for rendering (board, cells, text)
- Cell symbols and movement costs
- Difficulty settings (board size, timer, fire spread, score multiplier)

Difficulty Settings Control:
- Board size (10x10 to 20x20)
- Time limit (90s to 45s)
- Fire spread frequency and probability
- Score multiplier (easier = lower multiplier)

To adjust game balance, edit DIFFICULTY_SETTINGS dictionary.
To change colors, edit the color constants (COLOR_* variables).
"""

# Grid and screen layout
GRID_ROWS = 15
GRID_COLS = 15
CELL_SIZE = 40
SCREEN_WIDTH = GRID_COLS * CELL_SIZE
SCREEN_HEIGHT = GRID_ROWS * CELL_SIZE

# Backward-compatible grid aliases used by the current game files
GRID_WIDTH = GRID_COLS
GRID_HEIGHT = GRID_ROWS

# Frame rate
FPS = 60

# Game modes
MODE_MANUAL = "MANUAL"
MODE_AI_AUTO = "AI AUTO"
MODE_CHALLENGE = "CHALLENGE"

# AI settings
AI_MOVE_DELAY_MS = 200

# Difficulty levels (used by Challenge Mode scaffolding)
DIFFICULTY_EASY = "EASY"
DIFFICULTY_MEDIUM = "MEDIUM"
DIFFICULTY_HARD = "HARD"
DEFAULT_DIFFICULTY = DIFFICULTY_MEDIUM

# Central difficulty settings used by board generation, timer, and fire spread.
DIFFICULTY_SETTINGS = {
	DIFFICULTY_EASY: {
		"rows": 10,
		"cols": 10,
		"time_limit_sec": 90,
		"wall_count": 8,
		"fire_count": 3,
		"smoke_count": 4,
		"exit_count": 2,
		"fire_spread_interval_ms": 2600,
		"fire_spread_probability": 0.10,
		"allow_fire_overwrite_exits": False,
		"score_step_penalty": 1,
		"score_multiplier": 1.0,
	},
	DIFFICULTY_MEDIUM: {
		"rows": 15,
		"cols": 15,
		"time_limit_sec": 60,
		"wall_count": 22,
		"fire_count": 7,
		"smoke_count": 10,
		"exit_count": 3,
		"fire_spread_interval_ms": 1700,
		"fire_spread_probability": 0.18,
		"allow_fire_overwrite_exits": False,
		"score_step_penalty": 2,
		"score_multiplier": 1.5,
	},
	DIFFICULTY_HARD: {
		"rows": 20,
		"cols": 20,
		"time_limit_sec": 45,
		"wall_count": 48,
		"fire_count": 14,
		"smoke_count": 18,
		"exit_count": 4,
		"fire_spread_interval_ms": 950,
		"fire_spread_probability": 0.28,
		"allow_fire_overwrite_exits": False,
		"score_step_penalty": 3,
		"score_multiplier": 2.0,
	},
}

# Colors
BACKGROUND_COLOR = (245, 247, 250)
GRID_LINE_COLOR = (220, 225, 232)
EMPTY_CELL_COLOR = (255, 255, 255)
WALL_COLOR = (54, 62, 73)
FIRE_COLOR = (220, 53, 69)
FIRE_COLOR_ALT = (255, 140, 0)      # orange for fire animation
SMOKE_COLOR = (158, 163, 172)
PLAYER_COLOR = (30, 102, 245)
EXIT_COLOR = (46, 204, 113)
PATH_COLOR = (255, 193, 7)
TEXT_COLOR = (33, 37, 41)
NEXT_MOVE_COLOR = (170, 255, 195)  # light green for next AI move
VISITED_COLOR = (255, 234, 167)    # lighter yellow for visited cells

# Backward-compatible color aliases used by the current game files
COLOR_EMPTY = EMPTY_CELL_COLOR
COLOR_GRID = GRID_LINE_COLOR
COLOR_WALL = WALL_COLOR
COLOR_FIRE = FIRE_COLOR
COLOR_SMOKE = SMOKE_COLOR
COLOR_PLAYER = PLAYER_COLOR
COLOR_EXIT = EXIT_COLOR
COLOR_PATH = PATH_COLOR
COLOR_TEXT = TEXT_COLOR

# Cell symbols
EMPTY = "."
WALL = "#"
FIRE = "F"
SMOKE = "S"
PLAYER = "P"
EXIT = "E"
PATH = "*"

# Backward-compatible cell aliases used by the current game files
CELL_EMPTY = EMPTY
CELL_WALL = WALL
CELL_FIRE = FIRE
CELL_SMOKE = SMOKE
CELL_PLAYER = PLAYER
CELL_EXIT = EXIT
CELL_PATH = PATH

# Movement costs
EMPTY_COST = 1
SMOKE_COST = 4
EXIT_COST = 1

# Backward-compatible movement cost aliases used by the current game files
COST_EMPTY = EMPTY_COST
COST_SMOKE = SMOKE_COST
COST_EXIT = EXIT_COST
COST_WALL = float("inf")
COST_FIRE = float("inf")

# Challenge Mode: Behavior when no safe path exists
# If True, the game ends immediately when no path is available.
# If False, the player can continue moving manually to attempt escape.
CHALLENGE_END_GAME_ON_NO_PATH = True

# Messages
TITLE = "AI-Based Fire Escape Game - Using A* Search Algorithm"
MSG_WELCOME = "Move with W/A/S/D, Press H to show/hide AI path"
MSG_WIN = "You escaped! Press Q to quit."
MSG_LOSE_FIRE = "Game Over! You stepped into fire. Press Q to quit."
MSG_LOSE_NO_PATH = "Game Over! No valid path exists. Press Q to quit."
