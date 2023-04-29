from enum import IntEnum, auto
from copy import deepcopy
from typing import Union
from os import system
from time import sleep
import json
import argparse
import io

DEBUG = False

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

def d_print(string):
    if DEBUG:
        print(string)

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

def find_rook_position(is_black, end_position):
    # black kingside
    if is_black and end_position == "G8":
        return "H8"
    # black queenside
    elif is_black and end_position == "C8":
        return "A8"
    # white kingside
    elif not is_black and end_position == "G1":
        return "H1"
    # white queenside
    elif not is_black and end_position == "C1":
        return "A1"

class Piece:
    def __init__(self, piece_id: PIECE_ID, is_black : bool, rank : int = 0, file : int = 0):
        self.piece_id = piece_id
        self.is_black = is_black
        self.rank = rank
        self.file = file
        self.moved = False

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
            d_print("Tried to move less than 1 square forward.")
            return False
        if abs(end_coords[0] - piece.file) > 1:
            # trying to move more than 1 square to the side
            d_print("Tried to move too far sideways.")
            return False
        if ((piece.rank != 1 and not piece.is_black) or (piece.rank != 6 and piece.is_black)) and (abs(piece.rank - end_coords[1]) > 1):
            # trying to move 2 when it's not first turn
            d_print("Tried to move 2 squares when it's not this pawn's first move.")
            return False
        if abs(end_coords[0] - piece.file) > 0 and abs(end_coords[1] - piece.rank) > 1:
            # trying to move 2 forward and 1 sideways (like a knight)
            d_print("Tried to move like a knight.")
            return False
        if (abs(piece.rank - end_coords[1]) > 2):
            # trying to move more than 2, ever
            d_print("Tried to move more than 2 squares forward.")
            return False
        return True
    
    @classmethod
    def check_knight_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not ((x_move == 1 and y_move == 2) or (x_move == 2 and y_move == 1)):
            return False
        return True
    
    @classmethod
    def check_bishop_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not x_move == y_move:
            d_print("Bishops must move diagonally.")
            return False
        if x_move == 0 and y_move == 0:
            d_print("Bishop must move.")
            return False
        return True

    @classmethod
    def check_rook_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not (x_move == 0 and y_move > 0) or (x_move > 0 and y_move == 0):
            d_print("Rooks must move along a rank or file.")
            return False
        return True
    
    @classmethod
    def check_queen_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if not ((x_move == 0 and y_move > 0) or (x_move > 0 and y_move == 0) or (x_move == y_move)):
            d_print(f"{x_move},{y_move}")
            d_print("Queens must move along a rank or file or diagonally.")
            return False
        if x_move == 0 and y_move == 0:
            d_print("Queen must move.")
            return False
        return True
    
    @classmethod
    def check_king_move(cls, piece : Piece, end_coords : tuple[int,int]):
        x_move = abs(piece.file - end_coords[0])
        y_move = abs(piece.rank - end_coords[1])
        if x_move > 2 or y_move > 1:
            d_print("King can only move one space.")
            return False
        if not ((x_move == 0 and y_move > 0) or (x_move > 0 and y_move == 0) or x_move == y_move):
            d_print("Kings must move along a rank or file or diagonally.")
            return False
        if x_move == 0 and y_move == 0:
            d_print("King must move.")
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
            d_print("Can't move onto your own piece.")
            return False
        return True

    @classmethod
    def check_obstacles(cls, board : Position, piece : Piece, end_coords : tuple[int, int], black_to_move : bool):    
        x_move = end_coords[0] - piece.file
        y_move = end_coords[1] - piece.rank
        x_increment = int(x_move / abs(x_move)) if x_move != 0 else 0
        y_increment = int(y_move / abs(y_move)) if y_move != 0 else 0
        cur_x = piece.file + x_increment # start from next space to move
        cur_y = piece.rank + y_increment
        positions = board.get_piece_positions()
        # ends BEFORE endpoint as this is a separate check
        while not (cur_x == end_coords[0] and cur_y == end_coords[1]):
            position = coord_to_position(cur_y, cur_x)
            at_position = positions.get(position)
            if at_position != None:
                d_print("There is a piece in the way of making this move.")
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
            d_print("You can't move diagonally unless you're capturing, and can't capture your own piece.")
            return False
        if not abs(end_coords[0] - piece.file) == 1 and at_endpoint != None:
            # can only capture diagonally or something is in our way
            d_print("You can only capture diagonally.")
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
    
    @classmethod
    def check_castling(cls, position : Position, start_position : str, end_position : str, black_to_move : bool):
        piece_positions = position.get_piece_positions()
        piece = piece_positions.get(start_position)
        
        # if we're not moving a king
        if not piece.piece_id == PIECE_ID.king: return True
        
        start_coords = position_to_coord(start_position)
        end_coords = position_to_coord(end_position)
        x_diff = end_coords[0] - start_coords[0]
        # if you're not trying to castle
        if abs(x_diff) != 2: return True
        if piece.moved: return False

        mid = coord_to_position(end_coords[1], end_coords[0] + int(x_diff / 2))
        # if player is attempting to castle through check
        # we don't check for endpoint or obstacles because those are already handled by separate, generic checks
        if CheckChecker.check_can_attack(position, not black_to_move, mid): return False

        rook_position = find_rook_position(piece.is_black, end_position)
        rook = piece_positions.get(rook_position)
        if rook != None and rook.piece_id == PIECE_ID.rook and not rook.moved:
            return True

        return False

class CheckChecker:
    @classmethod
    def check_can_attack(cls, board : Position, team_is_black : bool, to_attack : str):
        pieces = [piece for piece in board.pieces if piece.is_black == team_is_black]
        for piece in pieces:
            # if any piece can attack the space, the space can be attacked
            # if piece.piece_id == PIECE_ID.king:
            #     # no pawns in pieces? O.o
            #     print(f"Bishop can attack: {MoveStrategyChecker.check_move(piece, to_attack)}")
            if MoveStrategyChecker.check_move(piece, to_attack) and PieceChecker.check_move(board, piece, to_attack, team_is_black):
                d_print("A piece can give check to king.")
                return True
        return False  

    # tuple stores [is black in check? is white in check?]
    @classmethod
    def check_check(cls, board : Position) -> tuple[bool, bool]:
        black_king = None
        white_king = None
        # get black king and white king
        for piece in board.pieces:
            if piece.piece_id == PIECE_ID.king:
                if piece.is_black:
                    black_king = piece
                else:
                    white_king = piece
                if black_king is not None and white_king is not None:
                    break

        black_position = coord_to_position(black_king.rank, black_king.file)
        d_print(f"Black King position is {black_position}")
        white_position = coord_to_position(white_king.rank, white_king.file)
        d_print(f"White King position is {white_position}")

        return (
            cls.check_can_attack(board, False, black_position),
            cls.check_can_attack(board, True, white_position)
        )
    
class MoveMaker():
    @classmethod
    def make_possible_moves(cls, position : Position, piece : Piece):
        strategies = {
            PIECE_ID.pawn: cls.make_pawn_move,
            PIECE_ID.king: cls.make_king_move,
            PIECE_ID.queen: cls.make_queen_move,
            PIECE_ID.rook: cls.make_rook_move,
            PIECE_ID.bishop: cls.make_bishop_move,
            PIECE_ID.knight: cls.make_knight_move
        }
        return strategies[piece.piece_id](piece)
    
    @classmethod
    def make_pawn_move(cls, piece : Piece):
        forward = -1 if piece.is_black else 1
        start_position = coord_to_position(piece.rank, piece.file)
        moves = []
        cases = [ (forward, 0), (forward * 2, 0), (forward, 1), (forward, -1) ]
        for case in cases:
            end_coord = (piece.rank + case[0], piece.file + case[1])
            if end_coord[0] >= 0 and end_coord[0] < 8 and end_coord[1] >= 0 and end_coord[1] < 8:
                end_position = coord_to_position(end_coord[0], end_coord[1])
                moves.append((start_position, end_position))
        return moves

    @classmethod
    def make_king_move(cls, piece : Piece):
        moves = []
        start_position = coord_to_position(piece.rank, piece.file)
        for x_move in range(-2, 3): # account for castling
            for y_move in range(-1, 2):
                if x_move == 0 and y_move == 0:
                    continue
                final_y = piece.rank + y_move
                final_x = piece.file + x_move
                if final_x > 7 or final_x < 0 or final_y > 7 or final_y < 0:
                    continue
                end_position = coord_to_position(final_y, final_x)
                moves.append((start_position, end_position))
        return moves

    @classmethod
    def make_queen_move(cls, piece):
        moves = []
        moves.extend(cls.make_rook_move(piece))
        moves.extend(cls.make_bishop_move(piece))
        return moves

    @classmethod
    def make_rook_move(cls, piece : Piece):
        moves = []
        start_position = coord_to_position(piece.rank, piece.file)
        for x_move in range(8):
            end_position = coord_to_position(piece.rank, x_move)
            moves.append((start_position, end_position))
        for y_move in range(8):
            end_position = coord_to_position(y_move, piece.file)
        return moves

    @classmethod
    def make_bishop_move(cls, piece : Piece):
        moves = []
        start_position = coord_to_position(piece.rank, piece.file)
        for distance in range(1,8):
            # down-right (+,+)
            if piece.rank + distance < 8 and piece.file + distance < 8:
                end_position = coord_to_position(piece.rank + distance, piece.file + distance)
                moves.append((start_position, end_position))
            # down-left (-,+)
            if piece.rank + distance < 8 and piece.file - distance >= 0:
                end_position = coord_to_position(piece.rank + distance, piece.file - distance)
                moves.append((start_position, end_position))
            # up-right (+,-)
            if piece.rank - distance >= 0 and piece.file + distance < 8:
                end_position = coord_to_position(piece.rank - distance, piece.file + distance)
                moves.append((start_position, end_position))
            # up-left (-,-)
            if piece.rank - distance >= 0 and piece.file - distance >= 0:
                end_position = coord_to_position(piece.rank - distance, piece.file - distance)
                moves.append((start_position, end_position))
        return moves

    @classmethod
    def make_knight_move(cls, piece : Piece):
        # cases: x = 2, y = 1; y = 2, x = 1 and abs equivalents
        moves = []
        start_position = coord_to_position(piece.rank, piece.file)
        cases : list[tuple[int]] = [ (1,2), (2,1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-2, -1), (-1, -2) ]
        for case in cases:
            end_coord = (piece.rank + case[0], piece.file + case[1])
            if end_coord[0] >= 0 and end_coord[0] < 8 and end_coord[1] >= 0 and end_coord[1] < 8:
                end_position = coord_to_position(end_coord[0], end_coord[1])
                moves.append((start_position, end_position))
        return moves

class Game():
    def __init__(self, renderer : Union[PositionRenderer, None] = None, pawn_choice = None):
        self.renderer = renderer
        self.prev_moves = []
        self.king_moved = [False, False]
        if renderer is None:
            self.renderer = PositionRenderer()
        self.setup()
        self.pawn_choice = pawn_choice

    @classmethod
    def new_position_from_move(self, prev_position : Position, start_position : str, end_position : str, make_pawn_choice : callable) -> Position:
        new_position = deepcopy(prev_position)
        start_coords = position_to_coord(start_position)
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
        # check for castling as we then need to move *two* pieces
        # if it's an invalid castle it should have been dealt with long ago
        if piece.piece_id == PIECE_ID.king and abs(start_coords[0] - end_coords[0]) == 2:
            rook_position = find_rook_position(piece.is_black,end_position)
            rook = piece_positions.get(rook_position)
            if rook.file == 0: rook.file = 3
            elif rook.file == 7: rook.file = 5
            rook.moved = True
        # spicy logic here but as pawns can't go backwards, should be fine
        elif piece.piece_id == PIECE_ID.pawn and (end_coords[1] == 7 or end_coords[1] == 0):
            pawn_choice : int = make_pawn_choice()
            piece.piece_id = pawn_choice

        piece.file, piece.rank = end_coords
        piece.moved = True
        return new_position
    
    @classmethod
    def always_promote_queen(cls):
        return PIECE_ID.queen
    # generates all possible possitions for current player to move to
    # helpful for AI
    # if this returns 0 positions, it means that the player whose turn it is has been mated
    @classmethod
    def generate_next_positions(cls, position : Position, black_to_move : bool):
        pieces : list[Piece] = position.pieces
        pieces_to_move = filter(lambda piece : piece.is_black == black_to_move, pieces)
        moves = []
        for piece in pieces_to_move:
            moves.extend(MoveMaker.make_possible_moves(position, piece))
        valid_moves = filter(lambda move : cls.check_move(position, move[0], move[1], black_to_move), moves)
        next_positions = []
        for move in valid_moves:
            next_positions.append(cls.new_position_from_move(position, move[0], move[1], cls.always_promote_queen))
        return next_positions

    def try_move(self, start_position : str, end_position : str):
        valid = Game.check_move(self.current_position, start_position, end_position, self.black_to_move)
        if not valid:
            return
        self.current_position = Game.new_position_from_move(self.current_position, start_position, end_position, self.pawn_choice)
        self.prev_moves.append(f"{start_position} {end_position}")
        checks = CheckChecker.check_check(self.current_position)
        if checks[0] or checks[1]:
            team = "Black" if checks[0] else "White"
            print(f"{team} is in check!")
        # for checkmate, need to generate all possible next moves for defending team and see if any escape check
        self.black_to_move = not self.black_to_move
        

    @classmethod
    def check_move(cls, board : Position, start_position : str, end_position : str, black_to_move : bool):
        piece_positions = board.get_piece_positions()
        piece = piece_positions.get(start_position)
        # check that there's a piece where we want to move
        if piece is None:
            d_print("There's no piece in that square.")
            return False
        # check that the piece belongs to us
        if piece.is_black != black_to_move:
            d_print("This is not your piece to move.")
            return False
        # check that the move's not invalid for the piece
        if not MoveStrategyChecker.check_move(piece, end_position):
            d_print("That's not a valid move for that piece.")
            return False
        # check that there's no obstructions for the move
        if not PieceChecker.check_move(board, piece, end_position, black_to_move):
            d_print("This move is obstructed by another piece.")
            return False
        if piece.piece_id == PIECE_ID.king:
            if not PieceChecker.check_castling(board, start_position, end_position, black_to_move):
                return False
        # check that the move doesn't reveal or maintain check for player moving
        new_position = Game.new_position_from_move(board, start_position, end_position, cls.always_promote_queen)
        in_check = CheckChecker.check_check(new_position)
        # reversed because black_to_move is the PREVIOUS state of the board
        if (black_to_move and in_check[0]) or (not black_to_move and in_check[1]):
            d_print("This move would reveal or maintain check against your king!")
            return False
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


def pawn_choice():
    choice = -1
    valid = [PIECE_ID.bishop, PIECE_ID.rook, PIECE_ID.knight, PIECE_ID.queen]
    while choice not in valid:
        print("Choose a piece to promote your pawn to")
        for c in valid:
            print(f"{c} - {piece_info[c]}")
        choice = int(input("> "))
    return choice


def main():
    parser = argparse.ArgumentParser(description="Python Chess game.")
    parser.add_argument('--store', help="Store the list of moves at the given path.")
    parser.add_argument('--load', help="Load the list of moves at the given path.")
    args = vars(parser.parse_args())

    renderer = PositionRenderer(darkmode=True)
    game = Game(renderer, pawn_choice)

    # normal start
    preprocess_list = []

    store_path = args.get("store")
    load_path = args.get("load")
    if load_path != None:
        with open(load_path,  "r") as f:
            all_lines = "\n".join(f.readlines())
            preprocess_list = json.loads(all_lines)

    for move in preprocess_list:
        move_split = move.split(" ")
        game.try_move(move_split[0], move_split[1])

    while True:
        game.render()

        next_moves = Game.generate_next_positions(game.current_position, game.black_to_move)
        checks = CheckChecker.check_check(game.current_position)
        if len(next_moves) == 0:
            if checks[0] or checks[1]:
                team = "Black" if checks[0] else "White"
                print(f"{team} has been mated! Wait 5s to restart.")
                sleep(5)
                game.setup()
                game.render()

        move = input('> ')
        if move in ["quit", "exit", "q"]:
            break
        move_split = move.upper().split(" ")

        if len(move_split) == 2:
            game.try_move(move_split[0], move_split[1])
        
        # store after each move
        if store_path != None:
            with open(store_path, "w") as f:
                json.dump(game.prev_moves, f)

if __name__ == "__main__":
    main()