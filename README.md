# AI-Based Fire Escape Game Using A\* Search Algorithm

## Project Overview

This project is a grid-based fire escape game made with Python and Pygame.
The player starts on a grid map and must reach an exit safely while avoiding walls and fire.
Smoke cells are allowed, but they are harder to cross.

An AI helper uses the A\* Search algorithm to suggest the safest path to an exit.
You can show or hide that path during the game.

## Features of Version 1

- Grid-based board
- Manual player movement
- Walls and obstacles
- Fire danger zones
- Smoke cells with higher movement cost
- Multiple exits
- A\* safest pathfinding
- Toggle AI path using H
- Win/Lose condition

## Algorithm Used

The AI uses A\* Search to find the safest path.

The algorithm uses this formula:

$$f(n) = g(n) + h(n)$$

- $g(n)$ = actual cost from the start to the current cell
- $h(n)$ = Manhattan distance from the current cell to the nearest exit
- $f(n)$ = total estimated cost

### Why Manhattan Distance Is Used

Manhattan distance works well here because movement is only allowed in four directions:
up, down, left, and right.
It gives a simple and efficient estimate of how far a cell is from an exit.

### How the Safest Path Is Selected

A\* checks cells with the lowest estimated total cost first.
That means it prefers paths that are both short and safe.
Smoke cells are still allowed, but they are less attractive because they cost more.

## Cell Cost System

- Normal cell = 1
- Smoke cell = 4
- Exit cell = 1
- Wall = blocked
- Fire = blocked

## Controls

- W = Up
- A = Left
- S = Down
- D = Right
- H = Show/Hide AI Path
- R = Restart
- ESC = Quit

## How to Run

1. Install Python.
2. Install Pygame:

   ```bash
   pip install pygame
   ```

3. Run the game:

   ```bash
   python main.py
   ```

## Future Improvements

- Fire spreading
- Timer
- Score system
- Difficulty levels
- Random map generation
- AI Auto Mode
- Challenge Mode

## Project Goal

This game is designed for an Artificial Intelligence Lab project.
It helps students understand grid maps, pathfinding, heuristics, and cost-based movement in a simple game environment.
