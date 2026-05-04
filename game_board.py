"""
Game board management for the Fire Escape AI Game.
"""

import pygame

from config import (
    GRID_ROWS,
    GRID_COLS,
    CELL_SIZE,
    EMPTY,
    WALL,
    FIRE,
    SMOKE,
    PLAYER,
    EXIT,
    PATH,
    EMPTY_COST,
    SMOKE_COST,
    EXIT_COST,
    WALL_COLOR,
    FIRE_COLOR,
    SMOKE_COLOR,
    PLAYER_COLOR,
    EXIT_COLOR,
    PATH_COLOR,
    NEXT_MOVE_COLOR,
    VISITED_COLOR,
    EMPTY_CELL_COLOR,
    GRID_LINE_COLOR,
)


class GameBoard:
    """
    Store the fixed game map and helper methods for board logic.
    """

    ICON_FONT = {
        "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
        "E": ["#####", "#    ", "#### ", "#    ", "#####"],
        "F": ["#####", "#    ", "#### ", "#    ", "#    "],
        "S": [" ####", "#    ", " ### ", "    #", "#### "],
    }

    RAW_MAP = [
        # This grid is the game map. Each symbol shows what is in one cell.
        "###############",
        "#P...S...E....#",
        "#...#.........#",
        "#...#....SS...#",
        "#...#..FF.....#",
        "#...#..FF.....#",
        "#...#.........#",
        "#...#..###....#",
        "#........#....#",
        "#...#.........#",
        "#...#..SS.....#",
        "#...#.........#",
        "#...#.........#",
        "#............E#",
        "###############",
    ]

    def __init__(self):
        """Create the board from the fixed 15x15 symbol map."""
        self.rows = GRID_ROWS
        self.cols = GRID_COLS
        self.height = GRID_ROWS
        self.width = GRID_COLS

        self.grid = [list(row) for row in self.RAW_MAP]

        # Keep both row/col positions and x/y-compatible positions.
        self.player_start_cell = self.find_player()
        self.exit_cells = self.find_exits()
        self.player_start = self._cell_to_xy(self.player_start_cell)
        self.exits = [self._cell_to_xy(cell) for cell in self.exit_cells]

        self._validate_map()

    def _validate_map(self):
        """Make sure the fixed map matches the expected board size."""
        if len(self.grid) != self.rows:
            raise ValueError("Game board must have 15 rows.")

        for row in self.grid:
            if len(row) != self.cols:
                raise ValueError("Every game board row must have 15 columns.")

    def _cell_to_xy(self, cell):
        """Convert a (row, col) cell position to (x, y) coordinates."""
        row, col = cell
        return (col, row)

    def _xy_to_cell(self, position):
        """Convert an (x, y) position to a (row, col) cell position."""
        x, y = position
        return (y, x)

    def find_player(self):
        """Return the player position as a (row, col) tuple."""
        for row_index, row in enumerate(self.grid):
            for col_index, cell in enumerate(row):
                if cell == PLAYER:
                    return (row_index, col_index)
        return None

    def find_exits(self):
        """Return a list of all exit positions as (row, col) tuples."""
        exits = []
        for row_index, row in enumerate(self.grid):
            for col_index, cell in enumerate(row):
                if cell == EXIT:
                    exits.append((row_index, col_index))
        return exits

    def is_inside_grid(self, row, col):
        """Return True when the given cell is inside the board."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_cell(self, row, col):
        """Return the cell value at a given (row, col) position."""
        if self.is_inside_grid(row, col):
            return self.grid[row][col]
        return WALL

    def is_blocked(self, row, col):
        """Return True if the cell is blocked by a wall or fire."""
        cell = self.get_cell(row, col)
        # Walls block movement because they are solid obstacles.
        # Fire is also blocked here so the pathfinder avoids dangerous cells.
        return cell == WALL or cell == FIRE

    def get_cell_cost(self, row, col):
        """Return the movement cost for the given cell."""
        cell = self.get_cell(row, col)

        if cell == EMPTY:
            return EMPTY_COST
        if cell == SMOKE:
            # Smoke has a higher cost because it is harder and slower to move through.
            return SMOKE_COST
        if cell == EXIT:
            return EXIT_COST
        return float("inf")

    def update_player_position(self, old_pos, new_pos):
        """Move the player marker from one cell to another."""
        old_row, old_col = old_pos
        new_row, new_col = new_pos

        if self.is_inside_grid(old_row, old_col):
            self.grid[old_row][old_col] = EMPTY

        if self.is_inside_grid(new_row, new_col):
            self.grid[new_row][new_col] = PLAYER

        self.player_start_cell = new_pos
        self.player_start = self._cell_to_xy(new_pos)

    def draw(self, screen, path=None, next_cell=None, visited=None, player_pos=None, highlight_player=False):
        """Draw the board and optional AI path using Pygame.

        Parameters:
        - path: iterable of (row, col) cells representing the A* path
        - next_cell: (row, col) tuple indicating the next AI move
        - visited: iterable of (row, col) already visited by the AI
        """
        path_cells = set(path or [])
        visited_cells = set(visited or [])
        next_cell = next_cell if next_cell is not None else None

        # Draw a clean board background first.
        board_rect = pygame.Rect(0, 0, self.cols * CELL_SIZE, self.rows * CELL_SIZE)
        pygame.draw.rect(screen, (235, 239, 244), board_rect)

        for row_index in range(self.rows):
            for col_index in range(self.cols):
                cell = self.grid[row_index][col_index]
                rect = pygame.Rect(
                    col_index * CELL_SIZE,
                    row_index * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )

                # Base color for this cell
                color = self._get_cell_color(cell)

                # Overlays: next move, visited, path. Do not overlay special cells.
                is_special = cell in (PLAYER, EXIT, FIRE, WALL)

                if not is_special:
                    if next_cell == (row_index, col_index):
                        color = NEXT_MOVE_COLOR
                    elif (row_index, col_index) in visited_cells:
                        color = VISITED_COLOR
                    elif (row_index, col_index) in path_cells:
                        color = PATH_COLOR

                inner_rect = rect.inflate(-4, -4)
                pygame.draw.rect(screen, color, inner_rect, border_radius=6)

                # Optional pulsing highlight around the player when AI mode is active
                if highlight_player and player_pos is not None and cell == PLAYER:
                    try:
                        ticks = pygame.time.get_ticks()
                        phase = (ticks % 800) / 800.0
                        border_width = 2 + int(phase * 3)
                    except Exception:
                        border_width = 2

                    border_rect = rect.inflate(-6, -6)
                    pygame.draw.rect(screen, PLAYER_COLOR, border_rect, width=border_width, border_radius=8)

                if cell in (PLAYER, EXIT, FIRE, SMOKE):
                    icon = self._get_icon(cell)
                    if icon:
                        self._draw_icon(screen, icon, inner_rect, self._get_icon_color(cell))

        self._draw_grid_lines(screen)

    def _draw_grid_lines(self, screen):
        """Draw simple grid lines over the whole board."""
        for row_index in range(self.rows + 1):
            y = row_index * CELL_SIZE
            pygame.draw.line(screen, GRID_LINE_COLOR, (0, y), (self.cols * CELL_SIZE, y))

        for col_index in range(self.cols + 1):
            x = col_index * CELL_SIZE
            pygame.draw.line(screen, GRID_LINE_COLOR, (x, 0), (x, self.rows * CELL_SIZE))

    def _get_cell_color(self, cell):
        """Map a cell symbol to its display color."""
        if cell == EMPTY:
            return EMPTY_CELL_COLOR
        if cell == WALL:
            return WALL_COLOR
        if cell == FIRE:
            return FIRE_COLOR
        if cell == SMOKE:
            return SMOKE_COLOR
        if cell == PLAYER:
            return PLAYER_COLOR
        if cell == EXIT:
            return EXIT_COLOR
        if cell == PATH:
            return PATH_COLOR
        return EMPTY_CELL_COLOR

    def _get_icon(self, cell):
        """Return the symbol icon pattern for special cells."""
        if cell == PLAYER:
            return self.ICON_FONT["P"]
        if cell == EXIT:
            return self.ICON_FONT["E"]
        if cell == FIRE:
            return self.ICON_FONT["F"]
        if cell == SMOKE:
            return self.ICON_FONT["S"]
        return None

    def _get_icon_color(self, cell):
        """Return a readable color for the icon on a given cell."""
        if cell in (PLAYER, EXIT, FIRE):
            return (255, 255, 255)
        if cell == SMOKE:
            return (40, 40, 40)
        return (255, 255, 255)

    def _draw_icon(self, screen, icon_lines, rect, color):
        """Draw a simple block-style icon centered in a cell."""
        icon_width = len(icon_lines[0])
        icon_height = len(icon_lines)
        scale = max(2, min(rect.width // (icon_width + 1), rect.height // (icon_height + 1)))

        icon_pixel_width = icon_width * scale
        icon_pixel_height = icon_height * scale
        start_x = rect.x + (rect.width - icon_pixel_width) // 2
        start_y = rect.y + (rect.height - icon_pixel_height) // 2

        for row_index, row in enumerate(icon_lines):
            for col_index, pixel in enumerate(row):
                if pixel != " ":
                    pixel_rect = pygame.Rect(
                        start_x + col_index * scale,
                        start_y + row_index * scale,
                        scale,
                        scale,
                    )
                    pygame.draw.rect(screen, color, pixel_rect)

    def is_valid_position(self, x, y):
        """Compatibility helper used by the current player logic."""
        row, col = self._xy_to_cell((x, y))
        return self.is_inside_grid(row, col) and not self.is_blocked(row, col)

    def is_fire(self, x, y):
        """Compatibility helper used by the current player logic."""
        row, col = self._xy_to_cell((x, y))
        return self.get_cell(row, col) == FIRE

    def is_exit(self, x, y):
        """Compatibility helper used by the current player logic."""
        row, col = self._xy_to_cell((x, y))
        return self.get_cell(row, col) == EXIT

    def get_nearest_exit(self, position):
        """Return the nearest exit as an (x, y) position for compatibility."""
        if not self.exit_cells:
            return None

        x, y = position
        nearest_cell = min(
            self.exit_cells,
            key=lambda cell: abs(x - cell[1]) + abs(y - cell[0]),
        )
        return self._cell_to_xy(nearest_cell)