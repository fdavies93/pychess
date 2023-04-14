from enum import IntEnum
from copy import deepcopy

class PIECE_ID(IntEnum):
    king = 0
    queen = 1
    rook = 2
    bishop = 3
    knight = 4
    pawn = 5

piece_info = {
    PIECE_ID.king: "King",
    PIECE_ID.queen: "Queen",
    PIECE_ID.rook: "Rook",
    PIECE_ID.bishop: "Bishop",
    PIECE_ID.knight: "Knight",
    PIECE_ID.pawn: "Pawn"
}

def get_unicode_char(piece_id : PIECE_ID, isBlack : bool):
    return chr(0x2654 + piece_id + (6 if isBlack else 0))

def file_to_letter(file : int):
    if file > 7 or file < 0:
        raise ValueError("Only files between 0 and 7 are valid.")
    return chr(65 + file)

def position_to_cood(rank : int, file : int) -> str:
    return file_to_letter(file) + str(rank + 1)

class Piece:
    def __init__(self, piece_id: PIECE_ID, is_black : bool, rank : int = 0, file : int = 0):
        self.piece_id = piece_id
        self.is_black = is_black
        self.rank = rank
        self.file = file

class Position:
    def __init__(self, pieces : list[Piece]):
        self.pieces = deepcopy(pieces)
    
    def get_piece_positions(self) -> dict[str, Piece]:
        positions = dict()
        for piece in self.pieces:
            positions[position_to_cood(piece.rank, piece.file)] = piece
        return positions

    def render(self, reversed : bool = False):
        board = ""
        positions = self.get_piece_positions()
        back_range = range(7,-1,-1)
        forward_range = range(0, 8, 1)
        for file in (forward_range if not reversed else back_range):
            board += ' ' + file_to_letter(file)
        board += "\n"
        for rank in (back_range if not reversed else forward_range):
            board += str(rank+1)
            for file in (forward_range if not reversed else back_range):
                back = "█"
                if (rank + file) % 2 == 1:
                    back = " "
                coord = position_to_cood(rank, file) 
                if coord in positions:
                    piece = positions[coord]
                    board += get_unicode_char(piece.piece_id, piece.is_black) + ' '
                else:
                    board += back * 2
            board += "\n"
        return board

test = Position([Piece(PIECE_ID.pawn, False), Piece(PIECE_ID.pawn, True, 0, 1)])

def start_position():
    pieces = [
        Piece(PIECE_ID.rook, False, file=0),
        Piece(PIECE_ID.knight, False, file=1),
        Piece(PIECE_ID.bishop, False, file=2),
        Piece(PIECE_ID.queen, False, file=3),
        Piece(PIECE_ID.king, False, file=4),
        Piece(PIECE_ID.bishop, False, file=5),
        Piece(PIECE_ID.knight, False, file=6),
        Piece(PIECE_ID.rook, False, file=7),
        Piece(PIECE_ID.rook, True, file=0, rank=7),
        Piece(PIECE_ID.knight, True, file=1, rank=7),
        Piece(PIECE_ID.bishop, True, file=2, rank=7),
        Piece(PIECE_ID.queen, True, file=3, rank=7),
        Piece(PIECE_ID.king, True, file=4, rank=7),
        Piece(PIECE_ID.bishop, True, file=5, rank=7),
        Piece(PIECE_ID.knight, True, file=6, rank=7),
        Piece(PIECE_ID.rook, True, file=7, rank=7)
    ]
    for i in range(8):
        pieces.append(Piece(PIECE_ID.pawn, False, file=i, rank=1))
        pieces.append(Piece(PIECE_ID.pawn, True, file=i, rank=6))
    return Position(pieces)

print(start_position().render(True))