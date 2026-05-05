"""
Player class for the Fire Escape AI Game.

This module manages:
- Player position (row, col) tracking
- Movement validation (can't walk through walls or fire)
- Move counting for scoring
- Position conversion between board (row, col) and screen (x, y) formats

The player is the human-controlled character trying to escape the fire.
In Manual Mode, WASD keys control movement.
In AI Auto Mode, the AI chooses movement direction.
In Challenge Mode, the player must escape before time runs out.
"""

from config import EXIT, FIRE, WALL


class Player:
    """Store the player position and movement count."""

    def __init__(self, start_position, game_board):
        """Create a player from a starting position."""
        self.game_board = game_board
        self.row, self.col = self._to_row_col(start_position)
        self.moves = 0

    def _to_row_col(self, position):
        """Convert an incoming position into (row, col)."""
        first, second = position

        # The game still passes positions around as (x, y), so convert to (row, col).
        return second, first

    def get_position(self):
        """Return the player's current position as (x, y) for compatibility."""
        return (self.col, self.row)

    def move(self, direction, board, allow_fire=False):
        """Move the player one step in the given direction."""
        new_row, new_col = self.row, self.col

        if direction == "UP":
            new_row -= 1
        elif direction == "DOWN":
            new_row += 1
        elif direction == "LEFT":
            new_col -= 1
        elif direction == "RIGHT":
            new_col += 1
        else:
            return False

        if not board.is_inside_grid(new_row, new_col):
            return False

        target = board.get_cell(new_row, new_col)

        if target == WALL:
            return False

        # Allow moving into fire only when explicitly permitted.
        if target == FIRE and not allow_fire:
            return False

        old_position = (self.row, self.col)
        new_position = (new_row, new_col)

        board.update_player_position(old_position, new_position)
        self.row, self.col = new_position
        self.moves += 1
        return True

    def try_move(self, direction):
        """Compatibility wrapper used by the current main game loop."""
        target_row, target_col = self.row, self.col

        if direction == "UP":
            target_row -= 1
        elif direction == "DOWN":
            target_row += 1
        elif direction == "LEFT":
            target_col -= 1
        elif direction == "RIGHT":
            target_col += 1
        else:
            return {"moved": False, "fire": False, "exit": False}

        if not self.game_board.is_inside_grid(target_row, target_col):
            return {"moved": False, "fire": False, "exit": False}

        target_cell = self.game_board.get_cell(target_row, target_col)
        # Default wrapper does not allow moving into fire
        moved = self.move(direction, self.game_board, allow_fire=False)

        return {
            "moved": moved,
            "fire": target_cell == FIRE,
            "exit": target_cell == EXIT,
        }

    def reset_to_start(self, start_position):
        """Reset the player to a starting position."""
        self.row, self.col = self._to_row_col(start_position)
        self.moves = 0