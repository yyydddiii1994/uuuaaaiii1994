import shogi
import time
from .engine import evaluate

# TT Entry flags
TT_EXACT = 0
TT_ALPHA = 1
TT_BETA = 2

class Searcher:
    def __init__(self):
        self.nodes = 0
        self.stop_search = False
        self.tt = {} # Transposition Table

    def clear_tt(self):
        self.tt.clear()

    def alphabeta(self, board, depth, alpha, beta, is_quiescence=False, can_null=True):
        self.nodes += 1
        if self.stop_search:
            return 0

        alpha_orig = alpha

        # Transposition Table lookup
        hash_key = board.zobrist_hash()
        tt_entry = self.tt.get(hash_key)

        if tt_entry is not None and tt_entry['depth'] >= depth:
            if tt_entry['flag'] == TT_EXACT:
                return tt_entry['value']
            elif tt_entry['flag'] == TT_ALPHA:
                if tt_entry['value'] <= alpha:
                    return alpha
            elif tt_entry['flag'] == TT_BETA:
                if tt_entry['value'] >= beta:
                    return beta

        if depth <= 0 and not is_quiescence:
            return self.quiescence_search(board, alpha, beta)

        if board.is_game_over():
            if board.is_checkmate():
                return -30000 + (100 - depth) # Mate distance
            return 0 # Draw/Stalemate

        # Null Move Pruning
        if can_null and depth >= 3 and not board.is_check():
            # Estimate if we have enough material to safely null move
            # In shogi, we almost always have pieces, so we can be a bit aggressive.
            board.push(shogi.Move.null())
            null_score = -self.alphabeta(board, depth - 1 - 2, -beta, -beta + 1, False, False)
            board.pop()

            if null_score >= beta:
                return beta

        legal_moves = list(board.generate_legal_moves())
        if not legal_moves:
            return -30000 + (100 - depth)

        tt_move = tt_entry['best_move'] if tt_entry else None

        # Move ordering
        def move_score(move):
            if move == tt_move:
                return 20000 # TT move first

            score = 0
            if board.piece_at(move.to_square): # Capture
                captured_piece = board.piece_at(move.to_square)
                if not move.drop_piece_type:
                    attacker = board.piece_at(move.from_square)
                    if captured_piece and attacker:
                        score += 1000 * captured_piece.piece_type - attacker.piece_type
            if move.promotion:
                score += 500
            if move.drop_piece_type:
                score += 50
            return score

        legal_moves.sort(key=move_score, reverse=True)

        best_move = None
        best_val = -30000

        # Principal Variation Search (PVS)
        for i, move in enumerate(legal_moves):
            board.push(move)

            if i == 0:
                # Full window search for first move
                score = -self.alphabeta(board, depth - 1, -beta, -alpha)
            else:
                # Null window search
                score = -self.alphabeta(board, depth - 1, -alpha - 1, -alpha)
                if alpha < score < beta:
                    # Re-search if it failed high
                    score = -self.alphabeta(board, depth - 1, -beta, -alpha)

            board.pop()

            if score > best_val:
                best_val = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                break # Beta cutoff

        # Store to TT
        tt_flag = TT_EXACT
        if best_val <= alpha_orig:
            tt_flag = TT_ALPHA
        elif best_val >= beta:
            tt_flag = TT_BETA

        self.tt[hash_key] = {
            'value': best_val,
            'depth': depth,
            'flag': tt_flag,
            'best_move': best_move
        }

        return best_val

    def quiescence_search(self, board, alpha, beta):
        self.nodes += 1
        if self.stop_search:
            return 0

        stand_pat = evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        legal_moves = list(board.generate_legal_moves())
        capture_moves = [m for m in legal_moves if board.piece_at(m.to_square) is not None and m.drop_piece_type is None]

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


    def search(self, board, max_depth=6, time_limit=2.0):
        self.nodes = 0
        self.stop_search = False
        start_time = time.time()

        best_move = None
        best_score = -30000

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

            # Root move ordering based on previous iteration
            def root_move_score(move):
                if move == best_move: return 20000

                score = 0
                if board.piece_at(move.to_square): score += 100
                if move.promotion: score += 50
                return score

            legal_moves.sort(key=root_move_score, reverse=True)

            for i, move in enumerate(legal_moves):
                board.push(move)

                if i == 0:
                    score = -self.alphabeta(board, depth - 1, -beta, -alpha)
                else:
                    score = -self.alphabeta(board, depth - 1, -alpha - 1, -alpha)
                    if alpha < score < beta:
                        score = -self.alphabeta(board, depth - 1, -beta, -alpha)

                board.pop()

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move
                if score > alpha:
                    alpha = score

                if (time.time() - start_time) > time_limit:
                    break

            if current_best_move is not None:
                best_move = current_best_move
                best_score = current_best_score
                print(f"info depth {depth} score cp {best_score} nodes {self.nodes} time {int((time.time() - start_time) * 1000)} pv {best_move.usi()}")

        return best_move
