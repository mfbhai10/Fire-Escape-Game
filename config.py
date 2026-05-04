"""
Configuration for the Fire Escape AI Game.
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

# These values are placeholders for Version 3 systems.
# They are centralized here so game logic can read one source of truth.
DIFFICULTY_SETTINGS = {
	DIFFICULTY_EASY: {
		"time_limit_sec": 180,
		"fire_spread_interval_ms": 2400,
		"score_step_penalty": 1,
	},
	DIFFICULTY_MEDIUM: {
		"time_limit_sec": 120,
		"fire_spread_interval_ms": 1700,
		"score_step_penalty": 2,
	},
	DIFFICULTY_HARD: {
		"time_limit_sec": 90,
		"fire_spread_interval_ms": 1200,
		"score_step_penalty": 3,
	},
}

# Colors
BACKGROUND_COLOR = (245, 247, 250)
GRID_LINE_COLOR = (220, 225, 232)
EMPTY_CELL_COLOR = (255, 255, 255)
WALL_COLOR = (54, 62, 73)
FIRE_COLOR = (220, 53, 69)
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

# Messages
TITLE = "AI-Based Fire Escape Game - Using A* Search Algorithm"
MSG_WELCOME = "Move with W/A/S/D, Press H to show/hide AI path"
MSG_WIN = "You escaped! Press Q to quit."
MSG_LOSE_FIRE = "Game Over! You stepped into fire. Press Q to quit."
MSG_LOSE_NO_PATH = "Game Over! No valid path exists. Press Q to quit."
