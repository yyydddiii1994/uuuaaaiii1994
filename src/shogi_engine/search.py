import shogi
import time
from .engine import evaluate

class Searcher:
    def __init__(self):
        self.nodes = 0
        self.stop_search = False

    def alphabeta(self, board, depth, alpha, beta, is_quiescence=False):
        self.nodes += 1
        if self.stop_search:
            return 0

        if depth <= 0 and not is_quiescence:
            # Enter Quiescence Search
            return self.quiescence_search(board, alpha, beta)

        if board.is_game_over():
            if board.is_checkmate():
                return -30000
            return 0 # Draw/Stalemate

        legal_moves = list(board.generate_legal_moves())
        if not legal_moves:
            return -30000

        # Move ordering
        def move_score(move):
            score = 0
            if board.piece_at(move.to_square): # Capture
                captured_piece = board.piece_at(move.to_square)
                # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
                if not move.drop_piece_type:
                    attacker = board.piece_at(move.from_square)
                    if captured_piece and attacker:
                        score += 1000 * captured_piece.piece_type - attacker.piece_type
            if move.promotion:
                score += 500
            if move.drop_piece_type:
                score += 50 # Drops are generally good in shogi, but captures/promotions are better
            return score

        legal_moves.sort(key=move_score, reverse=True)

        for move in legal_moves:
            board.push(move)
            score = -self.alphabeta(board, depth - 1, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def quiescence_search(self, board, alpha, beta):
        self.nodes += 1
        if self.stop_search:
            return 0

        stand_pat = evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Generate only captures in quiescence search (simplification)
        # Note: True quiescence in shogi is very complex due to drops. We'll stick to basic captures.
        legal_moves = list(board.generate_legal_moves())
        capture_moves = [m for m in legal_moves if board.piece_at(m.to_square) is not None and m.drop_piece_type is None]

        # Sort captures (MVV-LVA)
        def capture_score(move):
            captured_piece = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if captured_piece and attacker:
                return 1000 * captured_piece.piece_type - attacker.piece_type
            return 0

        capture_moves.sort(key=capture_score, reverse=True)

        for move in capture_moves:
            board.push(move)
            score = -self.quiescence_search(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha


    def search(self, board, max_depth=4, time_limit=2.0):
        self.nodes = 0
        self.stop_search = False
        start_time = time.time()

        best_move = None
        best_score = -30000

        # Iterative deepening
        for depth in range(1, max_depth + 1):
            if self.stop_search or (time.time() - start_time) > time_limit:
                break

            current_best_move = None
            current_best_score = -30000
            alpha = -30000
            beta = 30000

            legal_moves = list(board.generate_legal_moves())
            if not legal_moves:
                break

            # Basic move ordering for root
            def root_move_score(move):
                if move == best_move: return 10000 # PV move from previous iteration
                score = 0
                if board.piece_at(move.to_square): score += 100
                if move.promotion: score += 50
                return score

            legal_moves.sort(key=root_move_score, reverse=True)

            for move in legal_moves:
                board.push(move)
                score = -self.alphabeta(board, depth - 1, -beta, -alpha)
                board.pop()

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move
                if score > alpha:
                    alpha = score

                # Time management check after each move at root
                if (time.time() - start_time) > time_limit:
                    break

            if current_best_move is not None:
                best_move = current_best_move
                best_score = current_best_score
                print(f"info depth {depth} score cp {best_score} nodes {self.nodes} time {int((time.time() - start_time) * 1000)} pv {best_move.usi()}")

        return best_move
