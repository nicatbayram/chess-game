﻿# Chess Game

A feature-rich chess game implemented in Python using Pygame. This implementation includes a graphical user interface, move animations, AI opponent, and various gameplay features.

## Features

- Full chess rules implementation
- Multiple game modes:
  - Player vs Player
  - Player vs Computer (AI)
  - Online Multiplayer (placeholder for future implementation)
- Interactive GUI with:
  - Piece drag-and-drop support
  - Move highlighting
  - Valid move indicators
  - Move history panel
  - Game state information
- Advanced features:
  - Move animations
  - Hint system
  - Undo moves (Ctrl+Z)
  - Dark/Light theme toggle
  - Tutorial mode
  - Sound effects for moves and captures
- AI opponent with adjustable difficulty using minimax algorithm and alpha-beta pruning

## Requirements

- Python 3.x
- Pygame

## Installation

1. Make sure you have Python installed on your system
2. Install Pygame:

```bash
pip install pygame
```

3. Clone or download this repository
4. Make sure you have the following directory structure:

```
your-project-folder/
├── main.py
├── pieces/
│   └── default/
│       ├── white_king.png
│       ├── white_queen.png
│       └── ... (other piece images)
└── sounds/
    ├── move.wav
    └── capture.wav
```

## Usage

Run the game:

```bash
python main.py
```

### Controls

- Mouse: Click and drag pieces to move them
- Ctrl+Z: Undo last move
- Ctrl+R: Restart game
- GUI buttons:
  - Hint: Shows suggested move
  - Move List: Toggles move history panel
  - Dark Mode: Toggles between light and dark themes

### Game Modes

1. **Play vs Computer**: Play against an AI opponent
2. **Two Players**: Local multiplayer mode
3. **Online Multiplayer**: (Future feature) Play against other players online

## Configuration

The game can be configured by modifying the `Settings` class:

```python
@dataclass
class Settings:
    theme: str = "light"           # "light" or "dark"
    ai_difficulty: int = 2         # minimax search depth
    online_enabled: bool = False   # placeholder for future online mode
    tutorial_mode: bool = False    # display tutorial overlay
    piece_set: str = "default"     # directory name for piece images
```

## Technical Details

### Key Components

1. `ChessGame`: Main game class handling:

   - Board state management
   - Move validation
   - Game rules
   - GUI rendering
   - Event handling
   - Animation system

2. `EnhancedChessAI`: AI opponent implementation:

   - Minimax algorithm with alpha-beta pruning
   - Configurable search depth
   - Position evaluation
   - Move generation

3. `Piece`: Data class representing chess pieces:
   - Type (King, Queen, Rook, etc.)
   - Color
   - Position
   - Movement history

### Architecture

- Object-oriented design with clear separation of concerns
- Event-driven architecture for user interactions
- Modular code structure for easy maintenance and extensions
- Efficient board representation using 2D arrays
- Flexible rendering system supporting animations and themes

## Contributing

Feel free to contribute to this project by:

1. Forking the repository
2. Creating a feature branch
3. Making your changes
4. Submitting a pull request

## Future Enhancements

- Implement online multiplayer functionality
- Add more sophisticated AI evaluation functions
- Implement opening book for AI
- Add game save/load functionality
- Support for custom themes and piece sets
- Add move notation in standard chess format
- Implement tournament mode

## ScreenShots
<img width="400" alt="1" src="https://github.com/user-attachments/assets/b011ae4b-af9d-4825-a552-efe001d9582e" />
<img width="400" alt="2" src="https://github.com/user-attachments/assets/b7410254-871f-46a2-82aa-ff5fa38a6e2e" />

