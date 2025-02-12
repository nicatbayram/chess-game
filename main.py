import pygame
import sys
import copy
import random
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# =============================================================================
# CONSTANTS & SETTINGS
# =============================================================================
BOARD_SIZE = 720
INFO_PANEL_HEIGHT = 200
MOVE_LIST_WIDTH = 200
WINDOW_WIDTH = BOARD_SIZE + MOVE_LIST_WIDTH  # extra panel for move list
WINDOW_HEIGHT = BOARD_SIZE + INFO_PANEL_HEIGHT
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE = int(SQUARE_SIZE * 0.85)

# Color definitions (feel free to tweak these for different themes or high contrast modes)
LIGHT_MODE_LIGHT = (238, 238, 210)
LIGHT_MODE_DARK  = (118, 150, 86)
DARK_MODE_LIGHT  = (180, 180, 180)
DARK_MODE_DARK   = (50, 50, 50)
DARK_MODE_BG     = (49, 46, 43)
HIGHLIGHT_COLOR  = (186, 202, 43, 128)
POSSIBLE_MOVE_COLOR = (119, 119, 119, 128)

# A simple settings data–structure; you could later add more options (e.g. voice control)
@dataclass
class Settings:
    theme: str = "light"           # "light" or "dark"
    ai_difficulty: int = 2         # minimax search depth
    online_enabled: bool = False   # placeholder for future online mode
    tutorial_mode: bool = False    # display tutorial overlay
    piece_set: str = "default"     # directory name for piece images

settings = Settings()

# =============================================================================
# PIECE TYPES & DATA STRUCTURES
# =============================================================================
class PieceType(Enum):
    KING   = "king"
    QUEEN  = "queen"
    ROOK   = "rook"
    BISHOP = "bishop"
    KNIGHT = "knight"
    PAWN   = "pawn"

@dataclass
class Piece:
    type: PieceType
    color: str
    position: Tuple[int, int]
    has_moved: bool = False

# =============================================================================
# THE CHESS GAME CLASS (WITH ANIMATION, HINT, TUTORIAL, & MOVE ANALYSIS)
# =============================================================================
class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Enhanced Chess Game")
        self.clock = pygame.time.Clock()
        self.images = self._load_images()
        self.move_sound = pygame.mixer.Sound("move.wav")
        self.capture_sound = pygame.mixer.Sound("capture.wav")
        self.init_game()
        self.ai_enabled = False
        self.hint_move = None
        self.animation = None       # animation data dict when a move is animated
        self.animating = False
        self.tutorial_mode = settings.tutorial_mode
        self.show_move_list = False
        self.dark_mode = (settings.theme == "dark")
        self.online_mode = settings.online_enabled

    def _load_images(self):
        images = {}
        # Images are assumed to be in a folder "pieces/<piece_set>/"
        for color in ["white", "black"]:
            for piece_type in PieceType:
                key = f"{color}_{piece_type.value}"
                path = f"pieces/{settings.piece_set}/{key}.png"
                img = pygame.image.load(path)
                images[key] = pygame.transform.scale(img, (PIECE_SIZE, PIECE_SIZE))
        return images

    def init_game(self):
        self.board = self._create_initial_board()
        self.selected_piece = None
        self.valid_moves = []
        self.turn = "white"
        self.move_history = []  # Each move is stored as (start, end, captured_piece)
        self.captured_pieces = {"white": [], "black": []}
        self.game_over = None

    def _create_initial_board(self):
        board = [[None for _ in range(8)] for _ in range(8)]
        for col in range(8):
            board[1][col] = Piece(PieceType.PAWN, "black", (1, col))
            board[6][col] = Piece(PieceType.PAWN, "white", (6, col))
        piece_order = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
            PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK
        ]
        for col in range(8):
            board[0][col] = Piece(piece_order[col], "black", (0, col))
            board[7][col] = Piece(piece_order[col], "white", (7, col))
        return board

    # A helper that makes a deep copy of the board, applies a move, and returns the new board.
    def _simulate_move_board(self, board, start: Tuple[int,int], end: Tuple[int,int]) -> List[List[Optional[Piece]]]:
        board_copy = copy.deepcopy(board)
        piece = board_copy[start[0]][start[1]]
        board_copy[end[0]][end[1]] = piece
        board_copy[start[0]][start[1]] = None
        if piece:
            piece.position = end
            piece.has_moved = True
        return board_copy

    # Returns valid moves for a given piece on the provided board.
    def get_valid_moves_piece_board(self, piece: Piece, board: List[List[Optional[Piece]]]) -> List[Tuple[int,int]]:
        moves = self._get_piece_moves(piece, board)
        valid_moves = []
        for move in moves:
            simulated_board = self._simulate_move_board(board, piece.position, move)
            if not self.in_check(simulated_board, piece.color):
                valid_moves.append(move)
        return valid_moves

    # Standard in–check test over a given board.
    def in_check(self, board: List[List[Optional[Piece]]], color: str) -> bool:
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.type == PieceType.KING and piece.color == color:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        if not king_pos:
            return True  # king is missing
        opponent = "black" if color == "white" else "white"
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == opponent:
                    moves = self._get_piece_moves(piece, board)
                    if king_pos in moves:
                        return True
        return False

    # Returns moves for a piece on a given board (or self.board if board not provided).
    def _get_piece_moves(self, piece: Piece, board: Optional[List[List[Optional[Piece]]]] = None) -> List[Tuple[int,int]]:
        if board is None:
            board = self.board
        moves = []
        row, col = piece.position

        if piece.type == PieceType.PAWN:
            direction = 1 if piece.color == "black" else -1
            new_row = row + direction
            if 0 <= new_row < 8 and board[new_row][col] is None:
                moves.append((new_row, col))
                if not piece.has_moved:
                    new_row2 = row + 2 * direction
                    if 0 <= new_row2 < 8 and board[new_row2][col] is None:
                        moves.append((new_row2, col))
            for dc in [-1, 1]:
                new_col = col + dc
                if 0 <= new_col < 8 and 0 <= row + direction < 8:
                    target = board[row + direction][new_col]
                    if target and target.color != piece.color:
                        moves.append((row + direction, new_col))

        elif piece.type == PieceType.KNIGHT:
            knight_moves = [
                (row + 2, col + 1), (row + 2, col - 1),
                (row - 2, col + 1), (row - 2, col - 1),
                (row + 1, col + 2), (row + 1, col - 2),
                (row - 1, col + 2), (row - 1, col - 2)
            ]
            for r, c in knight_moves:
                if 0 <= r < 8 and 0 <= c < 8:
                    target = board[r][c]
                    if target is None or target.color != piece.color:
                        moves.append((r, c))

        elif piece.type == PieceType.BISHOP:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] is None:
                        moves.append((r, c))
                    else:
                        if board[r][c].color != piece.color:
                            moves.append((r, c))
                        break
                    r += dr
                    c += dc

        elif piece.type == PieceType.ROOK:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] is None:
                        moves.append((r, c))
                    else:
                        if board[r][c].color != piece.color:
                            moves.append((r, c))
                        break
                    r += dr
                    c += dc

        elif piece.type == PieceType.QUEEN:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] is None:
                        moves.append((r, c))
                    else:
                        if board[r][c].color != piece.color:
                            moves.append((r, c))
                        break
                    r += dr
                    c += dc

        elif piece.type == PieceType.KING:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    r, c = row + dr, col + dc
                    if 0 <= r < 8 and 0 <= c < 8:
                        target = board[r][c]
                        if target is None or target.color != piece.color:
                            moves.append((r, c))
        return moves

    # Returns valid moves for a piece on the current board.
    def get_valid_moves(self, piece: Piece) -> List[Tuple[int,int]]:
        return self.get_valid_moves_piece_board(piece, self.board)

    # --------------------------------------------------------------------------
    # MOVE MAKING WITH ANIMATION (and eventual pawn promotion, history update, etc.)
    # --------------------------------------------------------------------------
    def make_move(self, start: Tuple[int,int], end: Tuple[int,int]):
        piece = self.board[start[0]][start[1]]
        target = self.board[end[0]][end[1]]
        if target:
            self.capture_sound.play()
            self.captured_pieces[self.turn].append(target)
        else:
            self.move_sound.play()
        # Set up animation data (positions in pixel coordinates)
        self.animation = {
            "piece": piece,
            "start": (start[0]*SQUARE_SIZE, start[1]*SQUARE_SIZE),
            "end": (end[0]*SQUARE_SIZE, end[1]*SQUARE_SIZE),
            "start_pos": start,
            "end_pos": end,
            "start_time": pygame.time.get_ticks(),
            "duration": 300  # milliseconds
        }
        self.animating = True
        self.pending_move = (start, end, target)
        # Remove the piece immediately so that the board redraw does not show it (it will be drawn via animation)
        self.board[start[0]][start[1]] = None

    # When the animation completes, update the board state.
    def finalize_move(self):
        start, end, target = self.pending_move
        piece = self.animation["piece"]
        piece.position = end
        piece.has_moved = True
        self.board[end[0]][end[1]] = piece
        # Pawn promotion (auto–promote to queen)
        if piece.type == PieceType.PAWN:
            if (piece.color == "white" and end[0] == 0) or (piece.color == "black" and end[0] == 7):
                piece.type = PieceType.QUEEN
        self.move_history.append((start, end, target))
        self.turn = "black" if self.turn == "white" else "white"
        self.pending_move = None
        self.animation = None
        self.animating = False
        self.check_game_over()

    def undo_move(self):
        if not self.move_history:
            return
        start, end, captured_piece = self.move_history.pop()
        piece = self.board[end[0]][end[1]]
        piece.position = start
        self.board[start[0]][start[1]] = piece
        self.board[end[0]][end[1]] = captured_piece
        if captured_piece:
            self.captured_pieces[self.turn].pop()
        self.turn = "black" if self.turn == "white" else "white"
        self.game_over = None

    # --------------------------------------------------------------------------
    # AI MOVE (for “Play vs Computer” mode)
    # --------------------------------------------------------------------------
    def ai_move(self):
        if not self.ai_enabled or self.turn != self.ai.color:
            return
        pygame.time.wait(500)
        best_move = self.ai.get_best_move()
        if best_move is not None:
            self.make_move(best_move[0], best_move[1])
        else:
            self.game_over = "Stalemate"

    # --------------------------------------------------------------------------
    # HINT SYSTEM
    # --------------------------------------------------------------------------
    def get_hint(self):
        # For a hint, we quickly create a temporary AI (using a shallow search) to suggest a move.
        temp_ai = EnhancedChessAI(self, self.turn, depth=2)
        self.hint_move = temp_ai.get_best_move()

    # --------------------------------------------------------------------------
    # GAME–OVER AND MOVE–ANALYSIS
    # --------------------------------------------------------------------------
    def check_game_over(self):
        if self.is_checkmate():
            self.game_over = "Checkmate"
        elif self.is_stalemate():
            self.game_over = "Stalemate"

    def is_checkmate(self):
        if not self.in_check(self.board, self.turn):
            return False
        return self.is_game_over()

    def is_stalemate(self):
        if self.in_check(self.board, self.turn):
            return False
        return self.is_game_over()

    def is_game_over(self):
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == self.turn:
                    if self.get_valid_moves(piece):
                        return False
        return True

    def draw_move_list(self):
        # Draw the move history in the extra panel on the right.
        panel_rect = pygame.Rect(BOARD_SIZE, 0, MOVE_LIST_WIDTH, BOARD_SIZE)
        panel_color = (200, 200, 200) if not self.dark_mode else (80, 80, 80)
        pygame.draw.rect(self.screen, panel_color, panel_rect)
        font = pygame.font.Font(None, 24)
        y_offset = 10
        for i, move in enumerate(self.move_history):
            start, end, _ = move
            # Convert board positions to algebraic notation
            move_str = f"{i+1}. {chr(97+start[1])}{8-start[0]} -> {chr(97+end[1])}{8-end[0]}"
            text = font.render(move_str, True, (0, 0, 0) if not self.dark_mode else (255, 255, 255))
            self.screen.blit(text, (BOARD_SIZE + 10, y_offset))
            y_offset += 30

    def draw_tutorial_overlay(self):
        # A semi-transparent overlay with tutorial instructions
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.Font(None, 36)
        tutorial_text = [
            "Tutorial Mode:",
            "1. Click and drag to move your pieces.",
            "2. Valid moves are highlighted.",
            "3. Click the Hint button for suggestions.",
            "4. Use Ctrl+Z to undo a move."
        ]
        y = 50
        for line in tutorial_text:
            text = font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (50, y))
            y += 40

    def draw_info_panel(self):
        # Draw the info panel (at the bottom of the window)
        panel_rect = pygame.Rect(0, BOARD_SIZE, BOARD_SIZE, INFO_PANEL_HEIGHT)
        panel_color = DARK_MODE_BG if self.dark_mode else (255, 255, 255)
        pygame.draw.rect(self.screen, panel_color, panel_rect)
        font = pygame.font.Font(None, 36)
        text_color = (255, 255, 255) if self.dark_mode else (0, 0, 0)
        # Turn indicator
        turn_text = font.render(f"{self.turn.capitalize()}'s Turn", True, text_color)
        self.screen.blit(turn_text, (20, BOARD_SIZE + 20))
        # Hint Button
        hint_btn = pygame.Rect(BOARD_SIZE - 160, BOARD_SIZE + 20, 140, 40)
        pygame.draw.rect(self.screen, (LIGHT_MODE_DARK if not self.dark_mode else DARK_MODE_DARK), hint_btn)
        hint_text = font.render("Hint", True, text_color)
        self.screen.blit(hint_text, (hint_btn.x + 30, hint_btn.y + 5))
        self.hint_button_rect = hint_btn
        # Toggle Move List Button
        ml_btn = pygame.Rect(BOARD_SIZE - 160, BOARD_SIZE + 70, 140, 40)
        pygame.draw.rect(self.screen, (LIGHT_MODE_DARK if not self.dark_mode else DARK_MODE_DARK), ml_btn)
        ml_text = font.render("Move List", True, text_color)
        self.screen.blit(ml_text, (ml_btn.x + 10, ml_btn.y + 5))
        self.move_list_button_rect = ml_btn
        # Dark/Light Mode Button
        mode_btn = pygame.Rect(BOARD_SIZE - 160, BOARD_SIZE + 120, 140, 40)
        pygame.draw.rect(self.screen, (LIGHT_MODE_DARK if not self.dark_mode else DARK_MODE_DARK), mode_btn)
        mode_text = font.render("Dark Mode" if not self.dark_mode else "Light Mode", True, text_color)
        self.screen.blit(mode_text, (mode_btn.x + 10, mode_btn.y + 5))
        self.dark_mode_button_rect = mode_btn

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.Font(None, 74)
        text = font.render("Game Over", True, (255, 255, 255))
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)
        result_font = pygame.font.Font(None, 48)
        result_text = result_font.render(self.game_over, True, (255, 255, 255))
        result_rect = result_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        self.screen.blit(result_text, result_rect)
        restart_btn = pygame.Rect(WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 + 60, 160, 40)
        pygame.draw.rect(self.screen, (0, 150, 0), restart_btn)
        btn_font = pygame.font.Font(None, 36)
        btn_text = btn_font.render("New Game", True, (255, 255, 255))
        self.screen.blit(btn_text, (restart_btn.x + 20, restart_btn.y + 10))
        self.restart_button_rect = restart_btn

    def draw(self):
        # First, update any active move animation.
        if self.animating and self.animation:
            current_time = pygame.time.get_ticks()
            progress = (current_time - self.animation["start_time"]) / self.animation["duration"]
            if progress >= 1.0:
                progress = 1.0
                self.finalize_move()
        # Clear background and draw the board.
        self.screen.fill(DARK_MODE_BG if self.dark_mode else (255, 255, 255))
        # Draw board squares and pieces.
        for row in range(8):
            for col in range(8):
                # Choose square color based on theme.
                if self.dark_mode:
                    light_color = DARK_MODE_LIGHT
                    dark_color = DARK_MODE_DARK
                else:
                    light_color = LIGHT_MODE_LIGHT
                    dark_color = LIGHT_MODE_DARK
                color = light_color if (row + col) % 2 == 0 else dark_color
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                # Draw piece if present and not being animated.
                piece = self.board[row][col]
                if piece:
                    if self.animating and self.animation and piece == self.animation["piece"]:
                        continue  # will be drawn in the animation step
                    key = f"{piece.color}_{piece.type.value}"
                    img = self.images.get(key)
                    if img:
                        rect = img.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                                    row * SQUARE_SIZE + SQUARE_SIZE // 2))
                        self.screen.blit(img, rect)
        # Draw animated piece if applicable.
        if self.animating and self.animation:
            piece = self.animation["piece"]
            key = f"{piece.color}_{piece.type.value}"
            img = self.images.get(key)
            if img:
                start_px = self.animation["start"]
                end_px = self.animation["end"]
                current_time = pygame.time.get_ticks()
                progress = (current_time - self.animation["start_time"]) / self.animation["duration"]
                if progress > 1:
                    progress = 1
                # Interpolate between start and end (note: positions are stored as (row_px, col_px))
                current_x = start_px[1] + (end_px[1] - start_px[1]) * progress
                current_y = start_px[0] + (end_px[0] - start_px[0]) * progress
                rect = img.get_rect(center=(current_x + SQUARE_SIZE // 2, current_y + SQUARE_SIZE // 2))
                self.screen.blit(img, rect)
        # Highlight selected piece and valid moves.
        if self.selected_piece:
            row, col = self.selected_piece.position
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            self.screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            for move in self.valid_moves:
                move_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(move_surface, POSSIBLE_MOVE_COLOR, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 4)
                self.screen.blit(move_surface, (move[1] * SQUARE_SIZE, move[0] * SQUARE_SIZE))
        # If a hint is active, highlight the suggested move.
        if self.hint_move:
            start, end = self.hint_move
            hint_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            hint_surface.fill((0, 0, 255, 100))  # semi-transparent blue
            self.screen.blit(hint_surface, (start[1] * SQUARE_SIZE, start[0] * SQUARE_SIZE))
        # Draw info panel at the bottom.
        self.draw_info_panel()
        # Draw move list panel on the right.
        if self.show_move_list:
            self.draw_move_list()
        # Draw game over overlay if needed.
        if self.game_over:
            self.draw_game_over()
        # Draw tutorial overlay if enabled.
        if self.tutorial_mode:
            self.draw_tutorial_overlay()

    # Main game loop.
    def run(self):
        dragging = False
        drag_piece = None
        drag_offset = (0, 0)
        while True:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        if self.restart_button_rect.collidepoint(mouse_pos):
                            self.init_game()
                            self.game_over = None
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        if mouse_pos[1] < BOARD_SIZE and not self.animating:
                            row = mouse_pos[1] // SQUARE_SIZE
                            col = mouse_pos[0] // SQUARE_SIZE
                            piece = self.board[row][col]
                            if piece and piece.color == self.turn:
                                self.selected_piece = piece
                                self.valid_moves = self.get_valid_moves(piece)
                                dragging = True
                                drag_piece = piece
                                drag_offset = (mouse_pos[0] - col * SQUARE_SIZE, mouse_pos[1] - row * SQUARE_SIZE)
                        else:
                            # Check for clicks on info panel buttons.
                            if self.hint_button_rect.collidepoint(mouse_pos):
                                self.get_hint()
                            elif self.dark_mode_button_rect.collidepoint(mouse_pos):
                                self.dark_mode = not self.dark_mode
                            elif self.move_list_button_rect.collidepoint(mouse_pos):
                                self.show_move_list = not self.show_move_list
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1 and dragging and not self.animating:
                            mouse_pos = event.pos
                            end_row = mouse_pos[1] // SQUARE_SIZE
                            end_col = mouse_pos[0] // SQUARE_SIZE
                            if 0 <= end_row < 8 and 0 <= end_col < 8:
                                start_pos = drag_piece.position
                                end_pos = (end_row, end_col)
                                if end_pos in self.get_valid_moves(drag_piece):
                                    self.make_move(start_pos, end_pos)
                            dragging = False
                            drag_piece = None
                            self.selected_piece = None
                            self.valid_moves = []
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            self.undo_move()
                        elif event.key == pygame.K_r and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            self.init_game()
            # If playing vs. AI and it is AI’s turn (and no animation is in progress), let it move.
            if not self.game_over and self.ai_enabled and self.turn == self.ai.color and not self.animating:
                self.ai_move()
            self.draw()
            # If dragging a piece, draw it following the mouse.
            if dragging and drag_piece and not self.animating:
                mouse_pos = pygame.mouse.get_pos()
                key = f"{drag_piece.color}_{drag_piece.type.value}"
                img = self.images.get(key)
                if img:
                    rect = img.get_rect(center=(mouse_pos[0], mouse_pos[1]))
                    self.screen.blit(img, rect)
            pygame.display.flip()

# =============================================================================
# ENHANCED AI WITH MINIMAX & ALPHA-BETA PRUNING
# =============================================================================
# (This AI class reuses many of the same board–scanning routines so that
# it can “think” several moves ahead. Its difficulty is adjustable via search depth.)
class EnhancedChessAI:
    def __init__(self, game: ChessGame, color: str = "black", depth: int = 2):
        self.game = game
        self.color = color
        self.depth = depth
        self.piece_values = {
            PieceType.PAWN: 1,
            PieceType.KNIGHT: 3,
            PieceType.BISHOP: 3,
            PieceType.ROOK: 5,
            PieceType.QUEEN: 9,
            PieceType.KING: 100
        }

    def opponent_color(self) -> str:
        return "white" if self.color == "black" else "black"

    def evaluate_board_board(self, board: List[List[Optional[Piece]]]) -> int:
        score = 0
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    value = self.piece_values[piece.type]
                    if piece.color == self.color:
                        score += value
                    else:
                        score -= value
        return score

    def get_all_moves_board(self, board: List[List[Optional[Piece]]], color: str) -> List[Tuple[Tuple[int,int], Tuple[int,int]]]:
        moves = []
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == color:
                    valid_moves = self.game.get_valid_moves_piece_board(piece, board)
                    for move in valid_moves:
                        moves.append((piece.position, move))
        return moves

    def minimax(self, board: List[List[Optional[Piece]]], depth: int, alpha: float, beta: float, maximizing: bool) -> int:
        # Terminal condition: depth == 0 or game over on either side.
        if depth == 0 or self.game.is_game_over_board(board, self.color) or self.game.is_game_over_board(board, self.opponent_color()):
            return self.evaluate_board_board(board)
        if maximizing:
            max_eval = -float('inf')
            moves = self.get_all_moves_board(board, self.color)
            for move in moves:
                new_board = self.game._simulate_move_board(board, move[0], move[1])
                eval = self.minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            moves = self.get_all_moves_board(board, self.opponent_color())
            for move in moves:
                new_board = self.game._simulate_move_board(board, move[0], move[1])
                eval = self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self) -> Optional[Tuple[Tuple[int,int], Tuple[int,int]]]:
        best_move = None
        max_eval = -float('inf')
        moves = self.get_all_moves_board(self.game.board, self.color)
        for move in moves:
            new_board = self.game._simulate_move_board(self.game.board, move[0], move[1])
            eval = self.minimax(new_board, self.depth - 1, -float('inf'), float('inf'), False)
            if eval > max_eval:
                max_eval = eval
                best_move = move
        return best_move

# =============================================================================
# ADDITIONAL HELPER: Check if a given board state is “game over” for a color.
# (We add this as a method on ChessGame for use in the AI search.)
def is_game_over_board(self, board: List[List[Optional[Piece]]], color: str) -> bool:
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.color == color:
                if self.get_valid_moves_piece_board(piece, board):
                    return False
    return True

ChessGame.is_game_over_board = is_game_over_board

# =============================================================================
# START MENU (WITH OPTIONS FOR AI, TWO PLAYERS, AND ONLINE – THE LAST IS A PLACEHOLDER)
# =============================================================================
def show_start_menu() -> str:
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    game_mode = None
    while game_mode is None:
        screen.fill(DARK_MODE_BG)
        title_font = pygame.font.Font(None, 74)
        title = title_font.render("Enhanced Chess Game", True, (255, 255, 255))
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))
        button_font = pygame.font.Font(None, 36)
        # Play vs. AI button.
        ai_btn = pygame.Rect(WINDOW_WIDTH // 2 - 150, 300, 300, 50)
        pygame.draw.rect(screen, LIGHT_MODE_DARK, ai_btn)
        ai_text = button_font.render("Play vs Computer", True, LIGHT_MODE_LIGHT)
        screen.blit(ai_text, (ai_btn.x + 50, ai_btn.y + 15))
        # Two Players button.
        two_players_btn = pygame.Rect(WINDOW_WIDTH // 2 - 150, 400, 300, 50)
        pygame.draw.rect(screen, LIGHT_MODE_DARK, two_players_btn)
        two_players_text = button_font.render("Two Players", True, LIGHT_MODE_LIGHT)
        screen.blit(two_players_text, (two_players_btn.x + 70, two_players_btn.y + 15))
        # Online Multiplayer button (stub).
        online_btn = pygame.Rect(WINDOW_WIDTH // 2 - 150, 500, 300, 50)
        pygame.draw.rect(screen, LIGHT_MODE_DARK, online_btn)
        online_text = button_font.render("Online Multiplayer", True, LIGHT_MODE_LIGHT)
        screen.blit(online_text, (online_btn.x + 30, online_btn.y + 15))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if ai_btn.collidepoint(mouse_pos):
                    game_mode = "ai"
                elif two_players_btn.collidepoint(mouse_pos):
                    game_mode = "two_players"
                elif online_btn.collidepoint(mouse_pos):
                    game_mode = "online"
        pygame.display.flip()
        clock.tick(60)
    return game_mode

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    mode = show_start_menu()
    game = ChessGame()
    if mode == "ai":
        game.ai_enabled = True
        game.ai = EnhancedChessAI(game, "black", depth=settings.ai_difficulty)
    elif mode == "online":
        # Placeholder: In a full implementation, you would add network code here.
        game.online_mode = True
        print("Online Multiplayer mode is under development.")
    game.run()
