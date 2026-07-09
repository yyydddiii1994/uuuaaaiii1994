import shogi

# Material values
PIECE_VALUES = {
    shogi.PAWN: 100,
    shogi.LANCE: 300,
    shogi.KNIGHT: 400,
    shogi.SILVER: 500,
    shogi.GOLD: 600,
    shogi.BISHOP: 800,
    shogi.ROOK: 1000,
    shogi.KING: 15000,
    shogi.PROM_PAWN: 600,
    shogi.PROM_LANCE: 600,
    shogi.PROM_KNIGHT: 600,
    shogi.PROM_SILVER: 600,
    shogi.PROM_BISHOP: 1000,
    shogi.PROM_ROOK: 1200,
}

# Piece-Square Tables (PST)
def get_pst_value(piece_type, color, square):
    rank = shogi.rank_index(square)
    file = shogi.file_index(square)

    # Mirror rank for white
    if color == shogi.WHITE:
        rank = 8 - rank

    value = 0

    # Encourage advancing pieces
    if piece_type in (shogi.PAWN, shogi.LANCE, shogi.KNIGHT, shogi.SILVER):
        # Bonus for moving towards enemy camp (rank 0-2)
        if rank <= 2:
            value += 30
        elif rank <= 4:
            value += 10

    # King safety (encourage staying in camp and corners)
    if piece_type == shogi.KING:
        if rank >= 6:
            value += 50
            if file <= 2 or file >= 6:
                value += 30 # Encourage castling in corners
        elif rank <= 3:
            value -= 100 # Penalty for advancing too far in early/mid game

    # Rook and Bishop: encourage centralization and open files (simplified)
    if piece_type in (shogi.ROOK, shogi.BISHOP, shogi.PROM_ROOK, shogi.PROM_BISHOP):
        if 3 <= file <= 5:
            value += 20

    return value

def evaluate(board: shogi.Board):
    if board.is_checkmate():
        return -30000 if board.turn == shogi.BLACK else 30000

    score = 0

    # Piece material and PST on board
    for square in shogi.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            value = PIECE_VALUES.get(piece.piece_type, 0)
            pst_value = get_pst_value(piece.piece_type, piece.color, square)

            total_val = value + pst_value
            if piece.color == shogi.BLACK:
                score += total_val
            else:
                score -= total_val

    # Pieces in hand
    for piece_type in shogi.PIECE_TYPES_WITHOUT_KING:
        b_count = board.pieces_in_hand[shogi.BLACK].get(piece_type, 0)
        w_count = board.pieces_in_hand[shogi.WHITE].get(piece_type, 0)
        # Add a small bonus (e.g. 1.1x) for pieces in hand as they are flexible
        value = int(PIECE_VALUES.get(piece_type, 0) * 1.1)
        score += b_count * value
        score -= w_count * value

    # Return relative to the side to move
    return score if board.turn == shogi.BLACK else -score
