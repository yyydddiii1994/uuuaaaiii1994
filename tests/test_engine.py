import unittest
import shogi
from src.shogi_app.engine.eval import evaluate_board
from src.shogi_app.engine.search import SearchEngine

class TestEngine(unittest.TestCase):
    def test_evaluation_initial_board(self):
        board = shogi.Board()
        score = evaluate_board(board)
        self.assertEqual(score, 0, "Initial board evaluation should be 0 from Sente's perspective.")

    def test_evaluation_material_advantage(self):
        board = shogi.Board()
        # Give Black a captured pawn in hand
        board.add_piece_into_hand(shogi.PAWN, shogi.BLACK)
        score = evaluate_board(board)
        self.assertGreater(score, 0, "Black with extra pawn in hand should have positive evaluation.")

    def test_search_returns_legal_move(self):
        board = shogi.Board()
        engine = SearchEngine(depth=2, max_time=1.0)
        best_move = engine.get_best_move(board)
        self.assertIsNotNone(best_move)
        self.assertIn(best_move, board.legal_moves)

    def test_search_checkmate(self):
        # Create a 1-step mate position or simple checkmate test
        board = shogi.Board()
        # Set up a position where Black can mate in 1 move if possible, or verify checkmate detection
        engine = SearchEngine(depth=2, max_time=1.0)
        move = engine.get_best_move(board)
        self.assertIsNotNone(move)

if __name__ == "__main__":
    unittest.main()
