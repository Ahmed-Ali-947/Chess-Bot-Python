"""
Terminal chess — you're White, AI is Black.
Uses python-chess for rules/board, custom minimax for AI decisions.

Install: pip install chess
Run:     python Chessbot.py  (moves in UCI format, e.g. e2e4)
"""

import sys
import chess

# centipawn values
PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:   20000,
}

# positional bonuses per square, from White's perspective (a1=index 0)
# Black pieces use chess.square_mirror() to flip the table

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_TABLE = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

PIECE_SQUARE_TABLES = {
    chess.PAWN:   PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK:   ROOK_TABLE,
    chess.QUEEN:  QUEEN_TABLE,
    chess.KING:   KING_TABLE,
}

# depth 4+ gets slow without move ordering
SEARCH_DEPTH = 3

class ChessAI:
    """Minimax AI with alpha-beta pruning + TT + MVV-LVA"""

    def __init__(self, depth: int = SEARCH_DEPTH):
        self.depth = depth
        self.nodes_evaluated = 0
        self.tt = {}   # Transposition Table

    # Evaluation Function
    def evaluate(self, board: chess.Board) -> float:

        if board.is_checkmate():
            return float('-inf') if board.turn == chess.WHITE else float('inf')

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0

        for sq in chess.SQUARES:
            piece = board.piece_at(sq)

            if piece is None:
                continue

            piece_value = PIECE_VALUES[piece.piece_type]
            table = PIECE_SQUARE_TABLES[piece.piece_type]

            if piece.color == chess.WHITE:
                score += piece_value + table[sq]
            else:
                score -= piece_value + table[chess.square_mirror(sq)]

        return score

    # MVV-LVA Move Ordering
    def score_move(self, board: chess.Board, move: chess.Move):

        # Captures first using MVV-LVA
        if board.is_capture(move):

            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)

            # en passant safety
            if victim is None:
                return 1000

            return (
                PIECE_VALUES[victim.piece_type] * 10
                - PIECE_VALUES[attacker.piece_type]
            )

        # Promotions next
        if move.promotion:
            return 800

        # Quiet moves last
        return 0

    def order_moves(self, board: chess.Board):
        moves = list(board.legal_moves)
        moves.sort(
            key=lambda move: self.score_move(board, move),
            reverse=True
        )
        return moves

    # Alpha-Beta + TT
    def minimax(self, board: chess.Board,
                depth: int,
                alpha: float,
                beta: float,
                is_maximizing: bool):

        self.nodes_evaluated += 1

        # Transposition Table Lookup
        key = board.fen()

        if key in self.tt:
            stored_depth, stored_score = self.tt[key]

            if stored_depth >= depth:
                return stored_score

        # Leaf Node
        if depth == 0 or board.is_game_over():

            score = self.evaluate(board)
            self.tt[key] = (depth, score)
            return score

        # Ordered Moves
        moves = self.order_moves(board)

        # Maximizing (White)
        if is_maximizing:

            best_score = float('-inf')

            for move in moves:

                board.push(move)

                score = self.minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    False
                )

                board.pop()

                best_score = max(best_score, score)
                alpha = max(alpha, best_score)

                if beta <= alpha:
                    break   # beta cutoff

        # Minimizing (Black)
        else:

            best_score = float('inf')

            for move in moves:

                board.push(move)

                score = self.minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    True
                )

                board.pop()

                best_score = min(best_score, score)
                beta = min(beta, best_score)

                if beta <= alpha:
                    break   # alpha cutoff

        # Store in TT
        self.tt[key] = (depth, best_score)

        return best_score

    # Root Search
    def find_best_move(self, board: chess.Board):

        self.nodes_evaluated = 0
        self.tt.clear()   # clear each turn (simple version)

        best_move = None
        best_eval = float('inf')   # Black minimizing

        moves = self.order_moves(board)

        for move in moves:

            board.push(move)

            eval_score = self.minimax(
                board,
                self.depth - 1,
                float('-inf'),
                float('inf'),
                True
            )

            board.pop()

            if eval_score < best_eval:
                best_eval = eval_score
                best_move = move

        print(
            f"  [AI evaluated {self.nodes_evaluated} positions, "
            f"score: {best_eval}]"
        )

        return best_move