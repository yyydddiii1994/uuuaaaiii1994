"""
Main GUI window for Shogi application.
Handles board rendering, player interactions, piece drops/promotions, controls, Kifu log, and threaded AI moves.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
import shogi

from src.shogi_app.gui.board_canvas import BoardCanvas, PIECE_KANJI
from src.shogi_app.engine.search import SearchEngine

FILE_KANJI = ["９", "８", "７", "６", "５", "４", "３", "２", "１"]
RANK_KANJI = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]

def move_to_japanese(board: shogi.Board, move: shogi.Move, last_to_square=None) -> str:
    """Formats a Move into Japanese notation (e.g., ▲７六歩, △３四歩, ▲同　飛)."""
    color_prefix = "▲" if board.turn == shogi.BLACK else "△"

    if move.from_square is None:
        # Drop
        to_f = shogi.file_index(move.to_square)
        to_r = shogi.rank_index(move.to_square)
        to_str = f"{FILE_KANJI[to_f]}{RANK_KANJI[to_r]}"
        piece_str = PIECE_KANJI.get(move.drop_piece_type, "")
        return f"{color_prefix}{to_str}{piece_str}打"

    # Board move
    to_f = shogi.file_index(move.to_square)
    to_r = shogi.rank_index(move.to_square)
    if last_to_square is not None and move.to_square == last_to_square:
        to_str = "同　"
    else:
        to_str = f"{FILE_KANJI[to_f]}{RANK_KANJI[to_r]}"

    moving_piece = board.piece_at(move.from_square)
    piece_str = PIECE_KANJI.get(moving_piece.piece_type, "") if moving_piece else ""

    pro_str = "成" if move.promotion else ""
    return f"{color_prefix}{to_str}{piece_str}{pro_str}"

class ShogiMainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python 将棋対局ソフト")
        self.geometry("820x580")
        self.resizable(False, False)

        self.board = shogi.Board()
        self.search_engine = SearchEngine(depth=3, max_time=3.0)

        # Game settings
        self.player_color = shogi.BLACK # Player is Sente by default
        self.ai_color = shogi.WHITE
        self.ai_thinking = False
        self.difficulty_levels = {
            "初級 (Depth 1)": (1, 1.0),
            "中級 (Depth 3)": (3, 3.0),
            "上級 (Depth 5)": (5, 5.0)
        }

        # Interaction state
        self.selected_square = None
        self.selected_hand_piece = None # (color, piece_type)
        self.legal_targets = []
        self.last_move = None
        self.kifu_history = [] # list of (move_str, board_sfen)

        self._build_ui()
        self.reset_game()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel: Hands and Board Canvas
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, padx=10, pady=5)

        # Gote Hand Frame (Top)
        self.gote_hand_frame = ttk.LabelFrame(left_frame, text="△ 後手の持ち駒", padding=5)
        self.gote_hand_frame.pack(fill=tk.X, pady=(0, 5))
        self.gote_hand_canvas = tk.Canvas(self.gote_hand_frame, height=40, bg="#F0E68C", highlightthickness=0)
        self.gote_hand_canvas.pack(fill=tk.X)
        self.gote_hand_canvas.bind("<Button-1>", lambda e: self._on_hand_click(e, shogi.WHITE))

        # Board Canvas
        self.board_canvas = BoardCanvas(left_frame, size=450, on_square_click=self._on_square_click)
        self.board_canvas.pack()

        # Sente Hand Frame (Bottom)
        self.sente_hand_frame = ttk.LabelFrame(left_frame, text="▲ 先手の持ち駒", padding=5)
        self.sente_hand_frame.pack(fill=tk.X, pady=(5, 0))
        self.sente_hand_canvas = tk.Canvas(self.sente_hand_frame, height=40, bg="#F0E68C", highlightthickness=0)
        self.sente_hand_canvas.pack(fill=tk.X)
        self.sente_hand_canvas.bind("<Button-1>", lambda e: self._on_hand_click(e, shogi.BLACK))

        # Right panel: Controls, Status, Kifu
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Game Control Group
        ctrl_group = ttk.LabelFrame(right_frame, text="対局設定・操作", padding=10)
        ctrl_group.pack(fill=tk.X, pady=(0, 10))

        # Side selection
        side_frame = ttk.Frame(ctrl_group)
        side_frame.pack(fill=tk.X, pady=2)
        ttk.Label(side_frame, text="プレイヤー:").pack(side=tk.LEFT)
        self.side_var = tk.StringVar(value="Sente")
        ttk.Radiobutton(side_frame, text="先手 (▲)", variable=self.side_var, value="Sente", command=self._on_side_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(side_frame, text="後手 (△)", variable=self.side_var, value="Gote", command=self._on_side_change).pack(side=tk.LEFT, padx=5)

        # AI Difficulty selection
        diff_frame = ttk.Frame(ctrl_group)
        diff_frame.pack(fill=tk.X, pady=2)
        ttk.Label(diff_frame, text="AI 難易度:").pack(side=tk.LEFT)
        self.diff_var = tk.StringVar(value="中級 (Depth 3)")
        self.diff_combo = ttk.Combobox(diff_frame, textvariable=self.diff_var, values=list(self.difficulty_levels.keys()), state="readonly", width=14)
        self.diff_combo.pack(side=tk.LEFT, padx=5)

        # Buttons
        btn_frame = ttk.Frame(ctrl_group)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="対局開始", command=self.reset_game).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="待った", command=self.undo_move).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="投了", command=self.resign_game).pack(side=tk.LEFT, padx=2)

        # Status Display
        status_frame = ttk.LabelFrame(right_frame, text="対局状態", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_label = ttk.Label(status_frame, text="準備完了", font=("Hiragino Sans", 11, "bold"), foreground="#111111")
        self.status_label.pack(anchor=tk.W)

        # Kifu Move Log
        kifu_frame = ttk.LabelFrame(right_frame, text="棋譜", padding=5)
        kifu_frame.pack(fill=tk.BOTH, expand=True)

        self.kifu_listbox = tk.Listbox(kifu_frame, font=("Courier", 10))
        kifu_scroll = ttk.Scrollbar(kifu_frame, orient=tk.VERTICAL, command=self.kifu_listbox.yview)
        self.kifu_listbox.configure(yscrollcommand=kifu_scroll.set)

        self.kifu_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kifu_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_side_change(self):
        if self.side_var.get() == "Sente":
            self.player_color = shogi.BLACK
            self.ai_color = shogi.WHITE
            self.board_canvas.set_flipped(False)
        else:
            self.player_color = shogi.WHITE
            self.ai_color = shogi.BLACK
            self.board_canvas.set_flipped(True)

    def reset_game(self):
        if self.ai_thinking:
            return

        self._on_side_change()
        self.board = shogi.Board()
        self.selected_square = None
        self.selected_hand_piece = None
        self.legal_targets = []
        self.last_move = None
        self.kifu_history = []
        self.kifu_listbox.delete(0, tk.END)

        self.update_ui()

        if self.board.turn == self.ai_color:
            self.trigger_ai_move()

    def update_ui(self):
        self.board_canvas.set_selected_square(self.selected_square, self.legal_targets)
        last_from = self.last_move.from_square if self.last_move else None
        last_to = self.last_move.to_square if self.last_move else None
        self.board_canvas.set_last_move(last_from, last_to)
        self.board_canvas.redraw(self.board)

        self.redraw_hands()
        self.update_status()

    def update_status(self):
        if self.board.is_checkmate():
            winner = "後手" if self.board.turn == shogi.BLACK else "先手"
            self.status_label.config(text=f"詰み！ {winner}の勝ちです！", foreground="#D32F2F")
        elif self.board.is_game_over():
            self.status_label.config(text="引き分け（千日手等）", foreground="#1976D2")
        elif self.ai_thinking:
            self.status_label.config(text="AIが思考中...", foreground="#E65100")
        else:
            turn_str = "先手 (▲)" if self.board.turn == shogi.BLACK else "後手 (△)"
            check_str = " [王手!]" if self.board.is_check() else ""
            self.status_label.config(text=f"{turn_str}の手番です{check_str}", foreground="#111111")

    def redraw_hands(self):
        # Draw Sente and Gote pieces in hand on hand canvases
        for color, canvas in [(shogi.BLACK, self.sente_hand_canvas), (shogi.WHITE, self.gote_hand_canvas)]:
            canvas.delete("all")
            hand = self.board.pieces_in_hand[color]
            x = 10
            hand_item_types = [shogi.ROOK, shogi.BISHOP, shogi.GOLD, shogi.SILVER, shogi.KNIGHT, shogi.LANCE, shogi.PAWN]
            for pt in hand_item_types:
                count = hand[pt]
                if count > 0:
                    kanji = PIECE_KANJI.get(pt, "")
                    text = f"{kanji}x{count}" if count > 1 else kanji

                    is_selected = (self.selected_hand_piece == (color, pt))
                    bg = "#76C7C0" if is_selected else "#FFF"
                    fg = "#207567" if is_selected else "#8B5A2B"

                    # Create button-like rectangle
                    rect_id = canvas.create_rectangle(x, 5, x + 45, 35, fill=bg, outline=fg, width=2 if is_selected else 1)
                    text_id = canvas.create_text(x + 22, 20, text=text, font=("Hiragino Sans", 10, "bold"), fill="#111111")

                    # Store piece type tag
                    canvas.tag_bind(rect_id, "<Button-1>", lambda e, c=color, p=pt: self._select_hand_piece(c, p))
                    canvas.tag_bind(text_id, "<Button-1>", lambda e, c=color, p=pt: self._select_hand_piece(c, p))

                    x += 52

    def _select_hand_piece(self, color, piece_type):
        if self.ai_thinking or self.board.is_game_over():
            return
        if self.board.turn != color or color != self.player_color:
            return

        if self.selected_hand_piece == (color, piece_type):
            self.selected_hand_piece = None
            self.legal_targets = []
        else:
            self.selected_square = None
            self.selected_hand_piece = (color, piece_type)
            # Find drop legal targets
            self.legal_targets = [m.to_square for m in self.board.legal_moves if m.from_square is None and m.drop_piece_type == piece_type]

        self.update_ui()

    def _on_square_click(self, square: int):
        if self.ai_thinking or self.board.is_game_over():
            return
        if self.board.turn != self.player_color:
            return

        # Case 1: Drop move selected
        if self.selected_hand_piece is not None:
            color, piece_type = self.selected_hand_piece
            if square in self.legal_targets:
                drop_move = shogi.Move(from_square=None, to_square=square, drop_piece_type=piece_type)
                self.make_move(drop_move)
                self.selected_hand_piece = None
                self.legal_targets = []
            else:
                self.selected_hand_piece = None
                self.legal_targets = []
                self.update_ui()
            return

        # Case 2: Move selected square piece to target square
        if self.selected_square is not None and square in self.legal_targets:
            from_sq = self.selected_square
            to_sq = square

            # Check promotion possibilities
            piece = self.board.piece_at(from_sq)
            can_promote = False
            must_promote = False

            if piece and piece.piece_type in (shogi.PAWN, shogi.LANCE, shogi.KNIGHT, shogi.SILVER, shogi.BISHOP, shogi.ROOK):
                from_rank = shogi.rank_index(from_sq)
                to_rank = shogi.rank_index(to_sq)
                in_promo_zone = (from_rank in (0, 1, 2) or to_rank in (0, 1, 2)) if piece.color == shogi.BLACK else (from_rank in (6, 7, 8) or to_rank in (6, 7, 8))

                if in_promo_zone:
                    can_promote = True
                    # Mandatory promotion check (Pawn/Lance at rank 1, Knight at rank 1 or 2)
                    if piece.piece_type in (shogi.PAWN, shogi.LANCE):
                        if (piece.color == shogi.BLACK and to_rank == 0) or (piece.color == shogi.WHITE and to_rank == 8):
                            must_promote = True
                    elif piece.piece_type == shogi.KNIGHT:
                        if (piece.color == shogi.BLACK and to_rank in (0, 1)) or (piece.color == shogi.WHITE and to_rank in (7, 8)):
                            must_promote = True

            promote = False
            if must_promote:
                promote = True
            elif can_promote:
                promote = messagebox.askyesno("成りの確認", "成りますか？", parent=self)

            move = shogi.Move(from_square=from_sq, to_square=to_sq, promotion=promote)
            if move in self.board.legal_moves:
                self.selected_square = None
                self.legal_targets = []
                self.make_move(move)
            else:
                self.selected_square = None
                self.legal_targets = []
                self.update_ui()
            return

        # Case 3: Select piece on board
        piece = self.board.piece_at(square)
        if piece and piece.color == self.board.turn and piece.color == self.player_color:
            self.selected_square = square
            self.selected_hand_piece = None
            self.legal_targets = [m.to_square for m in self.board.legal_moves if m.from_square == square]
        else:
            self.selected_square = None
            self.legal_targets = []

        self.update_ui()

    def make_move(self, move: shogi.Move):
        last_to = self.last_move.to_square if self.last_move else None
        move_str = move_to_japanese(self.board, move, last_to_square=last_to)

        self.kifu_history.append((move_str, self.board.sfen()))
        self.kifu_listbox.insert(tk.END, f"{len(self.kifu_history)}. {move_str}")
        self.kifu_listbox.see(tk.END)

        self.board.push(move)
        self.last_move = move

        self.update_ui()

        if not self.board.is_game_over() and self.board.turn == self.ai_color:
            self.trigger_ai_move()

    def trigger_ai_move(self):
        self.ai_thinking = True
        self.update_status()

        depth, max_time = self.difficulty_levels.get(self.diff_var.get(), (3, 3.0))

        def ai_thread_func():
            ai_move = self.search_engine.get_best_move(self.board, depth=depth, max_time=max_time)
            self.after(0, lambda: self._on_ai_move_complete(ai_move))

        threading.Thread(target=ai_thread_func, daemon=True).start()

    def _on_ai_move_complete(self, ai_move: shogi.Move):
        self.ai_thinking = False
        if ai_move and ai_move in self.board.legal_moves:
            self.make_move(ai_move)
        else:
            self.update_status()

    def undo_move(self):
        if self.ai_thinking or len(self.kifu_history) == 0:
            return

        # Undo 2 moves if playing against AI and it's player's turn, or 1 move if AI's turn
        undo_count = 2 if (self.player_color is not None and len(self.kifu_history) >= 2) else 1
        for _ in range(undo_count):
            if len(self.kifu_history) > 0:
                self.board.pop()
                self.kifu_history.pop()
                self.kifu_listbox.delete(tk.END)

        self.last_move = self.board.move_stack[-1] if len(self.board.move_stack) > 0 else None
        self.selected_square = None
        self.selected_hand_piece = None
        self.legal_targets = []
        self.update_ui()

    def resign_game(self):
        if self.ai_thinking or self.board.is_game_over():
            return
        if messagebox.askyesno("投了の確認", "投了しますか？", parent=self):
            winner = "後手" if self.board.turn == shogi.BLACK else "先手"
            self.status_label.config(text=f"投了！ {winner}の勝ちです！", foreground="#D32F2F")
            messagebox.showinfo("対局終了", f"{winner}の勝ちです。")
