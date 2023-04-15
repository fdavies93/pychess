from enum import IntEnum, auto
from copy import deepcopy
from typing import Union
from os import system

class PIECE_ID(IntEnum):
    king = 0
    queen = 1
    rook = 2
    bishop = 3
    knight = 4
    pawn = 5

class CHAR_ID(IntEnum):
    white_space = auto()
    black_space = auto()

piece_info = {
    PIECE_ID.king: "King",
    PIECE_ID.queen: "Queen",
    PIECE_ID.rook: "Rook",
    PIECE_ID.bishop: "Bishop",
    PIECE_ID.knight: "Knight",
    PIECE_ID.pawn: "Pawn"
}

def get_unicode_char(piece_id : PIECE_ID, isBlack : bool, darkmode : bool = False):
    modifier = 0
    if (darkmode and not isBlack) or (not darkmode and isBlack):
        modifier = 6
    return chr(0x2654 + piece_id + modifier)

def file_to_letter(file : int):
    if file > 7 or file < 0:
        raise ValueError("Only files between 0 and 7 are valid.")
    return chr(65 + file)

def letter_to_file(letter : str):
    file = ord(letter) - 65
    if file > 7 or file < 0:
        raise ValueError("Only files between 0 and 7 are valid.")
    return file

def coord_to_position(rank : int, file : int) -> str:
    return file_to_letter(file) + str(rank + 1)

def position_to_coord(position : str):
    return (letter_to_file(position[0]), int(position[1]) - 1)

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
            positions[coord_to_position(piece.rank, piece.file)] = piece
        return positions

class PositionRenderer:

    def __init__(self, chars = None, darkmode = False):
        # default to light mode
        self.darkmode = darkmode
        self.chars = dict()
        if darkmode:
            self.chars[CHAR_ID.white_space] = "█"
            self.chars[CHAR_ID.black_space] = " "
        else:
            self.chars[CHAR_ID.white_space] = " "
            self.chars[CHAR_ID.black_space] = "█"

    def render(self, position : Position, reversed : bool = False):
        board = ""
        positions = position.get_piece_positions()
        back_range = range(7,-1,-1)
        forward_range = range(0, 8, 1)
        for file in (forward_range if not reversed else back_range):
            board += ' ' + file_to_letter(file)
        board += "\n"
        for rank in (back_range if not reversed else forward_range):
            board += str(rank+1)
            for file in (forward_range if not reversed else back_range):
                # black space
                back = self.chars[CHAR_ID.black_space]
                if (rank + file) % 2 == 1:
                    # white space
                    back = self.chars[CHAR_ID.white_space]
                coord = coord_to_position(rank, file) 
                if coord in positions:
                    piece = positions[coord]
                    board += get_unicode_char(piece.piece_id, piece.is_black, self.darkmode) + ' '
                else:
                    board += back * 2
            board += "\n"
        return board


class MoveStrategyChecker():

    @classmethod
    def check_move(cls, piece : Piece, end_position : str) -> bool:
        end_coords = position_to_coord(end_position)
        strategies = {
            PIECE_ID.pawn : cls.check_pawn_move,
            PIECE_ID.knight : cls.check_knight_move,
            PIECE_ID.king: cls.check_king_move,
            PIECE_ID.bishop: cls.check_bishop_move,
            PIECE_ID.queen: cls.check_queen_move,
            PIECE_ID.rook: cls.check_rook_move
        }
        if end_coords[0] > 7 or end_coords[0] < 0 or end_coords[1] > 7 or end_coords[1] < 0:
            return False
        return strategies[piece.piece_id](piece, end_coords)

    @classmethod
    def check_pawn_move(cls, piece : Piece, end_coords : tuple[int,int]):
        if ((end_coords[1] > piece.rank - 1) and piece.is_black) or ((end_coords[1] < piece.rank + 1) and not piece.is_black):
            # trying to move less than 1 space forward
            print("Tried to move less than 1 square forward.")
            return False
        if abs(end_coords[0] - piece.file) > 1:
            # trying to move more than 1 square to the side
            print("Tried to move too far sideways.")
            return False
        if ((piece.rank != 1 and not piece.is_black) or (piece.rank != 6 and piece.is_black)) and (abs(piece.rank - end_coords[1]) > 1):
            # trying to move 2 when it's not first turn
            print("Tried to move 2 squares when it's not this pawn's first move.")
            return False
        if abs(end_coords[0] - piece.file) > 0 and abs(end_coords[1] - piece.rank) > 1:
            # trying to move 2 forward and 1 sideways (like a knight)
            print("Tried to move like a knight.")
            return False
        if (abs(piece.rank - end_coords[1]) > 2):
            # trying to move more than 2, ever
            print("Tried to move more than 2 squares forward.")
            return False
        return True
    
    @classmethod
    def check_knight_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not (x_move == 1 and y_move == 2) or (x_move == 2 and y_move == 1):
            return False
        return True
    
    @classmethod
    def check_bishop_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not x_move == y_move:
            print("Bishops must move diagonally.")
            return False
        if x_move == 0 and y_move == 0:
            print("Bishop must move.")
            return False
        return True

    @classmethod
    def check_rook_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not (x_move == 0 and y_move > 0) or (x_move > 0 and y_move == 0):
            print("Rooks must move along a rank or file.")
            return False
        return True
    
    @classmethod
    def check_queen_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not (x_move == 0 and y_move > 0) or (x_move > 0 and y_move == 0) or x_move == y_move:
            print("Queens must move along a rank or file or diagonally.")
            return False
        if x_move == 0 and y_move == 0:
            print("Queen must move.")
            return False
        return True
    
    @classmethod
    def check_king_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if x_move > 1 and y_move > 1:
            print("King can only move one space.")
            return False
        if not (x_move == 0 and y_move > 0) or (x_move > 0 and y_move == 0) or x_move == y_move:
            print("Kings must move along a rank or file or diagonally.")
            return False
        if x_move == 0 and y_move == 0:
            print("King must move.")
            return False
        return True

class PieceChecker():
    
    @classmethod
    def check_move(cls, board : Position, piece : Piece, end_position : str, black_to_move : bool):
        end_coords = position_to_coord(end_position)
        strategies = {
            PIECE_ID.pawn : cls.check_pawn_move,
            PIECE_ID.knight : cls.check_knight_move,
            PIECE_ID.king: cls.check_bqkr_move,
            PIECE_ID.bishop: cls.check_bqkr_move,
            PIECE_ID.queen: cls.check_bqkr_move,
            PIECE_ID.rook: cls.check_bqkr_move
        }
        return strategies[piece.piece_id](board, piece, end_coords, black_to_move)

    @classmethod 
    def check_endpoint(cls, board : Position, piece : Piece, end_position : tuple[int, int], black_to_move : bool):    
        positions = board.get_piece_positions()
        at_endpoint = positions.get(coord_to_position(end_position[1], end_position[0]))
        if at_endpoint != None and at_endpoint.is_black == black_to_move:
            print("Can't move onto your own piece.")
            return False
        return True

    @classmethod
    def check_obstacles(cls, board : Position, piece : Piece, end_coords : tuple[int, int], black_to_move : bool):    
        x_move = end_coords[0] - piece.file
        y_move = end_coords[1] - piece.rank
        x_increment = int(x_move / abs(x_move))
        y_increment = int(y_move / abs(y_move))
        print(f"({x_increment},{y_increment})")
        cur_x = piece.file + x_increment # start from next space to move
        cur_y = piece.rank + y_increment
        positions = board.get_piece_positions()
        # ends BEFORE endpoint as this is a separate check
        while cur_x != end_coords[0] and cur_y != end_coords[1]:
            position = coord_to_position(cur_y, cur_x)
            at_position = positions.get(position)
            if at_position != None:
                print("There is a piece in the way of making this move.")
                return False
            cur_x += x_increment
            cur_y += y_increment
        return True

    # en passant not yet implemented
    @classmethod
    def check_pawn_move(cls, board : Position, piece : Piece, end_coords : tuple[int, int], black_to_move : bool):
        positions = board.get_piece_positions()
        at_endpoint = positions.get(coord_to_position(end_coords[1], end_coords[0]))
        if abs(end_coords[0] - piece.file) == 1 and (at_endpoint == None or at_endpoint.is_black == black_to_move):
            # must be capturing to move diagonally
            # and can't capture own piece
            print("You can't move diagonally unless you're capturing, and can't capture your own piece.")
            return False
        if not abs(end_coords[0] - piece.file) == 1 and at_endpoint != None:
            # can only capture diagonally or something is in our way
            print("You can only capture diagonally.")
            return False
        if abs(end_coords[1] - piece.rank) == 2:
            if end_coords[1] < piece.rank:
                to_check = positions.get( coord_to_position(piece.rank - 1, piece.file) )
            else:
                to_check = positions.get( coord_to_position(piece.rank + 1, piece.file) )
            if to_check != None:
                # there's something in the way of moving to that spot
                return False
        return True
    
    @classmethod
    def check_knight_move(cls, board : Position, piece : Piece, end_coords : tuple[int, int], black_to_move : bool):    
        if not cls.check_endpoint(board, piece, end_coords, black_to_move):
            return False
        return True

    # logic for rooks, queens, and bishops is identical: these pieces have no special rules
    # we also need to check obstacles for king in case of castling
    @classmethod
    def check_bqkr_move(cls, board : Position, piece : Piece, end_coords : tuple[int, int], black_to_move : bool):    
        if not cls.check_obstacles(board, piece, end_coords, black_to_move):
            return False
        if not cls.check_endpoint(board, piece, end_coords, black_to_move):
            return False
        return True

    

class Game():
    def __init__(self, renderer : Union[PositionRenderer, None] = None):
        self.renderer = renderer
        if renderer is None:
            self.renderer = PositionRenderer()
        self.setup()

    @classmethod
    def new_position_from_move(self, prev_position : Position, start_position : str, end_position : str) -> Position:
        new_position = deepcopy(prev_position)
        end_coords = position_to_coord(end_position)
        new_pieces = []
        # indirectly, remove the piece that we're capturing
        for piece in new_position.pieces:
            if piece.file != end_coords[0] or piece.rank != end_coords[1]:
                new_pieces.append(piece)
            else:
                # some kind of behaviour to indicate capture
                pass
        new_position.pieces = new_pieces
        piece_positions = new_position.get_piece_positions()
        piece = piece_positions.get(start_position)
        piece.file, piece.rank = end_coords
        return new_position
    
    def try_move(self, start_position : str, end_position : str):
        valid = Game.check_move(self.current_position, start_position, end_position, self.black_to_move)
        if not valid:
            return
        self.current_position = Game.new_position_from_move(self.current_position, start_position, end_position)
        self.black_to_move = not self.black_to_move

    @classmethod
    def check_move(cls, board : Position, start_position : str, end_position : str, black_to_move : bool):
        piece_positions = board.get_piece_positions()
        piece = piece_positions.get(start_position)
        # check that there's a piece where we want to move
        if piece is None:
            print("There's no piece in that square.")
            return False
        # check that the piece belongs to us
        if piece.is_black != black_to_move:
            print("This is not your piece to move.")
            return False
        # check that the move's not invalid for the piece
        if not MoveStrategyChecker.check_move(piece, end_position):
            print("That's not a valid move for that piece.")
            return False
        # check that there's no obstructions for the move
        if not PieceChecker.check_move(board, piece, end_position, black_to_move):
            return False
        # check that the move doesn't reveal check for player moving
        return True

    def setup(self):
        self.current_position = self.start_position()
        self.black_to_move = False

    def render(self):
        if self.black_to_move:
            print("Black's move.")
        else:
            print("White's move.")

        print(self.renderer.render(self.current_position))

    @classmethod
    def start_position(cls):
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

renderer = PositionRenderer(darkmode=True)
game = Game(renderer)
# game.render()

while True:
    game.render()
    move = input('> ')
    move_split = move.split(" ")
    game.try_move(move_split[0], move_split[1])
