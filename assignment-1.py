import heapq
import math


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def a_star(grid, start, goal, heuristic_func):
    n = len(grid)
    m = len(grid[0])

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    open_list = []
    heapq.heappush(open_list, (heuristic_func(start, goal), heuristic_func(start, goal), start))

    g_cost = {start: 0}
    parent = {start: None}
    closed = set()

    expanded_nodes = 0

    while open_list:
        f, h, current = heapq.heappop(open_list)

        if current in closed:
            continue

        closed.add(current)

        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = parent[current]
            path.reverse()
            return path, expanded_nodes

        expanded_nodes += 1

        for dx, dy in directions:
            nr = current[0] + dx
            nc = current[1] + dy
            neighbor = (nr, nc)

            if nr < 0 or nr >= n or nc < 0 or nc >= m:
                continue

            if grid[nr][nc] == '#':
                continue

            if neighbor in closed:
                continue

            new_g = g_cost[current] + 1

            if neighbor not in g_cost or new_g < g_cost[neighbor]:
                g_cost[neighbor] = new_g
                parent[neighbor] = current

                new_h = heuristic_func(neighbor, goal)
                new_f = new_g + new_h

                # Tie-breaking:
                # heap order = f value, then h value, then coordinate
                heapq.heappush(open_list, (new_f, new_h, neighbor))

    return None, expanded_nodes


def print_path(path):
    for i in range(len(path)):
        if i != len(path) - 1:
            print(path[i], end="->")
        else:
            print(path[i])


def print_grid_with_path(grid, path):
    new_grid = [row[:] for row in grid]

    for r, c in path:
        if new_grid[r][c] != 'S' and new_grid[r][c] != 'G':
            new_grid[r][c] = '*'

    for row in new_grid:
        print("".join(row))


# Main Program
n, m = map(int, input().split())

grid = []
start = None
goal = None

for i in range(n):
    row = list(input().strip())
    grid.append(row)

    for j in range(m):
        if row[j] == 'S':
            start = (i, j)
        elif row[j] == 'G':
            goal = (i, j)


path_manhattan, expanded_manhattan = a_star(grid, start, goal, manhattan)
path_euclidean, expanded_euclidean = a_star(grid, start, goal, euclidean)

# Use Manhattan path for final shortest path output
# Because diagonal movement is not allowed, Manhattan is more suitable.
final_path = path_manhattan

if final_path is None:
    print("No path found")
else:
    print("Shortest Path Length:", len(final_path))

    print("Path:")
    print_path(final_path)

    print("Grid with Path:")
    print_grid_with_path(grid, final_path)

    print("Nodes Expanded:")
    print("Euclidean Distance:", expanded_euclidean)
    print("Manhattan Distance:", expanded_manhattan)