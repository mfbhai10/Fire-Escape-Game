"""
A* pathfinding for the Fire Escape AI Game. [VERSION 1 CORE]

This module implements the A* algorithm for finding the safest path from
the player to any exit. It's the core of both AI Auto Mode and the hint system.

Key concepts:
- A* uses f_score = g_score + heuristic to explore nodes efficiently
- g_score: actual cost from start to current node
- heuristic: estimated cost to nearest exit (Manhattan distance)
- Smoke costs 4x more than empty, walls/fire are impassable (cost = infinity)
- Returns lowest-cost path to whichever exit is nearest

Usage:
  path, cost, selected_exit = astar_search(board, start_pos, [exit_pos1, exit_pos2])
  - path: list of (row, col) positions from start to exit
  - cost: total movement cost of the path
  - selected_exit: which exit was reached
"""

import heapq

from config import EMPTY, EXIT, FIRE, SMOKE, WALL, EMPTY_COST, SMOKE_COST, EXIT_COST


def manhattan_distance(pos1, pos2):
    """Return the Manhattan distance between two positions."""
    # Manhattan distance counts only up/down/left/right steps, so it fits grid movement.
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def heuristic(current, exits):
    """Return the minimum Manhattan distance from current to any exit."""
    if not exits:
        return 0

    # A* compares the current cell to every exit and keeps the smallest estimate.
    return min(manhattan_distance(current, exit_pos) for exit_pos in exits)


def reconstruct_path(came_from, current):
    """Rebuild the path from the start node to the current node."""
    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path


def _cell_cost(board, row, col):
    """Return the movement cost for a board cell."""
    cell = board.get_cell(row, col)

    if cell == EMPTY:
        return EMPTY_COST
    if cell == SMOKE:
        return SMOKE_COST
    if cell == EXIT:
        return EXIT_COST
    return float("inf")


def astar_search(board, start, exits):
    """Find the safest path from start to any of the given exits. [VERSION 1 CORE]

    This is the core pathfinding algorithm used throughout the game. It uses the A*
    algorithm with Manhattan distance heuristic to find the lowest-cost path to the
    nearest exit. Smoke is allowed but costs 4x more than empty cells.

    Returns a tuple: (path, total_cost, selected_exit)
    - path: list of (row, col) from start to selected_exit (inclusive), or [] if no path
    - total_cost: sum of movement costs along the path, or None if no path
    - selected_exit: the exit cell (row, col) chosen, or None if no path

    The heuristic is the Manhattan distance to the nearest exit (admissible),
    smoke cells have higher movement cost, and fire/walls are treated as blocked.
    The function is reusable for manual hint mode and AI Auto Mode.
    """
    if not exits:
        return [], None, None

    exit_set = set(exits)

    open_heap = []  # elements are (f_score, g_score, (row, col))
    came_from = {}
    g_score = {start: 0}
    closed_set = set()

    start_f = heuristic(start, exits)
    heapq.heappush(open_heap, (start_f, 0, start))

    # Main A* loop: expand nodes with lowest f = g + h first
    while open_heap:
        _, current_g, current = heapq.heappop(open_heap)

        if current in closed_set:
            continue

        closed_set.add(current)

        # Goal test: current node is any exit
        if current in exit_set:
            # Reconstruct and return the path, its total cost, and the exit reached
            path = reconstruct_path(came_from, current)
            total_cost = g_score.get(current, 0)
            return path, total_cost, current

        row, col = current
        neighbors = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]

        for next_row, next_col in neighbors:
            if not board.is_inside_grid(next_row, next_col):
                continue

            # Treat walls and fire as blocked
            if board.is_blocked(next_row, next_col):
                continue

            step_cost = _cell_cost(board, next_row, next_col)
            if step_cost == float("inf"):
                continue

            tentative_g = current_g + step_cost
            neighbor = (next_row, next_col)

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, exits)
                heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

    # No path found to any exit
    return [], None, None


def astar(start, goal, grid, grid_width, grid_height):
    """Compatibility wrapper for the older game loop API."""
    class GridBoardAdapter:
        def __init__(self, board_grid, width, height):
            self.grid = board_grid
            self.width = width
            self.height = height

        def is_inside_grid(self, row, col):
            return 0 <= row < self.height and 0 <= col < self.width

        def is_blocked(self, row, col):
            cell = self.grid[row][col]
            return cell == WALL or cell == FIRE

        def get_cell(self, row, col):
            return self.grid[row][col]

    board = GridBoardAdapter(grid, grid_width, grid_height)
    start_cell = (start[1], start[0])
    goal_cell = (goal[1], goal[0])

    path, total_cost, selected_exit = astar_search(board, start_cell, [goal_cell])

    # Convert the path back to x/y positions for the current game loop.
    return [(col, row) for row, col in path]