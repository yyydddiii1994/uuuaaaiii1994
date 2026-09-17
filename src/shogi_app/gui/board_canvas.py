"""
Tkinter Canvas widget for drawing Shogi board, pieces, selection highlights, and target highlights.
"""

import tkinter as tk
import shogi

# Japanese Kanji representation for piece types
PIECE_KANJI = {
    shogi.PAWN: "歩",
    shogi.LANCE: "香",
    shogi.KNIGHT: "桂",
    shogi.SILVER: "銀",
    shogi.GOLD: "金",
    shogi.BISHOP: "角",
    shogi.ROOK: "飛",
    shogi.KING: "玉",
    shogi.PROM_PAWN: "と",
    shogi.PROM_LANCE: "成香",
    shogi.PROM_KNIGHT: "成桂",
    shogi.PROM_SILVER: "成銀",
    shogi.PROM_BISHOP: "馬",
    shogi.PROM_ROOK: "龍",
}

class BoardCanvas(tk.Canvas):
    def __init__(self, parent, size=450, on_square_click=None, **kwargs):
        super().__init__(parent, width=size, height=size, bg="#E2AE63", highlightthickness=1, highlightbackground="#8B5A2B", **kwargs)
        self.size = size
        self.cell_size = size / 9.0
        self.on_square_click = on_square_click

        self.selected_square = None
        self.legal_targets = []
        self.last_move_squares = []
        self.is_flipped = False # False: Black bottom, True: White bottom

        self.bind("<Button-1>", self._handle_click)

    def set_flipped(self, flipped: bool):
        self.is_flipped = flipped
        self.redraw()

    def set_selected_square(self, square, legal_targets=None):
        self.selected_square = square
        self.legal_targets = legal_targets or []
        self.redraw()

    def set_last_move(self, from_sq, to_sq):
        self.last_move_squares = [sq for sq in (from_sq, to_sq) if sq is not None]
        self.redraw()

    def square_to_rect(self, square: int):
        """Converts 0..80 square index to (x1, y1, x2, y2) canvas coordinates."""
        rank = shogi.rank_index(square) # 0..8 (a..i, top to bottom)
        file = shogi.file_index(square) # 0..8 (9..1, left to right)

        if self.is_flipped:
            col = 8 - file
            row = 8 - rank
        else:
            col = file
            row = rank

        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        return x1, y1, x2, y2

    def coords_to_square(self, x: float, y: float) -> int:
        col = int(x // self.cell_size)
        row = int(y // self.cell_size)

        if not (0 <= col < 9 and 0 <= row < 9):
            return None

        if self.is_flipped:
            file = 8 - col
            rank = 8 - row
        else:
            file = col
            rank = row

        return rank * 9 + file

    def _handle_click(self, event):
        square = self.coords_to_square(event.x, event.y)
        if square is not None and self.on_square_click:
            self.on_square_click(square)

    def redraw(self, board: shogi.Board = None):
        if board is not None:
            self._board_state = board
        elif hasattr(self, '_board_state'):
            board = self._board_state
        else:
            return

        self.delete("all")

        # 1. Draw grid lines
        for i in range(10):
            pos = i * self.cell_size
            self.create_line(pos, 0, pos, self.size, fill="#5C3A21", width=1.5 if i in (0, 9) else 1)
            self.create_line(0, pos, self.size, pos, fill="#5C3A21", width=1.5 if i in (0, 9) else 1)

        # 2. Draw star dots (星) at (3,3), (3,6), (6,3), (6,6)
        star_points = [(3, 3), (3, 6), (6, 3), (6, 6)]
        r = 3.0
        for f, r_idx in star_points:
            col = (8 - f) if self.is_flipped else f
            row = (8 - r_idx) if self.is_flipped else r_idx
            cx = col * self.cell_size
            cy = row * self.cell_size
            self.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#5C3A21", outline="#5C3A21")

        # 3. Draw last move highlights
        for sq in self.last_move_squares:
            x1, y1, x2, y2 = self.square_to_rect(sq)
            self.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, fill="#F3E5AB", outline="", stipple="gray50")

        # 4. Draw selection highlight
        if self.selected_square is not None:
            x1, y1, x2, y2 = self.square_to_rect(self.selected_square)
            self.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2, fill="#76C7C0", outline="#207567", width=2)

        # 5. Draw legal target highlights
        for sq in self.legal_targets:
            x1, y1, x2, y2 = self.square_to_rect(sq)
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            if board.piece_at(sq) is not None:
                self.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2, outline="#FF6B6B", width=3)
            else:
                self.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill="#2ECC71", outline="")

        # 6. Draw pieces
        font_size = int(self.cell_size * 0.45)
        for sq in range(81):
            piece = board.piece_at(sq)
            if piece is None:
                continue

            x1, y1, x2, y2 = self.square_to_rect(sq)
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0

            kanji = PIECE_KANJI.get(piece.piece_type, "?")

            # Determine color & orientation
            # Black (先手) pieces point up if not flipped; White (後手) point down
            is_white = (piece.color == shogi.WHITE)
            text_color = "#900C3F" if piece.piece_type in (shogi.PROM_PAWN, shogi.PROM_LANCE, shogi.PROM_KNIGHT, shogi.PROM_SILVER, shogi.PROM_BISHOP, shogi.PROM_ROOK) else "#111111"

            # Draw pentagonal piece shape background
            pw, ph = self.cell_size * 0.38, self.cell_size * 0.42

            # Flip piece direction if White or canvas is flipped
            upside_down = (is_white != self.is_flipped)

            if upside_down:
                poly = [
                    cx, cy + ph,
                    cx - pw, cy + ph * 0.5,
                    cx - pw * 0.8, cy - ph,
                    cx + pw * 0.8, cy - ph,
                    cx + pw, cy + ph * 0.5
                ]
            else:
                poly = [
                    cx, cy - ph,
                    cx - pw, cy - ph * 0.5,
                    cx - pw * 0.8, cy + ph,
                    cx + pw * 0.8, cy + ph,
                    cx + pw, cy - ph * 0.5
                ]

            self.create_polygon(poly, fill="#FCEBB6", outline="#8B5A2B", width=1.5)
            self.create_text(cx, cy, text=kanji, font=("Hiragino Sans", font_size, "bold"), fill=text_color)
