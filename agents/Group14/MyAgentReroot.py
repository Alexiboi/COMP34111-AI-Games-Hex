#from random import choice, random
import random
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move
#from . import Node
from .Node import Node

class MyAgentReroot(AgentBase):
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.

    The class inherits from AgentBase, which is an abstract class.
    The AgentBase contains the colour property which you can use to get the agent's colour.
    You must implement the make_move method to make the agent functional.
    You CANNOT modify the AgentBase class, otherwise your agent might not function.
    """
    _iterations: int = 300
    _choices: list[Move]
    _board_size: int = 11
    virtual_bridges = []
    _root: Node | None
    
    #All moves that should be swapped on turn 2
    swappable_moves = [
        Move(5, 5),
        Move(4, 5),
        Move(6, 5),
        Move(5, 4),
        Move(5, 6),
        Move(4, 6),
        Move(6, 4),
    ]


    def __init__(self, colour: Colour):
        super().__init__(colour)
        self._choices = [
            (i, j) for i in range(self._board_size) for j in range(self._board_size)
        ]
        self._hexes = self._board_size * self._board_size
        self._root = None

        
        


    #COPY BOARD THROUGH AGENT, move if it is allowed to copy board through Board
    def copy_board(self, board: Board) -> Board:
        new_board = Board(board.size)

        for x in range(board.size):
            for y in range(board.size):
                new_board.set_tile_colour(x, y, board.tiles[x][y].colour)

        return new_board
    


    def make_move(self, turn: int, board: Board, opp_move: Move | None) -> Move:
        """The game engine will call this method to request a move from the agent.
        If the agent is to make the first move, opp_move will be None.
        If the opponent has made a move, opp_move will contain the opponent's move.
        If the opponent has made a swap move, opp_move will contain a Move object with x=-1 and y=-1,
        the game engine will also change your colour to the opponent colour.

        Args:
            turn (int): The current turn
            board (Board): The current board state
            opp_move (Move | None): The opponent's last move

        Returns:
            Move: The agent's move
        """
        print("MAKING MOVE")
        #SWAP
        if turn == 2:
            for move in self.swappable_moves:
                if move == opp_move:
                    return Move(-1, -1)

        #Remove moves made by other player
        if opp_move is not None:
            coord = opp_move._x, opp_move._y 
            if coord in self._choices:
                self._choices.remove(coord)


        empty_ratio = len(self._choices) / (self._hexes)
        if turn == 1:
            self._iterations = int(60000 / 4)

        elif turn <= 4:
            self._iterations = int(50000 / 4)

        elif turn <= 6:
            self._iterations = int(35000 / 4)

        elif turn <= 8:
            self._iterations = int(22500 / 4)

        elif turn <= 10:
            self._iterations = int(15000 / 4)

        else:

            if empty_ratio > 0.5:
                self._iterations = int(10000 / 4)
            elif empty_ratio > 0.35:
                self._iterations = int(6000 / 4)
            else:
                self._iterations = int(4000 / 4)
        
        self._iterations = int(self._iterations/2)        
        
        # Advance tree with opponent move (re-rooting)
        if opp_move is not None and self._root is not None:
            opp_coord = (opp_move._x, opp_move._y)

            for child in self._root.child_nodes:
                print((child.move.__str__(), opp_coord) )
                if child.move == opp_coord:
                    print("REROOTING...")
                    self._root = child
                    self._root.parent = None
                    break
            else:
                # Opponent move not explored → discard tree
                self._root = None

        
        #Find best move
        best_move = self.MCTS(self._choices,board)
        
        #Remove moves made by agent
        self._choices.remove(best_move)
        best_move = Move(_x = best_move[0], _y = best_move[1])
        return best_move
    

    def MCTS(self,choices,board):

        if self._root is None:
            print("Creating new root...")
            self._root = Node(
                self.copy_board(board),
                self.colour,
                choices,
                move=None,
                parent=None
            )

        root = self._root
        for i in range(self._iterations):
            node = root
            board_state = self.copy_board(board)

            #SELECTION
            #Check all untried nodes and node is non-terminal
            while node.untried_moves == [] and node.child_nodes:
                node = node.best_child()
                move = node.move
                board_state.set_tile_colour(move[0], move[1], node.colour)

            #EXPANSION
            #Add an extra child
            if node.untried_moves:
                move = random.choice(node.untried_moves)
                next_colour = self.opp_colour()
                board_state.set_tile_colour(move[0], move[1], node.colour)
                child = node.expand(self.copy_board(board_state), next_colour, move)
                node = child

            #SIMULATION
            rollout_colour = node.colour 
            rollout_moves = node.untried_moves[:]  # remaining legal moves

            random.shuffle(rollout_moves)

            for legal_move in rollout_moves:
                board_state.set_tile_colour(legal_move[0], legal_move[1], rollout_colour) #Colour random legal move
                rollout_colour = self.opp_colour()

                if board_state.has_ended(rollout_colour): #Check if game has ended
                    break

            #BACKPROPAGATION
            winner = board_state.get_winner()
            node.backpropagation(winner)

        if not root.child_nodes:
            # Fallback: no explored children
            return random.choice(choices)


        #Return most visited node
        best_child = max(root.child_nodes, key=lambda c: c.visits)
        self._root = best_child
        self._root.parent = None
        return best_child.move
            
    