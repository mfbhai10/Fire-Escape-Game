"""
Game board management for the Fire Escape AI Game.

This module handles:
- Random board generation with difficulty-based sizing
- A* solvability validation to ensure all maps have an exit
- Cell management and grid queries (is this cell walkable?)
- Fire spreading mechanics (two-phase snapshot-based)
- Board rendering with animations (fire pulsing, path overlays)
- Position tracking and coordinate conversions (row/col vs x/y)

Key concepts:
- The board is a 2D grid of cells (EMPTY, WALL, FIRE, SMOKE, etc.)
- Fire spreads in snapshot to prevent cascading (new fire doesn't spread same turn)
- All boards are validated with A* before use to guarantee exits exist
"""

import random

import pygame

from astar import astar_search

from config import (
    CELL_SIZE,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_SETTINGS,
    EMPTY,
    EMPTY_CELL_COLOR,
    EMPTY_COST,
    EXIT,
    EXIT_COLOR,
    EXIT_COST,
    FIRE,
    FIRE_COLOR,
    FIRE_COLOR_ALT,
    GRID_LINE_COLOR,
    GRID_COLS,
    GRID_ROWS,
    NEXT_MOVE_COLOR,
    PATH,
    PATH_COLOR,
    PLAYER,
    PLAYER_COLOR,
    SMOKE,
    SMOKE_COLOR,
    SMOKE_COST,
    WALL,
    WALL_COLOR,
    VISITED_COLOR,
)


class GameBoard:
    """Store the generated game map and helper methods for board logic."""

    ICON_FONT = {
        "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
        "E": ["#####", "#    ", "#### ", "#    ", "#####"],
        "F": ["#####", "#    ", "#### ", "#    ", "#    "],
        "S": [" ####", "#    ", " ### ", "    #", "#### "],
    }

    def __init__(self, difficulty=DEFAULT_DIFFICULTY):
        """Create a random board using the selected difficulty settings."""
        self.difficulty = difficulty if difficulty in DIFFICULTY_SETTINGS else DEFAULT_DIFFICULTY
        self.settings = DIFFICULTY_SETTINGS[self.difficulty]
        self.rows = self.settings["rows"]
        self.cols = self.settings["cols"]
        self.height = self.rows
        self.width = self.cols

        self.grid = self._generate_valid_grid()

        # Keep both row/col positions and x/y-compatible positions.
        self.player_start_cell = self.find_player()
        self.exit_cells = self.find_exits()
        self.player_start = self._cell_to_xy(self.player_start_cell)
        self.exits = [self._cell_to_xy(cell) for cell in self.exit_cells]

        self._validate_map()

    def _validate_map(self):
        """Make sure the generated map matches the expected board size."""
        if len(self.grid) != self.rows:
            raise ValueError(f"Game board must have {self.rows} rows for {self.difficulty} difficulty.")

        for row in self.grid:
            if len(row) != self.cols:
                raise ValueError(f"Every game board row must have {self.cols} columns for {self.difficulty} difficulty.")

    def _generate_valid_grid(self):
        """Generate random maps until A* confirms that at least one route exists."""
        base_counts = {
            "wall_count": self.settings["wall_count"],
            "fire_count": self.settings["fire_count"],
            "smoke_count": self.settings["smoke_count"],
        }

        attempts_per_round = 10
        obstacle_scale = 1.0
        max_rounds = 5

        for round_index in range(max_rounds):
            adjusted_counts = {
                name: max(0, int(count * obstacle_scale))
                for name, count in base_counts.items()
            }

            for attempt_index in range(attempts_per_round):
                grid, player_cell, exits = self._build_random_grid(adjusted_counts)
                self.grid = grid
                self.player_start_cell = player_cell
                self.exit_cells = exits
                self.player_start = self._cell_to_xy(player_cell)
                self.exits = [self._cell_to_xy(cell) for cell in exits]

                if self._is_map_solvable():
                    print(
                        f"Generated valid {self.difficulty} map on round {round_index + 1}, "
                        f"attempt {attempt_index + 1}."
                    )
                    return grid

            # If the map still is not solvable, reduce obstacle counts and try again.
            obstacle_scale *= 0.8

        # Final fallback: use a very open map so the game never gets stuck in generation.
        fallback_grid, player_cell, exits = self._build_random_grid(
            {"wall_count": 0, "fire_count": 0, "smoke_count": 0}
        )
        self.grid = fallback_grid
        self.player_start_cell = player_cell
        self.exit_cells = exits
        self.player_start = self._cell_to_xy(player_cell)
        self.exits = [self._cell_to_xy(cell) for cell in exits]

        print(f"Generated fallback {self.difficulty} map after repeated retries.")
        return fallback_grid

    def _build_random_grid(self, counts):
        """Build one random board using the provided obstacle counts."""
        grid = [[EMPTY for _ in range(self.cols)] for _ in range(self.rows)]

        # Surround the board with walls so the player cannot move off-grid.
        for row_index in range(self.rows):
            for col_index in range(self.cols):
                if row_index in (0, self.rows - 1) or col_index in (0, self.cols - 1):
                    grid[row_index][col_index] = WALL

        interior_cells = [
            (row_index, col_index)
            for row_index in range(1, self.rows - 1)
            for col_index in range(1, self.cols - 1)
        ]

        player_cell = random.choice(interior_cells)
        grid[player_cell[0]][player_cell[1]] = PLAYER

        available_cells = [cell for cell in interior_cells if cell != player_cell]
        exit_count = max(2 if self.difficulty != "HARD" else 3, self.settings["exit_count"])
        exit_count = min(exit_count, len(available_cells))
        exits = random.sample(available_cells, exit_count)

        for row_index, col_index in exits:
            grid[row_index][col_index] = EXIT

        reserved_cells = {player_cell, *exits}
        self._place_random_cells(grid, WALL, counts["wall_count"], reserved_cells)
        self._place_random_cells(grid, FIRE, counts["fire_count"], reserved_cells)
        self._place_random_cells(grid, SMOKE, counts["smoke_count"], reserved_cells)

        return grid, player_cell, exits

    def _place_random_cells(self, grid, cell_type, count, reserved_cells):
        """Place the requested number of cells without overwriting reserved cells."""
        available_cells = [
            (row_index, col_index)
            for row_index in range(1, self.rows - 1)
            for col_index in range(1, self.cols - 1)
            if (row_index, col_index) not in reserved_cells and grid[row_index][col_index] == EMPTY
        ]

        if not available_cells:
            return

        actual_count = min(count, len(available_cells))
        for row_index, col_index in random.sample(available_cells, actual_count):
            grid[row_index][col_index] = cell_type

    def _is_map_solvable(self):
        """Return True when A* can reach at least one exit from the player start."""
        if self.player_start_cell is None or not self.exit_cells:
            return False

        path, _, _ = astar_search(self, self.player_start_cell, self.exit_cells)
        return bool(path)

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

    def spread_fire(self, spread_probability, allow_fire_overwrite_exits=False):
        """Spread fire one step using a frozen snapshot of the current map. [VERSION 3]

        Fire spreads in two phases to prevent cascading:
        - Phase 1: Existing fire spreads to adjacent empty cells (becoming smoke) and
                   to adjacent smoke cells (which may ignite with lower probability)
        - Phase 2: Existing smoke near fire can ignite if it survives Phase 1
        
        The snapshot prevents newly created fire from spreading again in the same turn,
        making the fire spread feel gradual and giving the player time to react.
        
        Parameters:
        - spread_probability: Base probability (0-1) for empty→smoke and smoke→fire
        - allow_fire_overwrite_exits: If True, exits can eventually burn (rare)
        
        Returns list of (row, col) cells that changed.
        """
        fire_sources = [
            (row_index, col_index)
            for row_index in range(self.rows)
            for col_index in range(self.cols)
            if self.grid[row_index][col_index] == FIRE
        ]
        smoke_sources = [
            (row_index, col_index)
            for row_index in range(self.rows)
            for col_index in range(self.cols)
            if self.grid[row_index][col_index] == SMOKE
        ]

        new_smoke_cells = set()
        new_fire_cells = set()

        def get_neighbors(row_index, col_index):
            return [
                (row_index - 1, col_index),
                (row_index + 1, col_index),
                (row_index, col_index - 1),
                (row_index, col_index + 1),
            ]

        # Phase 1: fire spreads outward, but only one step from the original fire cells.
        for row_index, col_index in fire_sources:
            for next_row, next_col in get_neighbors(row_index, col_index):
                if not self.is_inside_grid(next_row, next_col):
                    continue

                target_cell = self.grid[next_row][next_col]

                # Walls stop the spread completely.
                if target_cell == WALL:
                    continue

                # Exits are protected unless a difficulty explicitly allows them to burn.
                if target_cell == EXIT and not allow_fire_overwrite_exits:
                    continue

                # Fire can immediately end the game if it reaches the player.
                if target_cell == PLAYER:
                    new_fire_cells.add((next_row, next_col))
                    continue

                # Empty cells become smoke first so the spread feels gradual.
                if target_cell == EMPTY and random.random() <= spread_probability:
                    new_smoke_cells.add((next_row, next_col))

                # Smoke close to fire can ignite, but we keep the probability lower.
                if target_cell == SMOKE and random.random() <= (spread_probability * 0.6):
                    new_fire_cells.add((next_row, next_col))

                # If exits are allowed to burn, they do so very slowly.
                if target_cell == EXIT and allow_fire_overwrite_exits and random.random() <= (spread_probability * 0.25):
                    new_fire_cells.add((next_row, next_col))

        # Phase 2: smoke that is already on the map can ignite later if it is near fire.
        for row_index, col_index in smoke_sources:
            if (row_index, col_index) in new_fire_cells:
                continue

            neighbors = get_neighbors(row_index, col_index)
            near_fire = any(
                self.is_inside_grid(next_row, next_col) and self.grid[next_row][next_col] == FIRE
                for next_row, next_col in neighbors
            )

            if near_fire and random.random() <= (spread_probability * 0.4):
                new_fire_cells.add((row_index, col_index))

        # Apply smoke first, then fire, so the map changes in a readable order.
        for row_index, col_index in new_smoke_cells:
            if self.grid[row_index][col_index] == EMPTY:
                self.grid[row_index][col_index] = SMOKE

        for row_index, col_index in new_fire_cells:
            if self.grid[row_index][col_index] != WALL:
                self.grid[row_index][col_index] = FIRE

        changed_cells = sorted(new_smoke_cells | new_fire_cells)
        return changed_cells

    def draw(self, screen, path=None, next_cell=None, visited=None, player_pos=None, highlight_player=False, cell_size=None):
        """Draw the board with animated cells and optional AI path using Pygame. [VERSION 2]

        Renders cells with smooth fire animation and visual overlays for the AI path.
        Visited cells show where the AI has been, the path shows the planned route,
        and the next cell indicates the AI's next move.

        Parameters:
        - path: iterable of (row, col) cells representing the A* path
        - next_cell: (row, col) tuple indicating the next AI move
        - visited: iterable of (row, col) already visited by the AI
        - cell_size: size of each cell in pixels (defaults to CELL_SIZE from config)
        """
        if cell_size is None:
            cell_size = CELL_SIZE
            
        path_cells = set(path or [])
        visited_cells = set(visited or [])
        next_cell = next_cell if next_cell is not None else None
        
        # Get current animation frame time for fire effects
        current_ticks = pygame.time.get_ticks()

        # Draw a clean board background first.
        board_rect = pygame.Rect(0, 0, self.cols * cell_size, self.rows * cell_size)
        pygame.draw.rect(screen, (235, 239, 244), board_rect)

        for row_index in range(self.rows):
            for col_index in range(self.cols):
                cell = self.grid[row_index][col_index]
                rect = pygame.Rect(
                    col_index * cell_size,
                    row_index * cell_size,
                    cell_size,
                    cell_size,
                )

                # Get base color for this cell (with animation support for fire)
                color = self._get_cell_color(cell, current_ticks)

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
                        phase = (current_ticks % 800) / 800.0
                        border_width = 2 + int(phase * 3)
                    except Exception:
                        border_width = 2

                    border_rect = rect.inflate(-6, -6)
                    pygame.draw.rect(screen, PLAYER_COLOR, border_rect, width=border_width, border_radius=8)

                if cell in (PLAYER, EXIT, FIRE, SMOKE):
                    icon = self._get_icon(cell)
                    if icon:
                        self._draw_icon(screen, icon, inner_rect, self._get_icon_color(cell))

        self._draw_grid_lines(screen, cell_size)

    def _draw_grid_lines(self, screen, cell_size=None):
        """Draw simple grid lines over the whole board."""
        if cell_size is None:
            cell_size = CELL_SIZE
            
        for row_index in range(self.rows + 1):
            y = row_index * cell_size
            pygame.draw.line(screen, GRID_LINE_COLOR, (0, y), (self.cols * cell_size, y))

        for col_index in range(self.cols + 1):
            x = col_index * cell_size
            pygame.draw.line(screen, GRID_LINE_COLOR, (x, 0), (x, self.rows * cell_size))

    def _get_cell_color(self, cell, current_ticks=None):
        """Map a cell symbol to its display color. [VERSION 2 ANIMATION]
        
        Fire cells are animated between red and orange for visual interest, cycling
        every 600ms. The animation uses a smooth pulsing effect where the blend starts
        at 0 (red), reaches 1 at 300ms (orange), then returns to 0 at 600ms (red).
        
        Parameters:
        - cell: the cell symbol to get color for
        - current_ticks: pygame.time.get_ticks() value for animation timing
        """
        if cell == EMPTY:
            return EMPTY_CELL_COLOR
        if cell == WALL:
            return WALL_COLOR
        if cell == FIRE:
            # Animate fire between red and orange for visual interest
            if current_ticks is not None:
                # Cycle every 600ms between the two fire colors
                cycle = (current_ticks % 600) / 600.0
                # Use a smooth step function (0 to 1) for pulsing effect
                if cycle < 0.5:
                    # First half: red to orange
                    blend = cycle * 2  # 0 to 1
                else:
                    # Second half: orange back to red
                    blend = (1 - cycle) * 2  # 1 to 0
                
                # Interpolate between FIRE_COLOR and FIRE_COLOR_ALT
                r = int(FIRE_COLOR[0] + (FIRE_COLOR_ALT[0] - FIRE_COLOR[0]) * blend)
                g = int(FIRE_COLOR[1] + (FIRE_COLOR_ALT[1] - FIRE_COLOR[1]) * blend)
                b = int(FIRE_COLOR[2] + (FIRE_COLOR_ALT[2] - FIRE_COLOR[2]) * blend)
                return (r, g, b)
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