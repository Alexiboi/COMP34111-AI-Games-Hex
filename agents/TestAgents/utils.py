import random
from src.Board import Board
from src.Move import Move

def make_valid_move(board: Board) -> Move:
    valid_moves = []

    for i in range(board.size):
        for j in range(board.size):
            if board.tiles[i][j].colour is None:
                valid_moves.append((i, j))

    return Move(*random.choice(valid_moves))
