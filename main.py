"""
Main game loop for the Fire Escape AI Game.
"""

import sys

import pygame

from config import (
    FPS,
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
    MODE_MANUAL,
    MODE_AI_AUTO,
    MODE_CHALLENGE,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_SETTINGS,
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
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI-Based Fire Escape Game Using A* Search")

        self.clock = pygame.time.Clock()

        # Create a font for the status UI area
        self.status_font = pygame.font.Font(None, 16)

        # Start menu state
        self.show_menu = True
        self.selected_mode = 1  # 1=Manual, 2=AI Auto, 3=Challenge
        self.active_mode = MODE_MANUAL
        self.selected_difficulty = DEFAULT_DIFFICULTY

        self.running = True
        self.ai_move_delay = AI_MOVE_DELAY_MS

        # Runtime values are reset together so restart stays reliable.
        self._reset_runtime_state()

        self._setup_game()

    def _reset_runtime_state(self):
        """Reset all gameplay variables that should return to defaults on restart."""
        self.game_over = False
        self.game_won = False
        self.show_path = True
        self.status_message = ""
        self.moves_count = 0

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
        self.challenge_time_limit_sec = DIFFICULTY_SETTINGS[self.selected_difficulty]["time_limit_sec"]
        self.challenge_remaining_sec = self.challenge_time_limit_sec
        self.challenge_start_ticks = 0
        self.environment_changed = False

        # Temporary on-screen messages
        self.temp_message = None
        self.temp_message_until = 0

    def _set_mode_manual(self):
        """Activate Manual Mode state."""
        self.active_mode = MODE_MANUAL
        self.ai_mode = False
        self.challenge_active = False
        self.current_path = []

    def _set_mode_ai_auto(self):
        """Activate AI Auto Mode state and prepare the first movement path."""
        self.active_mode = MODE_AI_AUTO
        self.ai_mode = True
        self.challenge_active = False
        self.current_path = list(self.ai_path)
        if self.current_path and self.current_path[0] == (self.player.row, self.player.col):
            self.current_path.pop(0)
        self.last_ai_move_time = pygame.time.get_ticks()

    def _set_mode_challenge(self):
        """Activate Challenge Mode state without changing current core gameplay rules."""
        self.active_mode = MODE_CHALLENGE
        self.ai_mode = False
        self.challenge_active = True
        self.challenge_time_limit_sec = DIFFICULTY_SETTINGS[self.selected_difficulty]["time_limit_sec"]
        self.challenge_remaining_sec = self.challenge_time_limit_sec
        self.challenge_start_ticks = pygame.time.get_ticks()

    def _apply_selected_mode(self):
        """Apply the mode selected on the start menu."""
        if self.selected_mode == 2:
            self._set_mode_ai_auto()
        elif self.selected_mode == 3:
            self._set_mode_challenge()
        else:
            self._set_mode_manual()

    def _refresh_ai_path_from_player(self):
        """Recalculate path metadata from the player's current position."""
        current_position = (self.player.row, self.player.col)
        path, cost, sel = astar_search(self.board, current_position, self.exits)
        self.ai_path = path or []
        self.ai_path_cost = cost or 0
        self.ai_selected_exit = sel
        self.environment_changed = False
        return bool(path)

    def _setup_game(self):
        """Create a fresh board, player, and initial AI path."""
        self.board = GameBoard()
        self.player_start = self.board.find_player()
        self.player = Player(self.board.player_start, self.board)
        self.exits = self.board.find_exits()

        self._reset_runtime_state()
        self.moves_count = self.player.moves

        # This is the first AI path and it is recalculated after each successful move.
        path_found = self._refresh_ai_path_from_player()

        if not path_found and (self.player.row, self.player.col) not in self.exits:
            self.game_over = True
            self.status_message = "No safe path found!"

    def restart_game(self):
        """Restart the game from the initial state and return to menu."""
        self._setup_game()
        self.show_menu = True
        self.active_mode = MODE_MANUAL

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
                elif event.key == pygame.K_RETURN:
                    # Start game with selection
                    self.show_menu = False
                    self._apply_selected_mode()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                continue

            # Gameplay key handling
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_h:
                self.show_path = not self.show_path
            elif event.key == pygame.K_r:
                # Restart and return to the selection menu
                self.restart_game()
                continue
            elif event.key == pygame.K_SPACE:
                # Toggle AI Auto Mode
                if not self.game_over and not self.game_won and self.active_mode != MODE_CHALLENGE:
                    if not self.ai_mode:
                        self._set_mode_ai_auto()
                    else:
                        self._set_mode_manual()
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
        """Move the player and update the game state."""
        if self.game_over or self.game_won:
            return

        moved = self.player.move(direction, self.board)

        if not moved:
            return

        self.moves_count = self.player.moves
        self.environment_changed = True

        current_position = (self.player.row, self.player.col)

        if current_position in self.exits:
            self.game_won = True
            self.status_message = "You Escaped Successfully!"
            return

        # Recalculate the safest route after every move so the AI path stays current.
        path_found = self._refresh_ai_path_from_player()

        if not path_found:
            # If A* cannot find any route to an exit, the player has no safe way out.
            self.game_over = True
            self.status_message = "No safe path found!"

    def _execute_ai_step(self):
        """Execute one step of AI Auto Mode with dynamic path recalculation and replanning."""
        # If we don't have a current path, try recalculating
        if not self.current_path:
            if not self.recalculate_ai_path():
                self.ai_mode = False
                self.status_message = "AI trapped: no safe path available"
                return

        # Skip current position if present
        current_position = (self.player.row, self.player.col)
        if self.current_path and self.current_path[0] == current_position:
            self.current_path.pop(0)

        # If nothing to move to, replan
        if not self.current_path:
            if not self.recalculate_ai_path():
                self.ai_mode = False
                self.status_message = "AI trapped: no safe path available"
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

    def _update_challenge_runtime(self):
        """Update challenge-only runtime values.

        Version 3 will expand this with countdown loss, fire spread, and scoring rules.
        """
        if not self.challenge_active:
            return

        if self.game_over or self.game_won:
            return

        elapsed_ms = pygame.time.get_ticks() - self.challenge_start_ticks
        elapsed_sec = max(0, elapsed_ms // 1000)
        self.challenge_remaining_sec = max(0, self.challenge_time_limit_sec - elapsed_sec)

    def _update_active_mode(self):
        """Run per-frame logic for the active mode."""
        if self.active_mode == MODE_AI_AUTO and self.ai_mode and not self.game_over and not self.game_won:
            current_time = pygame.time.get_ticks()
            # Move only if enough milliseconds have passed since the last move
            if current_time - self.last_ai_move_time >= self.ai_move_delay:
                self.last_ai_move_time = current_time
                self._execute_ai_step()

        if self.active_mode == MODE_CHALLENGE:
            self._update_challenge_runtime()

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

    def draw_footer(self):
        """Draw the instructions, move count, and status text at the bottom."""
        footer_top = SCREEN_HEIGHT
        footer_height = FOOTER_HEIGHT

        panel_rect = pygame.Rect(0, footer_top, SCREEN_WIDTH, footer_height)
        pygame.draw.rect(self.screen, (242, 244, 248), panel_rect)
        pygame.draw.rect(self.screen, (210, 216, 224), panel_rect, 2)

        accent_rect = pygame.Rect(0, footer_top, SCREEN_WIDTH, 6)
        pygame.draw.rect(self.screen, (74, 144, 226), accent_rect)

        title_text = "AI-Based Fire Escape Game"
        subtitle_text = "Using A* Search"
        moves_text = f"Moves: {self.moves_count}"
        mode_text = f"Mode: {self.active_mode}"
        controls_text = "WASD: Move | SPACE: Toggle AI | H: AI Path | R: Restart | ESC: Quit"
        if self.active_mode == MODE_CHALLENGE:
            controls_text = "WASD: Move | H: AI Path | R: Restart | ESC: Quit"

        # Calculate path information for the status display
        path_found = len(self.ai_path) > 0
        remaining_steps = len(self.current_path)
        path_cost = int(self.ai_path_cost) if path_found and self.ai_path_cost is not None else 0

        if self.game_won:
            status_text = "You Escaped Successfully!"
        elif self.game_over:
            status_text = self.status_message or "Game Over!"
        else:
            status_text = self.status_message or "Find a safe path to an exit."

        self.draw_block_text(title_text, 10, footer_top + 12, TEXT_COLOR, scale=2, spacing=2)
        self.draw_block_text(subtitle_text, 10, footer_top + 28, (90, 96, 105), scale=1, spacing=1)
        self.draw_block_text(moves_text, 10, footer_top + 48, TEXT_COLOR, scale=1, spacing=1)
        self.draw_block_text(mode_text, 140, footer_top + 48, TEXT_COLOR, scale=1, spacing=1)
        if self.active_mode == MODE_CHALLENGE:
            challenge_text = (
                f"Difficulty: {self.selected_difficulty} | "
                f"Time Left: {self.challenge_remaining_sec}s | "
                f"Score: {self.challenge_score}"
            )
            self.draw_block_text(challenge_text, 10, footer_top + 60, TEXT_COLOR, scale=1, spacing=1)
            status_y_text = footer_top + 78
        else:
            status_y_text = footer_top + 72
        self.draw_block_text(status_text, 10, status_y_text, (180, 78, 48) if self.game_over else TEXT_COLOR, scale=1, spacing=1)
        self.draw_block_text(controls_text, 10, footer_top + 96, (90, 96, 105), scale=1, spacing=1)

        # Draw the status panel background
        status_y = footer_top + 10
        path_status = "Path: Found" if path_found else "Path: NOT FOUND"
        path_status_color = (46, 204, 113) if path_found else (220, 53, 69)

        status_text1 = self.status_font.render(f"Mode: {self.active_mode}", True, TEXT_COLOR)
        status_text2 = self.status_font.render(path_status, True, path_status_color)
        status_text3 = self.status_font.render(f"Path Cost: {path_cost} | Steps: {remaining_steps}", True, TEXT_COLOR)

        status_panel = pygame.Rect(10, status_y + 115, SCREEN_WIDTH - 20, 12)
        pygame.draw.rect(self.screen, (240, 240, 245), status_panel)
        pygame.draw.rect(self.screen, (200, 210, 220), status_panel, 1)

        self.screen.blit(status_text1, (15, status_y + 117))
        self.screen.blit(status_text2, (120, status_y + 117))
        self.screen.blit(status_text3, (220, status_y + 117))

    def draw_menu(self):
        """Draw simple keyboard-based menu at startup."""
        self.screen.fill((30, 30, 35))
        title = self.status_font.render("Fire Escape AI Game - Mode Selection", True, (240, 240, 245))
        opt1 = self.status_font.render("1 - Manual Mode", True, (200, 200, 200))
        opt2 = self.status_font.render("2 - AI Auto Mode", True, (200, 200, 200))
        opt3 = self.status_font.render("3 - Challenge Mode", True, (200, 200, 200))
        hint = self.status_font.render("Use keys 1/2/3 to select. Press ENTER to start.", True, (180, 180, 180))
        selected = self.status_font.render(f"Selected: {self.selected_mode}", True, (140, 220, 140))

        self.screen.blit(title, (20, 20))
        self.screen.blit(opt1, (40, 70))
        self.screen.blit(opt2, (40, 100))
        self.screen.blit(opt3, (40, 130))
        self.screen.blit(hint, (20, 180))
        self.screen.blit(selected, (20, 220))
        pygame.display.flip()

    def draw(self):
        """Draw the board, optional AI path, and footer text or menu."""
        if self.show_menu:
            self.draw_menu()
            return

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
