# AI-Based Fire Escape Game Using A\* Search Algorithm

## Project Overview

This project is a grid-based fire escape game made with Python and Pygame.
The player starts on a grid map and must reach an exit safely while avoiding walls and fire.
Smoke cells are allowed, but they are harder to cross.

An AI helper uses the A\* Search algorithm to suggest the safest path to an exit.
You can show or hide that path during the game.

## The story of the game is:

A player is trapped inside a burning building. The building contains walls, fire, smoke, and multiple exits. The player must escape safely before the fire spreads or the timer runs out. The game uses the A* Search algorithm to calculate the safest path to the best exit. The AI considers movement cost, danger cost, smoke cost, walls, fire, and distance to the exit. In Manual Mode, the player controls movement with AI path hints. In AI Auto Mode, the AI controls the player automatically. In Challenge Mode, fire spreads after each move, the timer counts down, and A* recalculates the safest route dynamically. The player wins by reaching an exit and loses if trapped, burned, or out of time.

## Features Implemented

### Version 1: Core Pathfinding

- Grid-based board with random generation
- Manual player movement (W/A/S/D)
- Walls and obstacles
- Fire danger zones (blocked)
- Smoke cells with higher movement cost
- Multiple exits
- A\* safest pathfinding algorithm
- Toggle AI path visualization (H key)
- Win/Lose condition detection

### Version 2: User Interface & Multiple Modes

- **Manual Mode**: Player controls movement with A\* path hints
- **AI Auto Mode**: AI automatically moves the player using A\*
- Toggle between modes during gameplay (SPACE key)
- Path visibility toggle (H key)
- Responsive UI with game status footer
- Mode-specific game over behavior

### Version 3: Challenge Mode & Advanced Features

- **Challenge Mode**: Timed mode with dynamic fire spreading
- Fire spreads after each player move (snapshot-based algorithm)
- Countdown timer with difficulty-based time limits
- Score system: `Score = (Time * 10 - Moves * Penalty - Smoke * 5) * Multiplier`
- Three difficulty levels: Easy, Medium, Hard
- Difficulty-specific settings (grid size, time limit, fire probability, obstacles)
- Mode-specific win/game-over screens showing relevant statistics
- Dynamic A\* recalculation as environment changes

### Current Features

- **Main Menu**: Select game mode and difficulty before starting
- **Navigation**: Return to menu at any time (Q key)
- **Restart System**: Press R to start a new game with same mode/difficulty
- **Keyboard Controls**: Full support for menu navigation, gameplay, and end-screen controls
- **Screen States**: Menu → Playing → Win/Game Over → Menu (full cycle)

## Controls

### Main Menu

- **1** = Select Manual Mode
- **2** = Select AI Auto Mode
- **3** = Select Challenge Mode
- **E** = Select Easy difficulty
- **M** = Select Medium difficulty
- **H** = Select Hard difficulty
- **ENTER** or **R** = Start game
- **ESC** = Quit

### During Gameplay

- **W** = Move Up
- **A** = Move Left
- **S** = Move Down
- **D** = Move Right
- **SPACE** = Toggle AI Auto Mode (on/off)
- **C** = Toggle Challenge Mode
- **H** = Show/Hide AI Path
- **Q** = Return to Main Menu
- **R** = Restart (new game, same mode/difficulty)
- **ESC** = Quit

### Win / Game Over Screen

- **R** = Restart (new game, same mode/difficulty)
- **Q** = Return to Main Menu
- **ESC** = Quit

## Game Modes

### Manual Mode

- You control the player movement (W/A/S/D).
- The A\* path is shown as a hint (toggle with H).
- Win by reaching any exit.
- Game Over if you step into fire.
- No timer; no fire spreading.
- You can continue playing even if no safe path exists.

### AI Auto Mode

- The AI automatically moves the player to the safest exit using A\*.
- You can toggle AI on/off with SPACE.
- Path visualization shows the current AI plan.
- Win when AI successfully reaches an exit.
- Game Over if fire reaches the player.
- If no safe path exists, AI stops and shows a message; you can then move manually.
- No timer; no fire spreading.

### Challenge Mode

- **Timed gameplay**: Timer counts down each turn.
- **Dynamic fire spread**: Fire spreads after each player move (affects future pathfinding).
- Score system: Points based on remaining time, moves taken, and smoke crossed.
- Win by reaching an exit before the timer expires or fire traps you.
- Game Over conditions:
  - Timer reaches zero
  - Fire spreads to your position
  - You step into fire
  - No safe path remains and `CHALLENGE_END_GAME_ON_NO_PATH` is enabled
  - All exits become unreachable
- Difficulty affects: grid size, time limit, fire spread probability, number of obstacles, and score multiplier.

## How to Run

### Requirements

- Python 3.8 or higher
- Pygame

### Setup & Run

1. **Clone or download the repository**:

   ```bash
   cd Fire-Escape-Game
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install Pygame**:

   ```bash
   pip install pygame
   ```

4. **Run the game**:

   ```bash
   python3 main.py
   ```

5. **Select a mode and difficulty** from the main menu, then press ENTER to start.

### Troubleshooting

- If `python3 main.py` doesn't work, try `python main.py`
- On macOS/Linux with a virtual environment: `.venv/bin/python main.py`
- On Windows with a virtual environment: `.venv\Scripts\python main.py`

## Testing Game Features

### Quick Test Scenarios

1. **Manual Mode**: Start in Manual Mode, reach an exit → see "YOU ESCAPED!" win screen
2. **AI Auto Mode**: Start in AI Auto Mode, let AI move player to exit → see "AI ESCAPED SUCCESSFULLY!" win screen
3. **Challenge Mode**: Start in Challenge Mode, lose to fire or timer → see Challenge-mode game over screen
4. **Menu Navigation**:
   - Start game → press Q → return to main menu
   - From win screen, press Q → return to main menu
   - From game over screen, press R → restart same mode
5. **AI Mode Toggle**: In Manual Mode, press SPACE to activate AI Auto Mode
6. **Path Visualization**: Press H to toggle the A\* path visibility on/off

## File Structure

```
Fire-Escape-Game/
├── main.py              # Main game loop and mode logic
├── game_board.py        # Board generation and fire spreading
├── player.py            # Player movement and position
├── astar.py             # A* pathfinding algorithm
├── config.py            # Constants and difficulty settings
├── README.md            # This file
```

## Key Algorithm: A\* Search

The game uses **A\* Search** to find the safest path to an exit.

**Formula**: $f(n) = g(n) + h(n)$

- **g(n)**: Actual cost from start to current cell
- **h(n)**: Manhattan distance to nearest exit (heuristic estimate)
- **f(n)**: Total estimated cost (guides search priorities)

**Why Manhattan Distance**: Movement is only in 4 directions (up/down/left/right), making Manhattan distance an efficient and admissible heuristic.

**Cell Costs**:

- Normal cell: 1
- Smoke cell: 4 (traversable but costly)
- Exit cell: 1
- Wall: blocked
- Fire: blocked

## Project Goal

This game is designed for an Artificial Intelligence Lab project.
It helps students understand grid maps, pathfinding, heuristics, and cost-based movement in a simple game environment.
