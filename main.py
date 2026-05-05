"""
Main game loop for the Fire Escape AI Game.

This module handles:
- Game state and mode management (Manual, AI Auto, Challenge)
- Player input and event handling (WASD movement, mode switching)
- Game loop and 60 FPS frame rate control
- UI rendering (footer, menu, win/lose screens)
- Score calculation and challenge mode timing
- AI pathfinding requests and movement execution

The game runs at 60 FPS, using pygame.time.get_ticks() for all timing
to avoid blocking calls. The main game loop calls three methods each frame:
1. handle_events() - Check for keyboard/window input
2. _update_active_mode() - Update game state (timer, AI, fire spreading)
3. draw() - Render the current game state to the screen
"""

import sys

import pygame

from config import (
    FPS,
    CELL_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    EMPTY_COST,
    SMOKE_COST,
    EXIT_COST,
    SMOKE,
    EXIT,
    EMPTY,
    FIRE,
    WALL,
    AI_MOVE_DELAY_MS,
    DIFFICULTY_EASY,
    DIFFICULTY_MEDIUM,
    DIFFICULTY_HARD,
    MODE_MANUAL,
    MODE_AI_AUTO,
    MODE_CHALLENGE,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_SETTINGS,
    CHALLENGE_END_GAME_ON_NO_PATH,
)
from game_board import GameBoard
from player import Player
from astar import astar_search


FOOTER_HEIGHT = 132
WINDOW_HEIGHT = SCREEN_HEIGHT + FOOTER_HEIGHT


BLOCK_FONT = {
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    "C": [" ### ", "#   #", "#    ", "#   #", " ### "],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    "G": [" ### ", "#    ", "#  ##", "#   #", " ### "],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["#####", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#  ##", " ####"],
    "R": ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "X": ["#   #", " # # ", "  #  ", " # # ", "#   #"],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "   # ", "  #  ", " #   ", "#####"],
    "0": [" ### ", "#  ##", "# # #", "##  #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "   # ", "  #  ", "#####"],
    "3": ["#### ", "    #", " ### ", "    #", "#### "],
    "4": ["#   #", "#   #", "#####", "    #", "    #"],
    "5": ["#####", "#    ", "#### ", "    #", "#### "],
    "6": [" ### ", "#    ", "#### ", "#   #", " ### "],
    "7": ["#####", "   # ", "  #  ", " #   ", "#    "],
    "8": [" ### ", "#   #", " ### ", "#   #", " ### "],
    "9": [" ### ", "#   #", " ####", "    #", " ### "],
    ":": ["     ", "  #  ", "     ", "  #  ", "     "],
    "!": ["  #  ", "  #  ", "  #  ", "     ", "  #  "],
    "|": ["  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    ".": ["     ", "     ", "     ", "     ", "  #  "],
    "-": ["     ", "     ", "#####", "     ", "     "],
    "/": ["    #", "   # ", "  #  ", " #   ", "#    "],
    " ": ["     ", "     ", "     ", "     ", "     "],
}


class FireEscapeGame:
    """Manage the game state, drawing, and user input."""

    def __init__(self):
        """Set up Pygame and create the initial game state."""
        pygame.init()
        self.selected_difficulty = DEFAULT_DIFFICULTY
        self.screen = pygame.display.set_mode(self._get_window_size(self.selected_difficulty))
        pygame.display.set_caption("AI-Based Fire Escape Game Using A* Search")

        self.clock = pygame.time.Clock()

        # Create a font for the status UI area
        self.status_font = pygame.font.Font(None, 16)
        self.menu_title_font = pygame.font.Font(None, 48)
        self.menu_body_font = pygame.font.Font(None, 30)

        # Start menu state
        self.show_menu = True
        self.screen_state = "menu"  # "menu", "playing", "win", or "game_over"
        self.selected_mode = 1  # 1=Manual, 2=AI Auto, 3=Challenge
        self.active_mode = MODE_MANUAL
        # External checks may expect a `game_mode` attribute name; keep alias in sync.
        self.game_mode = self.active_mode

        self.running = True
        self.ai_move_delay = AI_MOVE_DELAY_MS

        # Runtime values are reset together so restart stays reliable.
        self._reset_runtime_state()

        self._setup_game()

    def _get_selected_mode_name(self):
        """Return the label for the currently selected menu mode."""
        if self.selected_mode == 2:
            return "AI Auto Mode"
        if self.selected_mode == 3:
            return "Challenge Mode"
        return "Manual Mode"

    def _start_selected_game(self):
        """Start a fresh game using the menu selections."""
        self._setup_game()
        self.show_menu = False
        self.screen_state = "playing"
        self._apply_selected_mode()

    def go_to_menu(self):
        """Return to the main menu from any game screen.
        
        This method stops gameplay, clears temporary state, and returns to the
        main menu without closing the window or restarting the game. Difficulty
        and mode selections are preserved.
        """
        # Stop gameplay immediately
        self.show_menu = True
        self.screen_state = "menu"
        self.ai_mode = False
        self.challenge_active = False
        self.current_path = []
        
        # Clear end-game state
        self.game_won = False
        self.game_over = False
        self.lose_reason = None
        self.status_message = ""
        self.temp_message = None
        
        # Stop timers and game updates
        self.game_start_ticks = 0
        self.last_fire_spread_time = 0

    def _get_difficulty_settings(self):
        """Return the selected difficulty settings with a safe fallback."""
        return DIFFICULTY_SETTINGS.get(self.selected_difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])

    def _get_time_limit_seconds(self):
        """Return the time limit for the selected difficulty."""
        return self._get_difficulty_settings()["time_limit_sec"]

    def _get_score_multiplier(self):
        """Return the difficulty multiplier used in the score formula."""
        difficulty = self.selected_difficulty
        if difficulty == DIFFICULTY_EASY:
            return 1.0
        if difficulty == DIFFICULTY_HARD:
            return 2.0
        return 1.5

    def _calculate_score(self):
        """Calculate the current score based on Challenge Mode state. [VERSION 3]

        Score = (Remaining Time * 10 - Moves * Step Penalty - Smoke Crossed * 5) * Difficulty Multiplier
        
        The difficulty multiplier is applied after the base score is computed:
        - Easy: 1.0x multiplier
        - Medium: 1.5x multiplier  
        - Hard: 2.0x multiplier
        
        The final score never goes below zero and is only calculated in Challenge Mode.
        Returns 0 if not in Challenge Mode or if time is negative.
        """
        if not self.challenge_active or self.remaining_time_sec < 0:
            return 0
        
        # Get penalty from difficulty settings (defaults to 2 if not found)
        settings = self._get_difficulty_settings()
        step_penalty = settings.get("score_step_penalty", 2)
        multiplier = settings.get("score_multiplier", 1.0)
        
        # Calculate raw score from time, moves, and smoke
        raw_score = (self.remaining_time_sec * 10) - (self.moves_count * step_penalty) - (self.smoke_crossed_count * 5)
        
        # Apply difficulty multiplier and clamp to minimum of 0
        final_score = int(raw_score * multiplier)
        return max(0, final_score)

    def _update_live_score(self):
        """Update the visible score while Challenge Mode is running."""
        if not self.challenge_active:
            self.live_score = self.final_score
            return

        self.live_score = self._calculate_score()

    def _finalize_score(self, escaped_successfully):
        """Lock in the final score when the game ends."""
        if not self.challenge_active:
            self.final_score = 0
            self.live_score = 0
            return

        if escaped_successfully:
            # Calculate and lock score on successful escape
            self.final_score = self._calculate_score()
        else:
            # Losing sets score to 0 (no points for failure)
            self.final_score = 0

        self.live_score = self.final_score

    def _start_challenge_timer(self):
        """Start a fresh countdown for Challenge Mode.

        The timer uses pygame.time.get_ticks() so it stays simple and does not rely
        on sleep-based timing.
        """
        self.game_start_ticks = pygame.time.get_ticks()
        self.last_fire_spread_time = self.game_start_ticks
        self.challenge_start_ticks = self.game_start_ticks
        self.time_limit_sec = self._get_time_limit_seconds()
        self.remaining_time_sec = self.time_limit_sec
        self.challenge_time_limit_sec = self.time_limit_sec
        self.challenge_remaining_sec = self.remaining_time_sec
        self.lose_reason = None

    def _update_challenge_timer(self):
        """Update the countdown only while Challenge Mode is active. [VERSION 3]
        
        Timer uses pygame.time.get_ticks() for frame-independent timing and stops
        updating when game_over or game_won becomes True to lock the final time.
        """
        if not self.challenge_active or self.game_over or self.game_won:
            return

        elapsed_ms = pygame.time.get_ticks() - self.game_start_ticks
        elapsed_sec = max(0, elapsed_ms // 1000)
        self.remaining_time_sec = max(0, self.time_limit_sec - elapsed_sec)
        self.challenge_remaining_sec = self.remaining_time_sec
        self._update_live_score()

        if self.remaining_time_sec <= 0:
            # Use centralized game-over handling so all teardown is consistent
            self.set_game_over("Time Up! Game Over")

    def _get_window_size(self, difficulty):
        """Calculate the display size for the selected difficulty."""
        settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])
        board_width = settings["cols"] * CELL_SIZE
        board_height = settings["rows"] * CELL_SIZE
        return (board_width, board_height + FOOTER_HEIGHT)

    def _resize_window_for_board(self):
        """Resize the window to match the current board dimensions."""
        self.screen = pygame.display.set_mode(self._get_window_size(self.selected_difficulty))

    def _reset_runtime_state(self):
        """Reset all gameplay variables that should return to defaults on restart."""
        self.game_over = False
        self.game_won = False
        self.show_path = True
        self.status_message = ""
        self.moves_count = 0
        self.game_start_ticks = 0
        self.last_fire_spread_time = 0

        # AI Auto Mode runtime values
        self.ai_mode = False
        self.last_ai_move_time = 0
        self.current_path = []
        self.ai_path = []
        self.ai_path_cost = 0
        self.ai_selected_exit = None
        self.ai_visited = set()

        # Challenge Mode runtime values (placeholders for Version 3)
        self.challenge_active = False
        self.challenge_score = 0
        self.smoke_crossed_count = 0
        self.live_score = 0
        self.final_score = 0
        difficulty_settings = self._get_difficulty_settings()
        self.challenge_time_limit_sec = difficulty_settings["time_limit_sec"]
        self.challenge_remaining_sec = self.challenge_time_limit_sec
        self.challenge_start_ticks = 0
        self.environment_changed = False
        self.time_limit_sec = difficulty_settings["time_limit_sec"]
        self.remaining_time_sec = self.time_limit_sec
        self.fire_spread_interval_ms = difficulty_settings["fire_spread_interval_ms"]
        self.fire_spread_probability = difficulty_settings["fire_spread_probability"]

        # Temporary on-screen messages
        self.temp_message = None
        self.temp_message_until = 0
        # Loss reason tracking (cleared on reset)
        self.lose_reason = None

    def _set_mode_manual(self):
        """Activate Manual Mode state."""
        self.active_mode = MODE_MANUAL
        self.ai_mode = False
        self.challenge_active = False
        self.current_path = []
        self.game_mode = self.active_mode

    def _set_mode_from_key(self, mode_key):
        """Switch to the selected mode while keeping the current board state.

        Challenge Mode resets its timer and mode-specific runtime values when it is
        activated so it behaves like a fresh challenge.
        """
        if mode_key == MODE_CHALLENGE:
            self._set_mode_challenge()
        elif mode_key == MODE_AI_AUTO:
            self._set_mode_ai_auto()
        else:
            self._set_mode_manual()

    def get_mode_display_name(self):
        """Return a user-friendly mode name for the HUD."""
        if self.active_mode == MODE_CHALLENGE:
            return "Challenge Mode"
        if self.active_mode == MODE_AI_AUTO:
            return "AI Auto Mode"
        return "Manual Mode"

    def _set_mode_ai_auto(self):
        """Activate AI Auto Mode state and prepare the first movement path."""
        self.active_mode = MODE_AI_AUTO
        self.ai_mode = True
        self.challenge_active = False
        self.current_path = list(self.ai_path)
        self.game_mode = self.active_mode
        if self.current_path and self.current_path[0] == (self.player.row, self.player.col):
            self.current_path.pop(0)
        self.last_ai_move_time = pygame.time.get_ticks()

    def _set_mode_challenge(self):
        """Activate Challenge Mode state without changing current core gameplay rules."""
        self.active_mode = MODE_CHALLENGE
        self.ai_mode = False
        self.challenge_active = True
        self.game_mode = self.active_mode
        self._start_challenge_timer()
        self.smoke_crossed_count = 0
        self.live_score = 0
        self.final_score = 0
        self._update_live_score()

    def _apply_selected_mode(self):
        """Apply the mode selected on the start menu."""
        if self.selected_mode == 2:
            self._set_mode_ai_auto()
        elif self.selected_mode == 3:
            self._set_mode_challenge()
        else:
            self._set_mode_manual()

    def _refresh_ai_path_from_player(self):
        """Recalculate path metadata from the player's current position. [VERSION 1 CORE]
        
        Called after every player move to update the AI's pathfinding. Uses A* search
        to find the safest route from the player to the nearest exit. This method
        runs in both AI Auto Mode and Challenge Mode to keep the path current.
        """
        self.exits = self.board.find_exits()
        current_position = (self.player.row, self.player.col)
        path, cost, sel = astar_search(self.board, current_position, self.exits)
        self.ai_path = path or []
        self.ai_path_cost = cost or 0
        self.ai_selected_exit = sel
        self.environment_changed = False
        return bool(path)

    def _is_current_path_valid(self):
        """Check if the current path is still safe to traverse.
        
        Returns False if any cell in the path is now FIRE or WALL, which means
        the path has been blocked and needs recalculation. Returns True if the
        path is still safe or if the path is empty.
        
        This method is called continuously in Challenge Mode to detect when
        fire spread or other board changes invalidate the cached path.
        """
        if not self.ai_path:
            # Empty path is trivially valid
            return True
        
        # Check each cell in the current path
        for row, col in self.ai_path:
            if not self.board.is_inside_grid(row, col):
                # Cell is out of bounds - path is invalid
                return False
            
            cell = self.board.get_cell(row, col)
            
            # Cells blocked by FIRE or WALL make the path invalid
            if cell == FIRE or cell == WALL:
                return False
        
        return True

    def _handle_path_invalidated(self):
        """Handle the case when the current path becomes blocked during Challenge Mode.
        
        Attempts to recalculate the path. If no safe path exists and
        CHALLENGE_END_GAME_ON_NO_PATH is True, ends the game with a message.
        If False, allows the player to continue attempting manual movement.
        """
        # Try to find a new path
        path_found = self._refresh_ai_path_from_player()
        
        if not path_found:
            # No path exists - apply the configured behavior
            if CHALLENGE_END_GAME_ON_NO_PATH:
                # End the game immediately using centralized handler
                self.set_game_over("No safe path available! Game Over.")
            else:
                # Allow player to continue manually
                self.ai_path = []
                self.ai_path_cost = 0
                self.ai_selected_exit = None
                self.status_message = "No safe path available. Try manual movement."

    def set_game_over(self, reason="Game Over"):
        """Set the game over state consistently across modes.

        Stops timers, AI movement, finalizes score, and stores the reason.
        """
        if self.game_over:
            return
        self.game_over = True
        self.screen_state = "game_over"
        self.lose_reason = reason
        self.status_message = reason
        # Stop challenge timer and AI movement
        self.challenge_active = False
        self.ai_mode = False
        self.current_path = []
        # Finalize scoring for challenge mode
        try:
            self._finalize_score(False)
        except Exception:
            pass

    def clear_lose_reason(self):
        self.lose_reason = None

    def check_win_condition(self):
        """Check if the player reached an exit and mark win state."""
        current_position = (self.player.row, self.player.col)
        if current_position in self.exits:
            if not self.game_won:
                self.game_won = True
                self.screen_state = "win"
                self.status_message = "You Escaped Successfully!"
                self.ai_mode = False
                self.current_path = []
                self._finalize_score(True)
            return True
        return False

    def check_lose_conditions(self):
        """Evaluate lose conditions and apply game-over when appropriate.

        Returns True if game over was triggered.
        """
        # 2. Fire reaches the player (fire spread onto player)
        if self.board.get_cell(self.player.row, self.player.col) == FIRE:
            self.set_game_over("Game Over! Fire reached you.")
            return True

        # 4/5. No safe path to any exit or all exits blocked/unreachable
        path_exists = self._refresh_ai_path_from_player()
        if not path_exists:
            if self.active_mode == MODE_CHALLENGE:
                if CHALLENGE_END_GAME_ON_NO_PATH:
                    self.set_game_over("No safe path found!")
                    return True
                else:
                    self.status_message = "No safe path available. Try manual movement."
            elif self.active_mode == MODE_AI_AUTO:
                # Stop AI and notify, but do not end the game unless in fire
                self.ai_mode = False
                self.current_path = []
                self.status_message = "AI Auto Mode stopped: No safe path found."
            else:
                # Manual mode: warn but do not end game
                self.status_message = "No safe path available. Try manual movement."

        return False

    def _setup_game(self):
        """Create a fresh board, player, and initial AI path."""
        self.board = GameBoard(self.selected_difficulty)
        self._resize_window_for_board()
        self.player_start = self.board.find_player()
        self.player = Player(self.board.player_start, self.board)
        self.exits = self.board.find_exits()

        self._reset_runtime_state()
        self.moves_count = self.player.moves

        # This is the first AI path and it is recalculated after each successful move.
        path_found = self._refresh_ai_path_from_player()

        if not path_found and (self.player.row, self.player.col) not in self.exits:
            self.set_game_over("No safe path found!")

    def reset_game(self):
        """Reset the current game while preserving difficulty and mode selection.
        
        This is called when the player presses R during gameplay to start a fresh
        round with a new random board without returning to the menu. All game state
        is reset, including:
        - Player position
        - Random map (newly generated)
        - Timer and score
        - Move count and smoke count
        - AI path, selected exit, and path cost
        - Win/loss state and status messages
        - Fire and smoke cells (new map has fresh fire/smoke)
        
        The selected difficulty and game mode are preserved.
        """
        # Save the current mode selection so we can restore it after setup
        current_mode_selection = self.selected_mode
        current_active_mode = self.active_mode
        
        # Generate fresh board, reset all runtime state
        self._setup_game()
        
        # Ensure we're back in playing state
        self.show_menu = False
        self.screen_state = "playing"
        
        # Restore the mode selection and reactivate it
        self.selected_mode = current_mode_selection
        
        # Restore the active mode, but handle AI Auto Mode specially:
        # If AI Auto Mode was active, restart it; if Manual Mode was active, restore it
        if current_active_mode == MODE_AI_AUTO:
            self._set_mode_ai_auto()
        elif current_active_mode == MODE_CHALLENGE:
            self._set_mode_challenge()
        else:
            # Default to Manual Mode
            self._set_mode_manual()

    def restart_game(self):
        """Restart the game from the initial state and return to menu."""
        self._setup_game()
        self.show_menu = True
        # Use the mode setter to ensure aliases and runtime flags stay in sync.
        self._set_mode_manual()

    def handle_events(self):
        """Handle keyboard and window events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            # Menu handling
            if self.show_menu:
                if event.key == pygame.K_1:
                    self.selected_mode = 1
                elif event.key == pygame.K_2:
                    self.selected_mode = 2
                elif event.key == pygame.K_3:
                    self.selected_mode = 3
                elif event.key == pygame.K_e:
                    self.selected_difficulty = DIFFICULTY_EASY
                elif event.key == pygame.K_m:
                    self.selected_difficulty = DIFFICULTY_MEDIUM
                elif event.key == pygame.K_h:
                    self.selected_difficulty = DIFFICULTY_HARD
                elif event.key == pygame.K_RETURN:
                    self._start_selected_game()
                elif event.key == pygame.K_r:
                    self._start_selected_game()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                continue

            # Gameplay key handling
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_q:
                # Q returns to main menu from any gameplay screen
                self.go_to_menu()
                continue
            elif event.key == pygame.K_h:
                self.show_path = not self.show_path
            elif event.key == pygame.K_c:
                # Toggle Challenge Mode separately from AI Auto Mode.
                if self.active_mode == MODE_CHALLENGE:
                    self._set_mode_manual()
                    self.challenge_active = False
                    self.current_path = []
                else:
                    self._set_mode_challenge()
            elif event.key == pygame.K_r:
                # Reset the current game with a new random board, keeping mode/difficulty.
                # If we're on an end screen, restart; otherwise reset board.
                if self.game_over or self.game_won:
                    # Restart a fresh round, preserving mode and difficulty
                    self.reset_game()
                else:
                    self.reset_game()
                continue
            elif event.key == pygame.K_SPACE:
                # Toggle AI Auto Mode
                if not self.game_over and not self.game_won and self.active_mode != MODE_CHALLENGE:
                    if not self.ai_mode:
                        self._set_mode_ai_auto()
                    else:
                        self._set_mode_manual()
            # When on final screens only allow R (restart), Q (menu), and ESC (quit)
            elif self.game_over or self.game_won:
                if event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_q:
                    self.go_to_menu()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                # ignore all other keys while showing final screen
                continue

            elif not self.game_over and not self.game_won and not self.ai_mode:
                # Manual movement is only allowed when AI Auto Mode is off
                if event.key == pygame.K_w:
                    self.move_player("UP")
                elif event.key == pygame.K_s:
                    self.move_player("DOWN")
                elif event.key == pygame.K_a:
                    self.move_player("LEFT")
                elif event.key == pygame.K_d:
                    self.move_player("RIGHT")

    def move_player(self, direction):
        """Move the player and update the game state. [VERSION 1 CORE]
        
        This is the main method that processes every player movement. It:
        - Validates the move is allowed (not wall/fire, within grid)
        - Tracks smoke crossings and moves count
        - Detects win condition (reached exit)
        - Spreads fire in Challenge Mode
        - Recalculates A* path for next frame
        - Detects loss condition (no safe path)
        
        Called from handle_events() for manual movement or from _execute_ai_step() 
        for AI movement.
        """
        if self.game_over or self.game_won:
            return

        next_row, next_col = self.player.row, self.player.col
        if direction == "UP":
            next_row -= 1
        elif direction == "DOWN":
            next_row += 1
        elif direction == "LEFT":
            next_col -= 1
        elif direction == "RIGHT":
            next_col += 1

        target_cell = self.board.get_cell(next_row, next_col)

        # Allow moving into fire only in Manual Mode (player choice).
        allow_fire_entry = self.active_mode == MODE_MANUAL
        moved = self.player.move(direction, self.board, allow_fire=allow_fire_entry)

        if not moved:
            return

        self.moves_count = self.player.moves
        self.environment_changed = True

        # Track smoke crossings for scoring only when the player actually steps into smoke.
        if self.active_mode == MODE_CHALLENGE and target_cell == SMOKE:
            self.smoke_crossed_count += 1
            self._update_live_score()

        # If the player moved into a cell that is now on fire, treat as immediate loss.
        if target_cell == FIRE and moved:
            # Manual moves into fire cause immediate game over.
            if self.active_mode == MODE_MANUAL:
                self.set_game_over("Game Over! You moved into fire.")
                return
            # AI should never move into fire because pathfinding avoids it.

        # Check for win after the move
        if self.check_win_condition():
            return

        if self.active_mode == MODE_CHALLENGE:
            self._spread_fire_after_player_move()
            if self.game_over or self.game_won:
                return

        # Recalculate the safest route after every move so the AI path stays current.
        path_found = self._refresh_ai_path_from_player()

        if not path_found:
            # Mode-specific behavior when no path exists
            if self.active_mode == MODE_CHALLENGE:
                if CHALLENGE_END_GAME_ON_NO_PATH:
                    self.set_game_over("No safe path found!")
                else:
                    self.status_message = "No safe path available. Try manual movement."
            elif self.active_mode == MODE_AI_AUTO:
                # Stop AI movement but do not end the game
                self.ai_mode = False
                self.current_path = []
                self.status_message = "AI Auto Mode stopped: No safe path found."
            else:
                # Manual Mode: warn but let the player continue
                self.status_message = "No safe path available. Try manual movement."

    def _spread_fire_after_player_move(self):
        """Spread fire once after the player moves in Challenge Mode. [VERSION 3]

        This uses a snapshot of the current fire cells so newly created fire cannot
        spread again during the same turn. Empty cells may become smoke first, and
        smoke can ignite later if it is near fire.
        
        This method is only called in Challenge Mode after each valid player move.
        """
        if self.game_over or self.game_won:
            return

        settings = self._get_difficulty_settings()
        changed_cells = self.board.spread_fire(
            settings["fire_spread_probability"],
            allow_fire_overwrite_exits=settings.get("allow_fire_overwrite_exits", False),
        )

        if not changed_cells:
            return

        self.environment_changed = True

        # Fire reaching the player ends the game immediately.
        if self.board.get_cell(self.player.row, self.player.col) == FIRE:
            self.set_game_over("Game Over! Fire reached you.")
            return

        # Re-run pathfinding so the AI hint and selected exit stay accurate after fire changes.
        path_found = self._refresh_ai_path_from_player()
        if not path_found:
            # Path invalidated by fire spread - apply configured behavior
            if CHALLENGE_END_GAME_ON_NO_PATH:
                self.set_game_over("No safe path found!")
            else:
                # Allow player to continue attempting escape
                self.status_message = "No safe path available. Try manual movement."

    def _execute_ai_step(self):
        """Execute one step of AI Auto Mode with dynamic path recalculation and replanning."""
        # If we don't have a current path, try recalculating
        if not self.current_path:
            if not self.recalculate_ai_path():
                self.ai_mode = False
                self.status_message = "AI Auto Mode stopped: No safe path found."
                return

        # Skip current position if present
        current_position = (self.player.row, self.player.col)
        if self.current_path and self.current_path[0] == current_position:
            self.current_path.pop(0)

        # If nothing to move to, replan
        if not self.current_path:
            if not self.recalculate_ai_path():
                self.ai_mode = False
                self.status_message = "AI Auto Mode stopped: No safe path found."
                return

        next_position = self.current_path[0]
        next_row, next_col = next_position

        # If next cell became unsafe (fire or wall), immediately replan
        if not self.is_cell_safe_for_ai(next_row, next_col):
            if not self.recalculate_ai_path():
                self.ai_mode = False
                self.status_message = "AI trapped: no safe path available"
                return

            # after replanning, ensure we have a next step
            if not self.current_path:
                self.ai_mode = False
                self.status_message = "AI trapped: no safe path available"
                return

            next_position = self.current_path[0]
            next_row, next_col = next_position

        current_row, current_col = self.player.row, self.player.col

        # Determine the direction to move
        direction = None
        if next_row < current_row:
            direction = "UP"
        elif next_row > current_row:
            direction = "DOWN"
        elif next_col < current_col:
            direction = "LEFT"
        elif next_col > current_col:
            direction = "RIGHT"

        if direction:
            # Use the higher-level move_player() to handle win/lose and bookkeeping
            # This prevents duplicating game-over and exit logic here.
            self.move_player(direction)

            # If move_player succeeded it updates self.moves_count and player position.
            # Check if the game ended as a result of the move.
            if self.game_won:
                # Stop AI when we reached the exit
                self.ai_mode = False
                self.current_path = []
                return

            if self.game_over:
                # Stop AI on game over
                self.ai_mode = False
                self.current_path = []
                return

            # Mark the previous position as visited for visualization
            self.ai_visited.add(current_position)

            # After move_player() the AI's global path was recalculated inside move_player().
            # Use that freshly computed path as the current working path for the AI.
            self.current_path = list(self.ai_path)
            # Remove starting cell if present so the next step points forward
            if self.current_path and self.current_path[0] == (self.player.row, self.player.col):
                self.current_path.pop(0)

    def is_cell_safe_for_ai(self, row, col):
        """Return True if the given cell is safe for the AI to step into.

        Unsafe cells are `FIRE` or `WALL`. Smoke is allowed but has higher cost.
        """
        if not self.board.is_inside_grid(row, col):
            return False
        cell = self.board.get_cell(row, col)
        return cell != FIRE and cell != WALL

    def recalculate_ai_path(self):
        """Recalculate the AI path from the player's current position to any exit.

        Returns True if a path was found, False otherwise. Updates `current_path`,
        `ai_path`, `ai_path_cost`, and `ai_selected_exit`.
        """
        # Show a brief "recalculating" message
        now = pygame.time.get_ticks()
        self.temp_message = "Recalculating path..."
        self.temp_message_until = now + 700

        if not self._refresh_ai_path_from_player():
            # No path found
            self.current_path = []
            self.ai_path = []
            self.ai_path_cost = 0
            self.ai_selected_exit = None
            # Show no-path message briefly
            now = pygame.time.get_ticks()
            self.temp_message = "No safe path found"
            self.temp_message_until = now + 1200
            return False

        # Store the recalculated path and metadata
        current_position = (self.player.row, self.player.col)
        self.current_path = list(self.ai_path)
        # Remove starting cell if present (we don't want to step to current position)
        if self.current_path and self.current_path[0] == current_position:
            self.current_path.pop(0)
        # Brief confirmation message (fades quickly)
        now = pygame.time.get_ticks()
        self.temp_message = "Path updated"
        self.temp_message_until = now + 600
        return True

    def _get_path_status_display(self):
        """Generate a display-friendly path status string for the HUD.
        
        Returns a tuple of (status_text, color) that indicates:
        - Whether a path was found
        - Whether the path is currently valid (all cells traversable)
        - Any relevant error messages
        """
        if not self.ai_path:
            return "Path: NOT FOUND", (220, 53, 69)  # Red
        
        if not self._is_current_path_valid():
            return "Path: BLOCKED (recalculating)", (255, 193, 7)  # Yellow/orange
        
        return "Path: SAFE", (46, 204, 113)  # Green

    def _get_difficulty_settings(self):
        """Get the settings for the currently selected difficulty."""
        return DIFFICULTY_SETTINGS.get(self.selected_difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])

    def _update_challenge_runtime(self):
        """Update Challenge Mode runtime values and validate path safety."""
        self._update_challenge_timer()
        
        # In Challenge Mode, continuously validate that the cached path is still safe.
        # If fire or walls block the path, trigger recalculation with the configured behavior.
        if self.active_mode == MODE_CHALLENGE and not self.game_over and not self.game_won:
            if not self._is_current_path_valid():
                # Path has been blocked - recalculate and apply configured behavior
                self._handle_path_invalidated()

        # After timer/path updates, check general lose conditions
        if self.active_mode == MODE_CHALLENGE and not self.game_over and not self.game_won:
            self.check_lose_conditions()

    def _update_active_mode(self):
        """Run per-frame logic for the active mode."""
        # Skip updates if not actively playing
        if self.show_menu or self.screen_state != "playing":
            return

        self._update_challenge_runtime()

        if self.active_mode == MODE_AI_AUTO and self.ai_mode and not self.game_over and not self.game_won:
            current_time = pygame.time.get_ticks()
            # Move only if enough milliseconds have passed since the last move
            if current_time - self.last_ai_move_time >= self.ai_move_delay:
                self.last_ai_move_time = current_time
                self._execute_ai_step()

    def draw_block_text(self, text, x, y, color, scale=1, spacing=1):
        """Draw text using a tiny built-in block font."""
        cursor_x = x
        for character in text.upper():
            pattern = BLOCK_FONT.get(character, BLOCK_FONT[" "])
            for row_index, row in enumerate(pattern):
                for col_index, pixel in enumerate(row):
                    if pixel != " ":
                        rect = pygame.Rect(
                            cursor_x + col_index * scale,
                            y + row_index * scale,
                            scale,
                            scale,
                        )
                        pygame.draw.rect(self.screen, color, rect)
            cursor_x += (len(pattern[0]) * scale) + spacing

    def calculate_path_cost(self, path):
        """Calculate the total movement cost of a given path."""
        if not path:
            return 0
        
        total_cost = 0
        for row, col in path:
            cell = self.board.get_cell(row, col)
            if cell == EMPTY:
                total_cost += EMPTY_COST
            elif cell == SMOKE:
                total_cost += SMOKE_COST
            elif cell == EXIT:
                total_cost += EXIT_COST
            else:
                # Wall or Fire would have infinite cost, but shouldn't be in the path
                pass
        
        return total_cost

    def _render_ui_text(self, text, size=16, color=(33, 37, 41), bold=False):
        """Render text with fallback support for pygame.font."""
        try:
            font = pygame.font.Font(None, size)
            if bold:
                font.set_bold(True)
            return font.render(text, True, color)
        except Exception:
            # Fallback: use default font if custom fails
            return pygame.font.Font(None, 24).render(text, True, color)

    def draw_footer(self):
        """Draw an improved, organized UI panel at the bottom of the screen. [VERSION 2]"""
        footer_top = self.board.rows * CELL_SIZE
        footer_width = self.board.cols * CELL_SIZE

        # Background panel
        panel_rect = pygame.Rect(0, footer_top, footer_width, FOOTER_HEIGHT)
        pygame.draw.rect(self.screen, (242, 244, 248), panel_rect)
        pygame.draw.rect(self.screen, (180, 188, 200), panel_rect, 2)

        # Top accent line
        accent_rect = pygame.Rect(0, footer_top, footer_width, 4)
        pygame.draw.rect(self.screen, (74, 144, 226), accent_rect)

        # Gather game state information
        score_value = self.final_score if (self.game_over or self.game_won) else self.live_score
        path_found = len(self.ai_path) > 0
        remaining_steps = len(self.current_path)
        path_cost = int(self.ai_path_cost) if path_found and self.ai_path_cost else 0
        
        # Determine status message and color
        if self.game_won:
            status_msg = "✓ Escaped Successfully!"
            status_color = (46, 204, 113)
        elif self.game_over:
            status_msg = "✗ Game Over"
            status_color = (220, 53, 69)
        else:
            path_status, path_status_color = self._get_path_status_display()
            if "NOT FOUND" in path_status:
                status_msg = "No safe path available"
                status_color = (220, 53, 69)
            elif "BLOCKED" in path_status:
                status_msg = "Path blocked - recalculating..."
                status_color = (255, 193, 7)
            else:
                status_msg = "Safe path found"
                status_color = (46, 204, 113)

        # Check if there's a temporary message to display
        current_time = pygame.time.get_ticks()
        if self.temp_message and current_time < self.temp_message_until:
            status_msg = self.temp_message
            status_color = (255, 193, 7)  # Yellow for temporary messages

        # Layout: 4 rows of information
        y_pos = footer_top + 8
        line_height = 30

        # Row 1: Title and Mode
        title_text = self._render_ui_text("Fire Escape AI", size=18, bold=True)
        mode_text = self._render_ui_text(
            f"Mode: {self.get_mode_display_name()} | Difficulty: {self.selected_difficulty}",
            size=14,
        )
        self.screen.blit(title_text, (10, y_pos))
        self.screen.blit(mode_text, (220, y_pos))
        y_pos += line_height

        # Row 2: Game Stats
        moves_text = self._render_ui_text(f"Moves: {self.moves_count}", size=13)
        time_text = self._render_ui_text(f"Time: {self.remaining_time_sec}s", size=13)
        score_text = self._render_ui_text(f"Score: {score_value}", size=13)
        smoke_text = self._render_ui_text(f"Smoke Crossed: {self.smoke_crossed_count}", size=13)
        
        self.screen.blit(moves_text, (10, y_pos))
        self.screen.blit(time_text, (120, y_pos))
        self.screen.blit(score_text, (220, y_pos))
        self.screen.blit(smoke_text, (320, y_pos))
        y_pos += line_height

        # Row 3: Path Info
        if self.ai_selected_exit is not None:
            exit_row, exit_col = self.ai_selected_exit
            exit_text_str = f"Exit: ({exit_row}, {exit_col})"
        else:
            exit_text_str = "Exit: None"
        
        path_cost_text = self._render_ui_text(f"Path Cost: {path_cost}", size=13)
        steps_text = self._render_ui_text(f"Steps: {remaining_steps}", size=13)
        exit_info_text = self._render_ui_text(exit_text_str, size=13)
        
        self.screen.blit(path_cost_text, (10, y_pos))
        self.screen.blit(steps_text, (140, y_pos))
        self.screen.blit(exit_info_text, (240, y_pos))
        y_pos += line_height

        # Row 4: Status and Controls
        status_text = self._render_ui_text(status_msg, size=14, color=status_color, bold=True)
        self.screen.blit(status_text, (10, y_pos))
        
        # Controls legend
        controls_text = self._render_ui_text(
            "W/A/S/D: Move | H: Path | SPACE: AI | Q: Menu | R: Restart | ESC: Quit",
            size=12,
            color=(90, 96, 105),
        )
        self.screen.blit(controls_text, (10, y_pos + 22))

    def draw_menu(self):
        """Draw simple keyboard-based menu at startup."""
        self.screen.fill((30, 30, 35))
        title = self.menu_title_font.render("Fire Escape AI Game", True, (240, 240, 245))
        subtitle = self.menu_body_font.render("Simple Menu", True, (180, 180, 180))

        mode_label = self.menu_body_font.render(
            f"Selected mode: {self._get_selected_mode_name()}",
            True,
            (140, 220, 140),
        )
        difficulty_label = self.menu_body_font.render(
            f"Selected difficulty: {self.selected_difficulty}",
            True,
            (140, 220, 140),
        )
        mode_help = self.menu_body_font.render(
            "1 = Manual Mode   2 = AI Auto Mode   3 = Challenge Mode",
            True,
            (200, 200, 200),
        )
        difficulty_help = self.menu_body_font.render(
            "E = Easy   M = Medium   H = Hard",
            True,
            (200, 200, 200),
        )
        start_help = self.menu_body_font.render("Press ENTER or R to start", True, (240, 240, 245))
        quit_help = self.menu_body_font.render("Press ESC to quit", True, (180, 180, 180))

        self.screen.blit(title, (20, 20))
        self.screen.blit(subtitle, (20, 65))
        self.screen.blit(mode_label, (20, 120))
        self.screen.blit(difficulty_label, (20, 155))
        self.screen.blit(mode_help, (20, 210))
        self.screen.blit(difficulty_help, (20, 245))
        self.screen.blit(start_help, (20, 300))
        self.screen.blit(quit_help, (20, 335))
        pygame.display.flip()

    def draw_win_screen(self):
        """Draw the win/escaped screen with game statistics."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.board.cols * CELL_SIZE, self.board.rows * CELL_SIZE))
        overlay.set_alpha(200)
        overlay.fill((30, 100, 30))  # Green tint
        self.screen.blit(overlay, (0, 0))

        # Calculate center position
        screen_width = self.board.cols * CELL_SIZE
        center_x = screen_width // 2

        title_font = pygame.font.Font(None, 64)
        info_font = pygame.font.Font(None, 26)
        controls_font = pygame.font.Font(None, 22)

        # Render mode-specific win screens
        if self.active_mode == MODE_AI_AUTO:
            title_text = title_font.render("AI ESCAPED SUCCESSFULLY!", True, (180, 255, 180))
            title_rect = title_text.get_rect(center=(center_x, 60))
            self.screen.blit(title_text, title_rect)

            stats = [
                f"Mode: AI Auto Mode",
                f"Difficulty: {self.selected_difficulty}",
                f"Selected Exit: {self.ai_selected_exit}",
                f"Path Cost: {int(self.ai_path_cost) if self.ai_path_cost else 0}",
                f"AI Steps Taken: {self.moves_count}",
                f"Smoke Crossed: {self.smoke_crossed_count}",
                "A* successfully found and followed the safest path.",
            ]
        elif self.active_mode == MODE_CHALLENGE:
            title_text = title_font.render("YOU ESCAPED!", True, (180, 255, 180))
            title_rect = title_text.get_rect(center=(center_x, 60))
            self.screen.blit(title_text, title_rect)

            stats = [
                f"Mode: Challenge Mode",
                f"Difficulty: {self.selected_difficulty}",
                f"Final Score: {self.final_score}",
                f"Remaining Time: {self.remaining_time_sec}s",
                f"Moves: {self.moves_count}",
                f"Smoke Crossed: {self.smoke_crossed_count}",
                f"Selected Exit: {self.ai_selected_exit}",
                f"Final Path Cost: {int(self.ai_path_cost) if self.ai_path_cost else 0}",
                "You escaped before the fire blocked the building.",
            ]
        else:
            # Manual Mode
            title_text = title_font.render("YOU ESCAPED!", True, (180, 255, 180))
            title_rect = title_text.get_rect(center=(center_x, 60))
            self.screen.blit(title_text, title_rect)

            stats = [
                f"Mode: Manual Mode",
                f"Difficulty: {self.selected_difficulty}",
                f"Moves: {self.moves_count}",
                f"Smoke Crossed: {self.smoke_crossed_count}",
                f"Path Cost: {int(self.ai_path_cost) if self.ai_path_cost else 0}",
                "You reached the exit manually.",
            ]

        y_pos = 150
        for stat in stats:
            stat_text = info_font.render(stat, True, (245, 245, 245))
            stat_rect = stat_text.get_rect(center=(center_x, y_pos))
            self.screen.blit(stat_text, stat_rect)
            y_pos += 40

        control_text = controls_font.render("Press R to restart  |  Press Q for menu  |  Press ESC to quit", True, (220, 255, 220))
        control_rect = control_text.get_rect(center=(center_x, y_pos + 20))
        self.screen.blit(control_text, control_rect)

    def draw_game_over_screen(self):
        """Draw the game over screen with loss information."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.board.cols * CELL_SIZE, self.board.rows * CELL_SIZE))
        overlay.set_alpha(200)
        overlay.fill((100, 30, 30))  # Red tint
        self.screen.blit(overlay, (0, 0))

        screen_width = self.board.cols * CELL_SIZE
        center_x = screen_width // 2

        title_font = pygame.font.Font(None, 64)
        info_font = pygame.font.Font(None, 26)
        controls_font = pygame.font.Font(None, 22)

        reason = self.lose_reason or self.status_message or "Game Over"

        title_text = title_font.render("GAME OVER", True, (255, 150, 150))
        title_rect = title_text.get_rect(center=(center_x, 60))
        self.screen.blit(title_text, title_rect)

        reason_text = info_font.render(reason, True, (255, 210, 210))
        reason_rect = reason_text.get_rect(center=(center_x, 120))
        self.screen.blit(reason_text, reason_rect)

        # Mode-specific statistics
        if self.active_mode == MODE_AI_AUTO:
            stats = [
                f"Mode: AI Auto Mode",
                f"Difficulty: {self.selected_difficulty}",
                f"AI Steps Taken: {self.moves_count}",
                f"Last Path Cost: {int(self.ai_path_cost) if self.ai_path_cost else 0}",
            ]
        elif self.active_mode == MODE_CHALLENGE:
            stats = [
                f"Mode: Challenge Mode",
                f"Difficulty: {self.selected_difficulty}",
                f"Final Score: 0",
                f"Remaining Time: {self.remaining_time_sec}s",
                f"Moves: {self.moves_count}",
                f"Smoke Crossed: {self.smoke_crossed_count}",
                f"Last Selected Exit: {self.ai_selected_exit}",
                f"Last Path Cost: {int(self.ai_path_cost) if self.ai_path_cost else 0}",
            ]
        else:
            # Manual mode: show concise information and reason (manual stepping into fire typically)
            stats = [
                f"Mode: Manual Mode",
                f"Reason: {reason}",
                f"Difficulty: {self.selected_difficulty}",
                f"Moves: {self.moves_count}",
                f"Smoke Crossed: {self.smoke_crossed_count}",
            ]

        y_pos = 170
        for stat in stats:
            stat_text = info_font.render(stat, True, (255, 245, 245))
            stat_rect = stat_text.get_rect(center=(center_x, y_pos))
            self.screen.blit(stat_text, stat_rect)
            y_pos += 36

        control_text = controls_font.render("Press R to restart  |  Press Q for menu  |  Press ESC to quit", True, (255, 200, 200))
        control_rect = control_text.get_rect(center=(center_x, y_pos + 10))
        self.screen.blit(control_text, control_rect)

    def draw(self):
        """Draw the board, optional AI path, footer text, menu, or end screens."""
        if self.show_menu:
            self.draw_menu()
            return

        # Draw the game board first
        # In AI mode, show the remaining path; otherwise show the full AI path
        if self.game_won:
            # Player reached exit: do not show path overlays
            path_to_draw = None
            next_cell = None
            visited = None
        else:
            if self.ai_mode:
                path_to_draw = self.current_path if self.show_path else None
                next_cell = self.current_path[0] if (self.current_path and self.show_path) else None
            else:
                path_to_draw = self.ai_path if self.show_path else None
                # when not in AI mode the next cell is undefined
                next_cell = None
            visited = self.ai_visited if self.show_path else None

        self.board.draw(self.screen, path_to_draw, next_cell=next_cell, visited=visited)
        self.draw_footer()

        # Draw end screens on top of the board
        if self.game_won:
            self.draw_win_screen()
        elif self.game_over:
            self.draw_game_over_screen()

        pygame.display.flip()

    def run(self):
        """Run the main game loop."""
        while self.running:
            self.handle_events()

            self._update_active_mode()

            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """Program entry point."""
    game = FireEscapeGame()
    game.run()


if __name__ == "__main__":
    main()
