"""
Evaluation module for Shogi engine.
Computes positional and material score relative to the current player's perspective.
"""

import shogi

# Base material values for piece types
PIECE_VALUES = {
    shogi.PAWN: 100,
    shogi.LANCE: 300,
    shogi.KNIGHT: 400,
    shogi.SILVER: 500,
    shogi.GOLD: 600,
    shogi.BISHOP: 800,
    shogi.ROOK: 1000,
    shogi.KING: 15000,
    shogi.PROM_PAWN: 550,
    shogi.PROM_LANCE: 550,
    shogi.PROM_KNIGHT: 550,
    shogi.PROM_SILVER: 550,
    shogi.PROM_BISHOP: 1100,
    shogi.PROM_ROOK: 1300,
}

# Hand piece values (slightly higher or equal to base piece values)
HAND_VALUES = {
    shogi.PAWN: 110,
    shogi.LANCE: 320,
    shogi.KNIGHT: 420,
    shogi.SILVER: 530,
    shogi.GOLD: 630,
    shogi.BISHOP: 850,
    shogi.ROOK: 1050,
}

# Simple positional bonus tables (9x9) from Black (BLACK / Sente) perspective
# Indexed by rank (0..8) and file (0..8)
# Higher rank index (0..8) corresponds to ranks 1..9 (1 is top/opponent side, 8 is bottom/own side)
PAWN_PST = [
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0], # Rank 1 (promotion zone)
    [20, 20, 20, 20, 20, 20, 20, 20, 20], # Rank 2
    [15, 15, 15, 20, 20, 20, 15, 15, 15], # Rank 3
    [10, 10, 15, 15, 20, 15, 15, 10, 10], # Rank 4
    [ 5,  5, 10, 10, 15, 10, 10,  5,  5], # Rank 5
    [ 0,  0,  5,  5,  5,  5,  5,  0,  0], # Rank 6
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0], # Rank 7
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0], # Rank 8
    [ 0,  0,  0,  0,  0,  0,  0,  0,  0], # Rank 9
]

def evaluate_board(board: shogi.Board) -> int:
    """
    Evaluates the current board state and returns a score relative to `board.turn`.
    A positive score means the side to move has an advantage.
    """
    if board.is_checkmate():
        # Current side is checkmated
        return -30000

    score = 0

    # 1. Evaluate pieces on board
    for square in range(81):
        piece = board.piece_at(square)
        if piece is None:
            continue

        val = PIECE_VALUES.get(piece.piece_type, 0)

        # Positional bonus for Pawn
        if piece.piece_type == shogi.PAWN:
            rank = shogi.rank_index(square)
            file = shogi.file_index(square)
            pst_val = PAWN_PST[rank][file] if piece.color == shogi.BLACK else PAWN_PST[8 - rank][8 - file]
            val += pst_val

        if piece.color == shogi.BLACK:
            score += val
        else:
            score -= val

    # 2. Evaluate pieces in hand (持ち駒)
    for piece_type in (shogi.PAWN, shogi.LANCE, shogi.KNIGHT, shogi.SILVER, shogi.GOLD, shogi.BISHOP, shogi.ROOK):
        val = HAND_VALUES.get(piece_type, 0)
        score += board.pieces_in_hand[shogi.BLACK][piece_type] * val
        score -= board.pieces_in_hand[shogi.WHITE][piece_type] * val

    # Return relative to current turn
    if board.turn == shogi.BLACK:
        return score
    else:
        return -score
