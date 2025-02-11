import pygame
import sys
import copy
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
BOARD_SIZE = 720
INFO_PANEL_HEIGHT = 200
WINDOW_WIDTH = BOARD_SIZE
WINDOW_HEIGHT = BOARD_SIZE + INFO_PANEL_HEIGHT
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE = int(SQUARE_SIZE * 0.85)

# Colors
LIGHT_MODE_LIGHT = (238, 238, 210)
LIGHT_MODE_DARK = (118, 150, 86)
DARK_MODE_LIGHT = (180, 180, 180)
DARK_MODE_DARK = (50, 50, 50)
DARK_MODE_BG = (49, 46, 43)
HIGHLIGHT_COLOR = (186, 202, 43, 128)
POSSIBLE_MOVE_COLOR = (119, 119, 119, 128)

class PieceType(Enum):
    KING = "king"
    QUEEN = "queen"
    ROOK = "rook"
    BISHOP = "bishop"
    KNIGHT = "knight"
    PAWN = "pawn"

@dataclass
class Piece:
    type: PieceType
    color: str
    position: Tuple[int, int]
    has_moved: bool = False

class ChessAI:
    def __init__(self, game, color="black"):
        self.game = game
        self.color = color
        self.piece_values = {
            PieceType.PAWN: 1,
            PieceType.KNIGHT: 3,
            PieceType.BISHOP: 3,
            PieceType.ROOK: 5,
            PieceType.QUEEN: 9,
            PieceType.KING: 100
        }
        
    def evaluate_board(self):
        score = 0
        for row in range(8):
            for col in range(8):
                piece = self.game.board[row][col]
                if piece:
                    value = self.piece_values[piece.type]
                    if piece.color == self.color:
                        score += value
                    else:
                        score -= value
        return score
    
    def get_all_moves(self):
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.game.board[row][col]
                if piece and piece.color == self.color:
                    valid_moves = self.game.get_valid_moves(piece)
                    for move in valid_moves:
                        moves.append((piece.position, move))
        return moves
    
    def evaluate_move(self, start, end):
        score = 0
        target = self.game.board[end[0]][end[1]]
        if target:
            score += self.piece_values[target.type] * 10
            
        center_dist = abs(3.5 - end[0]) + abs(3.5 - end[1])
        score += (7 - center_dist) / 2
        
        piece = self.game.board[start[0]][start[1]]
        if piece and self.is_under_attack(start):
            score += self.piece_values[piece.type]
                
        return score
    
    def is_under_attack(self, pos):
        opponent_color = "white" if self.color == "black" else "black"
        for row in range(8):
            for col in range(8):
                piece = self.game.board[row][col]
                if piece and piece.color == opponent_color:
                    moves = self.game.get_valid_moves(piece)
                    if pos in moves:
                        return True
        return False
    
    def get_best_move(self):
        moves = self.get_all_moves()
        if not moves:
            return None
        
        rated_moves = []
        for start, end in moves:
            score = self.evaluate_move(start, end)
            rated_moves.append((start, end, score))
        
        rated_moves.sort(key=lambda x: x[2], reverse=True)
        best_moves = rated_moves[:3]
        chosen_move = random.choice(best_moves)
        return chosen_move[0], chosen_move[1]

class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chess Game")
        
        self.images = self._load_images()
        self.move_sound = pygame.mixer.Sound("move.wav")
        self.capture_sound = pygame.mixer.Sound("capture.wav")
        
        self.ai_enabled = False
        self.ai_thinking = False
        self.game_over = None
        
        self.init_game()

    def init_game(self):
        self.board = self._create_initial_board()
        self.selected_piece = None
        self.valid_moves = []
        self.turn = "white"
        self.move_history = []
        self.captured_pieces = {"white": [], "black": []}
        self.dark_mode = False

    def init_ai(self, ai_color="black"):
        self.ai = ChessAI(self, ai_color)
        self.ai_enabled = True

    def _load_images(self):
        images = {}
        for color in ["white", "black"]:
            for piece_type in PieceType:
                key = f"{color}_{piece_type.value}"
                path = f"pieces/{key}.png"
                img = pygame.image.load(path)
                images[key] = pygame.transform.scale(img, (PIECE_SIZE, PIECE_SIZE))
        return images

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

    def _simulate_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[List[Optional[Piece]]]:
        board_copy = copy.deepcopy(self.board)
        piece = board_copy[start[0]][start[1]]
        board_copy[end[0]][end[1]] = piece
        board_copy[start[0]][start[1]] = None
        if piece:
            piece.position = end
            piece.has_moved = True
        return board_copy

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
            return True
        
        opponent = "black" if color == "white" else "white"
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == opponent:
                    moves = self._get_piece_moves(piece, board)
                    if king_pos in moves:
                        return True
        return False

    def _get_piece_moves(self, piece: Piece, board: Optional[List[List[Optional[Piece]]]] = None) -> List[Tuple[int, int]]:
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

    def get_valid_moves(self, piece: Piece) -> List[Tuple[int, int]]:
        moves = self._get_piece_moves(piece)
        valid_moves = []
        for move in moves:
            simulated_board = self._simulate_move(piece.position, move)
            if not self.in_check(simulated_board, piece.color):
                valid_moves.append(move)
        return valid_moves

    def is_valid_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        piece = self.board[start[0]][start[1]]
        if not piece or piece.color != self.turn:
            return False
        return end in self.get_valid_moves(piece)

    def make_move(self, start: Tuple[int, int], end: Tuple[int, int]):
        piece = self.board[start[0]][start[1]]
        target = self.board[end[0]][end[1]]
        
        if target:
            self.capture_sound.play()
            self.captured_pieces[self.turn].append(target)
        else:
            self.move_sound.play()
        
        piece.position = end
        piece.has_moved = True
        self.board[end[0]][end[1]] = piece
        self.board[start[0]][start[1]] = None

        if piece.type == PieceType.PAWN:
            if (piece.color == "white" and end[0] == 0) or (piece.color == "black" and end[0] == 7):
                piece.type = PieceType.QUEEN

        self.move_history.append((start, end, target))
        self.turn = "black" if self.turn == "white" else "white"
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

    def ai_move(self):
        if not self.ai_enabled or self.turn != self.ai.color:
            return
        pygame.time.wait(500)
        best_move = self.ai.get_best_move()
        if best_move is not None:
            start, end = best_move
            self.make_move(start, end)
            self.check_game_over()

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

    def draw(self):
        # Arka planı çiz (tahta ve info panel için)
        self.screen.fill(DARK_MODE_BG if self.dark_mode else (255, 255, 255))
        
        # Tahtayı (board) üst kısımda çiz (0,0 - BOARD_SIZE)
        for row in range(8):
            for col in range(8):
                if self.dark_mode:
                    light_color = DARK_MODE_LIGHT
                    dark_color = DARK_MODE_DARK
                else:
                    light_color = LIGHT_MODE_LIGHT
                    dark_color = LIGHT_MODE_DARK
                
                color = light_color if (row + col) % 2 == 0 else dark_color
                pygame.draw.rect(
                    self.screen,
                    color,
                    (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                )
                
                piece = self.board[row][col]
                if piece:
                    key = f"{piece.color}_{piece.type.value}"
                    img = self.images.get(key)
                    if img:
                        rect = img.get_rect()
                        rect.center = (col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                       row * SQUARE_SIZE + SQUARE_SIZE // 2)
                        self.screen.blit(img, rect)
        
        # Seçili taş ve geçerli hamleleri vurgula
        if self.selected_piece:
            row, col = self.selected_piece.position
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            self.screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            
            for move_row, move_col in self.valid_moves:
                move_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(
                    move_surface,
                    POSSIBLE_MOVE_COLOR,
                    (SQUARE_SIZE // 2, SQUARE_SIZE // 2),
                    SQUARE_SIZE // 4
                )
                self.screen.blit(move_surface, (move_col * SQUARE_SIZE, move_row * SQUARE_SIZE))

        # Bilgi panelini (info panel) altta çiz (y: BOARD_SIZE -> BOARD_SIZE+INFO_PANEL_HEIGHT)
        self.draw_info_panel()

        if self.game_over:
            self.draw_game_over()

    def draw_info_panel(self):
        panel_rect = pygame.Rect(0, BOARD_SIZE, WINDOW_WIDTH, INFO_PANEL_HEIGHT)
        panel_color = DARK_MODE_BG if self.dark_mode else (255, 255, 255)
        pygame.draw.rect(self.screen, panel_color, panel_rect)
        
        font = pygame.font.Font(None, 36)
        text_color = (255, 255, 255) if self.dark_mode else (0, 0, 0)
        
        # Sıra bilgisi (sol üstte)
        turn_text = font.render(f"{self.turn.capitalize()}'s Turn", True, text_color)
        self.screen.blit(turn_text, (20, BOARD_SIZE + 20))
        
        # White Captured taşlar (sol alt)
        white_title = font.render("White Captured:", True, text_color)
        self.screen.blit(white_title, (20, BOARD_SIZE + 60))
        y = BOARD_SIZE + 100
        for i, piece in enumerate(self.captured_pieces["white"]):
            key = f"{piece.color}_{piece.type.value}"
            img = self.images.get(key)
            if img:
                img_scaled = pygame.transform.scale(img, (40, 40))
                self.screen.blit(img_scaled, (20 + (i % 2) * 45, y + (i // 2) * 45))
        
        # Black Captured taşlar (orta)
        black_title = font.render("Black Captured:", True, text_color)
        self.screen.blit(black_title, (300, BOARD_SIZE + 60))
        y = BOARD_SIZE + 100
        for i, piece in enumerate(self.captured_pieces["black"]):
            key = f"{piece.color}_{piece.type.value}"
            img = self.images.get(key)
            if img:
                img_scaled = pygame.transform.scale(img, (40, 40))
                self.screen.blit(img_scaled, (300 + (i % 2) * 45, y + (i // 2) * 45))
        
        # Dark Mode / Light Mode düğmesi (sağ alt)
        button_rect = pygame.Rect(WINDOW_WIDTH - 180, BOARD_SIZE + INFO_PANEL_HEIGHT - 60, 160, 40)
        pygame.draw.rect(self.screen, DARK_MODE_DARK if self.dark_mode else LIGHT_MODE_DARK, button_rect)
        btn_text = font.render("Dark Mode" if not self.dark_mode else "Light Mode", True, text_color)
        self.screen.blit(btn_text, (button_rect.x + 10, button_rect.y + 10))
        self.dark_mode_button_rect = button_rect  # Event kontrolü için sakla

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

    def run(self):
        dragging = False
        drag_piece = None
        drag_pos = (0, 0)
        clock = pygame.time.Clock()

        while True:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        # Yeni Oyun düğmesi kontrolü (Game Over ekranında)
                        if (WINDOW_WIDTH // 2 - 80 <= mouse_pos[0] <= WINDOW_WIDTH // 2 + 80 and
                            WINDOW_HEIGHT // 2 + 60 <= mouse_pos[1] <= WINDOW_HEIGHT // 2 + 100):
                            self.init_game()
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            mouse_pos = event.pos
                            # Eğer tıklama tahtada ise
                            if mouse_pos[1] < BOARD_SIZE:
                                row = mouse_pos[1] // SQUARE_SIZE
                                col = mouse_pos[0] // SQUARE_SIZE
                                if 0 <= row < 8 and 0 <= col < 8:
                                    piece = self.board[row][col]
                                    if piece and piece.color == self.turn and (not self.ai_enabled or self.turn != self.ai.color):
                                        self.selected_piece = piece
                                        self.valid_moves = self.get_valid_moves(piece)
                                        dragging = True
                                        drag_piece = piece
                                        drag_pos = mouse_pos
                            else:
                                # Info panelde dark mode/light mode düğmesine tıklama kontrolü
                                if self.dark_mode_button_rect.collidepoint(mouse_pos):
                                    self.dark_mode = not self.dark_mode

                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1 and dragging:
                            mouse_pos = event.pos
                            end_row = mouse_pos[1] // SQUARE_SIZE
                            end_col = mouse_pos[0] // SQUARE_SIZE
                            if 0 <= end_row < 8 and 0 <= end_col < 8:
                                start_pos = drag_piece.position
                                end_pos = (end_row, end_col)
                                if self.is_valid_move(start_pos, end_pos):
                                    self.make_move(start_pos, end_pos)
                            dragging = False
                            drag_piece = None
                            self.selected_piece = None
                            self.valid_moves = []

                    elif event.type == pygame.MOUSEMOTION and dragging:
                        drag_pos = event.pos

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            self.undo_move()
                        elif event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            self.init_game()

            if not self.game_over and self.ai_enabled and self.turn == self.ai.color:
                self.ai_move()

            self.draw()

            if dragging and drag_piece:
                key = f"{drag_piece.color}_{drag_piece.type.value}"
                img = self.images.get(key)
                if img:
                    rect = img.get_rect()
                    rect.center = drag_pos
                    self.screen.blit(img, rect)

            pygame.display.flip()

def show_start_menu():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    game_mode = None

    while game_mode is None:
        screen.fill(DARK_MODE_BG)
        title_font = pygame.font.Font(None, 74)
        title = title_font.render("Chess Game", True, (255, 255, 255))
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))

        button_font = pygame.font.Font(None, 36)
        # Play vs AI Button
        ai_btn = pygame.Rect(WINDOW_WIDTH//2 - 150, 300, 300, 50)
        pygame.draw.rect(screen, LIGHT_MODE_DARK, ai_btn)
        ai_text = button_font.render("Play vs Computer", True, LIGHT_MODE_LIGHT)
        screen.blit(ai_text, (ai_btn.x + 50, ai_btn.y + 15))

        # Two Players Button
        two_players_btn = pygame.Rect(WINDOW_WIDTH//2 - 150, 400, 300, 50)
        pygame.draw.rect(screen, LIGHT_MODE_DARK, two_players_btn)
        two_players_text = button_font.render("Two Players", True, LIGHT_MODE_LIGHT)
        screen.blit(two_players_text, (two_players_btn.x + 70, two_players_btn.y + 15))

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

        pygame.display.flip()
        clock.tick(60)
    
    return game_mode

if __name__ == "__main__":
    game_mode = show_start_menu()
    game = ChessGame()
    if game_mode == "ai":
        game.init_ai()
    game.run()
