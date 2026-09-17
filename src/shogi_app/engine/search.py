"""
Search module for Shogi engine.
Implements Negamax search with Alpha-Beta pruning, move ordering, and depth control.
"""

import time
import shogi
from src.shogi_app.engine.eval import evaluate_board

# Constants
INF = 100000
MATE_SCORE = 30000

class SearchEngine:
    def __init__(self, depth: int = 3, max_time: float = 3.0):
        self.depth = depth
        self.max_time = max_time
        self.nodes_searched = 0
        self.start_time = 0.0
        self.time_stopped = False

    def order_moves(self, board: shogi.Board, moves):
        """
        Orders legal moves to improve Alpha-Beta pruning efficiency.
        Captures and promotions are prioritized.
        """
        scored_moves = []
        for move in moves:
            score = 0
            if move.from_square is not None:
                # Normal move on board
                captured = board.piece_at(move.to_square)
                if captured is not None:
                    score += 100 + captured.piece_type * 10

                if move.promotion:
                    score += 80
            else:
                # Drop move
                if move.drop_piece_type is not None:
                    score += 10

            scored_moves.append((score, move))

        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in scored_moves]

    def alpha_beta(self, board: shogi.Board, depth: int, alpha: int, beta: int) -> int:
        self.nodes_searched += 1

        if time.time() - self.start_time >= self.max_time:
            self.time_stopped = True
            return evaluate_board(board)

        if board.is_game_over():
            if board.is_checkmate():
                return -MATE_SCORE + (self.depth - depth) # prefer quicker mate
            return 0 # Draw / Sennichite / Impasse

        if depth <= 0:
            return evaluate_board(board)

        legal_moves = list(board.legal_moves)
        ordered_moves = self.order_moves(board, legal_moves)

        best_score = -INF
        for move in ordered_moves:
            board.push(move)
            score = -self.alpha_beta(board, depth - 1, -beta, -alpha)
            board.pop()

            if self.time_stopped:
                return score

            if score > best_score:
                best_score = score

            if score > alpha:
                alpha = score

            if alpha >= beta:
                break # Beta cutoff

        return best_score

    def get_best_move(self, board: shogi.Board, depth: int = None, max_time: float = None) -> shogi.Move:
        """
        Finds the best move for current player using Iterative Deepening Negamax.
        """
        if depth is None:
            depth = self.depth
        if max_time is None:
            max_time = self.max_time

        self.start_time = time.time()
        self.max_time = max_time
        self.nodes_searched = 0
        self.time_stopped = False

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_move = legal_moves[0]

        # Iterative deepening
        for current_depth in range(1, depth + 1):
            if self.time_stopped:
                break

            current_best_move = None
            best_score = -INF
            alpha = -INF
            beta = INF

            ordered_moves = self.order_moves(board, legal_moves)

            for move in ordered_moves:
                board.push(move)
                score = -self.alpha_beta(board, current_depth - 1, -beta, -alpha)
                board.pop()

                if self.time_stopped and current_depth > 1:
                    # If time limit exceeded during search depth > 1, throw away incomplete depth result
                    break

                if score > best_score:
                    best_score = score
                    current_best_move = move

                if score > alpha:
                    alpha = score

            if not self.time_stopped and current_best_move is not None:
                best_move = current_best_move

            # Early break if checkmate found
            if best_score > MATE_SCORE - 100:
                break

        return best_move
