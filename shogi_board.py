import tkinter as tk
from tkinter import simpledialog, messagebox
import copy

class ShogiBoard(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("将棋盤")

        self.board_state = [[None for _ in range(9)] for _ in range(9)]
        self.selected_entity = None # Can be a board position (r, c) or a captured piece ('piece_name', player)
        self.captured_pieces = {1: [], 2: []}  # Captured pieces for Player 1 and 2
        self.current_player = 1 # Start with player 1
        self.history = []

        self.PROMOTION_MAP = {
            '歩': 'と', '香': '成香', '桂': '成桂', '銀': '全',
            '角': '馬', '飛': '龍'
        }
        self.DEMOTION_MAP = {v: k for k, v in self.PROMOTION_MAP.items()}
        self.PROMOTED_PIECES = set(self.PROMOTION_MAP.values())

        # Define piece movements
        gold_moves = {'moves': [(-1, 0), (-1, -1), (-1, 1), (0, -1), (0, 1), (1, 0)], 'range': 1}
        self.PIECE_MOVES = {
            '歩': {'moves': [(-1, 0)], 'range': 1},
            '香': {'moves': [(-1, 0)], 'range': 8},
            '桂': {'moves': [(-2, -1), (-2, 1)], 'range': 1},
            '銀': {'moves': [(-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)], 'range': 1},
            '金': gold_moves,
            '角': {'moves': [(-1, -1), (-1, 1), (1, -1), (1, 1)], 'range': 8},
            '飛': {'moves': [(-1, 0), (1, 0), (0, -1), (0, 1)], 'range': 8},
            '玉': {'moves': [(-1, 0), (-1, -1), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1), (1, 1)], 'range': 1},
            '王': {'moves': [(-1, 0), (-1, -1), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1), (1, 1)], 'range': 1},
            # Promoted pieces
            'と': gold_moves,
            '成香': gold_moves,
            '成桂': gold_moves,
            '全': gold_moves,
            '馬': {'moves': [(-1, -1), (-1, 1), (1, -1), (1, 1)], 'range': 8, 'plus': [(-1, 0), (1, 0), (0, -1), (0, 1)]},
            '龍': {'moves': [(-1, 0), (1, 0), (0, -1), (0, 1)], 'range': 8, 'plus': [(-1, -1), (-1, 1), (1, -1), (1, 1)]},
        }

        self.create_widgets()
        self.setup_pieces()


    def create_widgets(self):
        main_frame = tk.Frame(self.master)
        main_frame.pack(padx=10, pady=10)

        self.canvas = tk.Canvas(main_frame, width=500, height=500, bg="burlywood")
        self.canvas.grid(row=0, column=0, rowspan=2)
        self.canvas.bind("<Button-1>", self.handle_board_click)

        # Captured pieces stands
        self.komadai2 = tk.Canvas(main_frame, width=120, height=230, bg="wheat")
        self.komadai2.grid(row=0, column=1, padx=5)
        self.komadai2.bind("<Button-1>", lambda e: self.handle_komadai_click(e, 2))
        self.komadai1 = tk.Canvas(main_frame, width=120, height=230, bg="wheat")
        self.komadai1.grid(row=1, column=1, padx=5)
        self.komadai1.bind("<Button-1>", lambda e: self.handle_komadai_click(e, 1))

        # Control buttons
        control_frame = tk.Frame(self.master)
        control_frame.pack(pady=5)
        undo_button = tk.Button(control_frame, text="待った", command=self.undo_move)
        undo_button.pack()


        self.draw_board()

    def draw_board(self):
        """Draws the 9x9 grid, pieces, and selection highlight."""
        self.canvas.delete("all")
        for i in range(10):
            # Vertical lines
            self.canvas.create_line(i * 50 + 25, 25, i * 50 + 25, 475, fill="black")
            # Horizontal lines
            self.canvas.create_line(25, i * 50 + 25, 475, i * 50 + 25, fill="black")
        self.redraw_pieces()
        self.draw_captured_stands()
        self.draw_selection_highlight()

    def draw_captured_stands(self):
        """Redraws the captured pieces stands."""
        self.komadai1.delete("all")
        self.komadai2.delete("all")

        # Player 1's stand
        for i, piece in enumerate(self.captured_pieces[1]):
            x = 30 + (i % 4) * 25
            y = 30 + (i // 4) * 35
            self.komadai1.create_text(x, y, text=piece, font=("Arial", 16))

        # Player 2's stand
        for i, piece in enumerate(self.captured_pieces[2]):
            x = 30 + (i % 4) * 25
            y = 30 + (i // 4) * 35
            self.komadai2.create_text(x, y, text=piece, font=("Arial", 16), angle=180)

    def draw_selection_highlight(self):
        """Draws a highlight around the selected piece or stand."""
        if not self.selected_entity:
            return

        # Highlight on board
        if isinstance(self.selected_entity, tuple):
            row, col = self.selected_entity
            x0, y0 = col * 50 + 25, row * 50 + 25
            self.canvas.create_rectangle(x0, y0, x0 + 50, y0 + 50, outline="blue", width=3)

        # Highlight on komadai
        elif isinstance(self.selected_entity, dict):
            player = self.selected_entity["player"]
            index = self.selected_entity["index"]
            komadai = self.komadai1 if player == 1 else self.komadai2

            if index < len(self.captured_pieces[player]):
                x = 30 + (index % 4) * 25
                y = 30 + (index // 4) * 35
                komadai.create_rectangle(x - 12, y - 17, x + 12, y + 17, outline="blue", width=2)

    def setup_pieces(self):
        """Sets up the initial board state with piece objects."""
        # Reset history for a new game
        self.history = []
        self.board_state = [[None for _ in range(9)] for _ in range(9)]
        self.captured_pieces = {1: [], 2: []}
        self.current_player = 1

        initial_placement = {
            (0, 0): {"piece": "香", "player": 2}, (0, 1): {"piece": "桂", "player": 2},
            (0, 2): {"piece": "銀", "player": 2}, (0, 3): {"piece": "金", "player": 2},
            (0, 4): {"piece": "王", "player": 2}, (0, 5): {"piece": "金", "player": 2},
            (0, 6): {"piece": "銀", "player": 2}, (0, 7): {"piece": "桂", "player": 2},
            (0, 8): {"piece": "香", "player": 2},
            (1, 1): {"piece": "飛", "player": 2}, (1, 7): {"piece": "角", "player": 2},
            (2, 0): {"piece": "歩", "player": 2}, (2, 1): {"piece": "歩", "player": 2},
            (2, 2): {"piece": "歩", "player": 2}, (2, 3): {"piece": "歩", "player": 2},
            (2, 4): {"piece": "歩", "player": 2}, (2, 5): {"piece": "歩", "player": 2},
            (2, 6): {"piece": "歩", "player": 2}, (2, 7): {"piece": "歩", "player": 2},
            (2, 8): {"piece": "歩", "player": 2},

            (8, 0): {"piece": "香", "player": 1}, (8, 1): {"piece": "桂", "player": 1},
            (8, 2): {"piece": "銀", "player": 1}, (8, 3): {"piece": "金", "player": 1},
            (8, 4): {"piece": "玉", "player": 1}, (8, 5): {"piece": "金", "player": 1},
            (8, 6): {"piece": "銀", "player": 1}, (8, 7): {"piece": "桂", "player": 1},
            (8, 8): {"piece": "香", "player": 1},
            (7, 1): {"piece": "角", "player": 1}, (7, 7): {"piece": "飛", "player": 1},
            (6, 0): {"piece": "歩", "player": 1}, (6, 1): {"piece": "歩", "player": 1},
            (6, 2): {"piece": "歩", "player": 1}, (6, 3): {"piece": "歩", "player": 1},
            (6, 4): {"piece": "歩", "player": 1}, (6, 5): {"piece": "歩", "player": 1},
            (6, 6): {"piece": "歩", "player": 1}, (6, 7): {"piece": "歩", "player": 1},
            (6, 8): {"piece": "歩", "player": 1},
        }
        for (row, col), piece_data in initial_placement.items():
            self.board_state[row][col] = piece_data

        self.save_state_to_history()
        self.draw_board()


    def redraw_pieces(self):
        """Redraws all pieces based on the current board_state."""
        for r, row_data in enumerate(self.board_state):
            for c, piece_data in enumerate(row_data):
                if piece_data:
                    self.draw_piece(r, c, piece_data)

    def draw_piece(self, row, col, piece_data):
        """Draws a single piece on the board."""
        x = col * 50 + 50
        y = row * 50 + 50
        piece_text = piece_data["piece"]
        player = piece_data["player"]

        # Player 2 (Gote) pieces are drawn rotated 180 degrees
        if player == 2:
            self.canvas.create_text(x, y, text=piece_text, font=("Arial", 20), angle=180)
        # Player 1 (Sente) pieces are drawn normally
        else:
            self.canvas.create_text(x, y, text=piece_text, font=("Arial", 20))

    def handle_board_click(self, event):
        """Handles user clicks on the main shogi board."""
        col = (event.x - 25) // 50
        row = (event.y - 25) // 50
        if not (0 <= row < 9 and 0 <= col < 9):
            self.selected_entity = None
            self.draw_board()
            return

        clicked_piece = self.board_state[row][col]

        # A captured piece is selected, try to drop
        if isinstance(self.selected_entity, dict):
            self.drop_piece(self.selected_entity, row, col)
            self.selected_entity = None
        # A board piece is selected
        elif isinstance(self.selected_entity, tuple):
            start_row, start_col = self.selected_entity
            if (row, col) == (start_row, start_col): # Deselect
                self.selected_entity = None
            elif clicked_piece and clicked_piece["player"] == self.current_player: # Reselect
                self.selected_entity = (row, col)
            else: # Try to move
                self.move_piece(start_row, start_col, row, col)
                self.selected_entity = None
        # Nothing is selected
        else:
            if clicked_piece and clicked_piece["player"] == self.current_player:
                self.selected_entity = (row, col)

        self.draw_board()

    def handle_komadai_click(self, event, player):
        """Handles clicks on the captured pieces stand (komadai)."""
        if player != self.current_player:
            self.selected_entity = None
        else:
            clicked_index = int((event.y - 10) / 35) * 4 + int((event.x - 10) / 25)
            if clicked_index < len(self.captured_pieces[player]):
                piece_name = self.captured_pieces[player][clicked_index]
                new_selection = {"piece": piece_name, "player": player, "index": clicked_index}

                is_same = False
                if isinstance(self.selected_entity, dict) and self.selected_entity == new_selection:
                    is_same = True

                if is_same:
                    self.selected_entity = None
                else:
                    self.selected_entity = new_selection
            else:
                self.selected_entity = None

        self.draw_board()

    def move_piece(self, start_row, start_col, end_row, end_col):
        piece_to_move = self.board_state[start_row][start_col]
        if not self.is_valid_move(piece_to_move, (start_row, start_col), (end_row, end_col)):
            return # Invalid move

        moving_player = piece_to_move["player"]

        target_piece = self.board_state[end_row][end_col]
        if target_piece and target_piece["player"] == moving_player:
            return # Cannot capture own piece

        if target_piece:
            captured_piece_name = target_piece["piece"]
            if captured_piece_name in self.PROMOTED_PIECES:
                captured_piece_name = self.DEMOTION_MAP[captured_piece_name]
            self.captured_pieces[moving_player].append(captured_piece_name)

        # Promotion logic
        if self.can_promote(piece_to_move, start_row, end_row):
            if messagebox.askyesno("昇格", "駒を成りますか？"):
                promoted_piece_name = self.PROMOTION_MAP.get(piece_to_move["piece"])
                if promoted_piece_name:
                    piece_to_move["piece"] = promoted_piece_name


        self.save_state_to_history()
        self.board_state[end_row][end_col] = piece_to_move
        self.board_state[start_row][start_col] = None
        self.current_player = 3 - self.current_player

    def can_promote(self, piece, from_row, to_row):
        player = piece["player"]
        piece_type = piece["piece"]

        if piece_type in self.PROMOTED_PIECES: # Already promoted
            return False

        promotion_zone_start = 0
        promotion_zone_end = 2

        if player == 2:
            promotion_zone_start = 6
            promotion_zone_end = 8

        # Check if the move is into, out of, or within the promotion zone
        from_in_zone = promotion_zone_start <= from_row <= promotion_zone_end
        to_in_zone = promotion_zone_start <= to_row <= promotion_zone_end

        # Pawns and lances MUST promote on the final rank
        if piece_type in "歩香" and (to_row == 0 or to_row == 8):
            return True
        # Knight MUST promote on the final two ranks
        if piece_type == "桂" and (0 <= to_row <= 1 or 7 <= to_row <= 8):
            return True

        if piece_type in "歩香桂銀金角飛玉王":
             if from_in_zone or to_in_zone:
                 return True

        return False

    def is_valid_move(self, piece, start_pos, end_pos):
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        player = piece["player"]
        piece_type = piece["piece"]

        d_row, d_col = end_row - start_row, end_col - start_col

        # Player 2 moves are inverted
        if player == 2:
            d_row, d_col = -d_row, -d_col

        move_info = self.PIECE_MOVES.get(piece_type)
        if not move_info: return False

        # Simple 1-step moves
        if (d_row, d_col) in move_info['moves'] and move_info['range'] == 1:
            return True

        # Ranged moves (Rook, Bishop, Lance)
        if move_info['range'] > 1:
            for move_dir in move_info['moves']:
                for i in range(1, move_info['range'] + 1):
                    step_row, step_col = move_dir[0] * i, move_dir[1] * i
                    if (step_row, step_col) == (d_row, d_col):
                        # Check for blocking pieces
                        for j in range(1, i):
                            check_row = start_row + (move_dir[0] * j if player == 1 else -move_dir[0] * j)
                            check_col = start_col + (move_dir[1] * j if player == 1 else -move_dir[1] * j)
                            if self.board_state[check_row][check_col]:
                                return False # Blocked path
                        return True

        # Promoted pieces with special 1-step moves
        if 'plus' in move_info and (d_row, d_col) in move_info['plus']:
            return True

        return False

    def drop_piece(self, piece_info, row, col):
        piece_name = piece_info["piece"]
        player = piece_info["player"]

        if not self.is_valid_drop(piece_name, player, row, col):
            messagebox.showerror("反則手", "その場所には駒を打てません。")
            return

        self.save_state_to_history()
        self.captured_pieces[player].pop(piece_info["index"])
        self.board_state[row][col] = {"piece": piece_name, "player": player}
        self.current_player = 3 - self.current_player

    def is_valid_drop(self, piece_name, player, row, col):
        # Rule 1: Cannot drop on an occupied square
        if self.board_state[row][col] is not None:
            return False

        # Rule 2: Nifu (Two Pawns in the same file)
        if piece_name == '歩':
            for r in range(9):
                piece = self.board_state[r][col]
                if piece and piece["piece"] == '歩' and piece["player"] == player:
                    return False

        # Rule 3: Piece with no legal moves
        if player == 1: # Sente
            if (piece_name == '歩' or piece_name == '香') and row == 0:
                return False
            if piece_name == '桂' and row <= 1:
                return False
        elif player == 2: # Gote
            if (piece_name == '歩' or piece_name == '香') and row == 8:
                return False
            if piece_name == '桂' and row >= 7:
                return False

        # Rule 4: Uchifuzume (Pawn drop checkmate) is not implemented due to complexity.

        return True

    def save_state_to_history(self):
        """Saves the current game state to the history."""
        state = {
            "board_state": copy.deepcopy(self.board_state),
            "captured_pieces": copy.deepcopy(self.captured_pieces),
            "current_player": self.current_player
        }
        self.history.append(state)

    def undo_move(self):
        """Reverts to the previous game state."""
        if len(self.history) > 1:
            self.history.pop() # Remove current state
            last_state = self.history[-1]
            self.board_state = copy.deepcopy(last_state["board_state"])
            self.captured_pieces = copy.deepcopy(last_state["captured_pieces"])
            self.current_player = last_state["current_player"]
            self.selected_entity = None
            self.draw_board()


if __name__ == "__main__":
    root = tk.Tk()
    app = ShogiBoard(master=root)
    app.mainloop()
