import sys
import shogi
import time
import threading
from .search import Searcher

class USIEngine:
    def __init__(self):
        self.board = shogi.Board()
        self.searcher = Searcher()
        self.engine_name = "Jules Shogi"
        self.engine_author = "Jules"
        self.search_thread = None

    def _search_task(self, board_copy, time_limit):
        # Increased depth for better potential
        best_move = self.searcher.search(board_copy, max_depth=12, time_limit=time_limit)

        if best_move:
            print(f"bestmove {best_move.usi()}")
        else:
            print("bestmove resign")
        sys.stdout.flush()

    def run(self):
        while True:
            try:
                line = sys.stdin.readline().strip()
                if not line:
                    continue

                parts = line.split()
                cmd = parts[0]

                if cmd == "usi":
                    print(f"id name {self.engine_name}")
                    print(f"id author {self.engine_author}")
                    print("usiok")
                    sys.stdout.flush()

                elif cmd == "isready":
                    print("readyok")
                    sys.stdout.flush()

                elif cmd == "usinewgame":
                    self.board.reset()
                    self.searcher.clear_tt()

                elif cmd == "position":
                    if len(parts) > 1:
                        if parts[1] == "startpos":
                            self.board.reset()
                            moves_start = 2
                        elif parts[1] == "sfen":
                            if len(parts) >= 6:
                                sfen = " ".join(parts[2:6])
                                try:
                                    self.board.set_sfen(sfen)
                                except Exception as e:
                                    print(f"info string Failed to parse sfen: {e}")
                                moves_start = 6
                            else:
                                continue
                        else:
                            continue

                        if len(parts) > moves_start and parts[moves_start] == "moves":
                            for move_str in parts[moves_start+1:]:
                                try:
                                    self.board.push_usi(move_str)
                                except Exception as e:
                                    print(f"info string Failed to push move {move_str}: {e}")

                elif cmd == "go":
                    time_limit = 5.0

                    if "infinite" in parts:
                        time_limit = 999999.0
                    else:
                        if "btime" in parts and self.board.turn == shogi.BLACK:
                            idx = parts.index("btime")
                            if idx + 1 < len(parts):
                                btime = int(parts[idx+1])
                                time_limit = max(0.5, btime / 30000.0)
                        elif "wtime" in parts and self.board.turn == shogi.WHITE:
                            idx = parts.index("wtime")
                            if idx + 1 < len(parts):
                                wtime = int(parts[idx+1])
                                time_limit = max(0.5, wtime / 30000.0)

                        if "byoyomi" in parts:
                            idx = parts.index("byoyomi")
                            if idx + 1 < len(parts):
                                byoyomi = int(parts[idx+1])
                                time_limit = max(time_limit, byoyomi / 1000.0 - 0.2)

                    board_copy = shogi.Board(self.board.sfen())
                    self.searcher.stop_search = False

                    self.search_thread = threading.Thread(target=self._search_task, args=(board_copy, time_limit))
                    self.search_thread.start()

                elif cmd == "stop":
                    self.searcher.stop_search = True
                    if self.search_thread:
                        self.search_thread.join()

                elif cmd == "quit":
                    self.searcher.stop_search = True
                    if self.search_thread and self.search_thread.is_alive():
                        self.search_thread.join()
                    break
            except Exception as e:
                print(f"info string error: {e}")
                sys.stdout.flush()

if __name__ == "__main__":
    engine = USIEngine()
    engine.run()
