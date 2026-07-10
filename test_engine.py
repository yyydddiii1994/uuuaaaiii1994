from src.shogi_engine.search import Searcher
import shogi
import time

board = shogi.Board()
searcher = Searcher()
t = time.time()
best_move = searcher.search(board, max_depth=4, time_limit=5.0)
print(f"Time: {time.time() - t:.2f}s, nodes: {searcher.nodes}, Best move: {best_move.usi()}")
