#from random import choice, random
import random
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move
#from . import Node
from ..Group14.Node import Node

class MyAgent_Ale(AgentBase):
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.

    The class inherits from AgentBase, which is an abstract class.
    The AgentBase contains the colour property which you can use to get the agent's colour.
    You must implement the make_move method to make the agent functional.
    You CANNOT modify the AgentBase class, otherwise your agent might not function.
    """
    _iterations: int = 100
    _choices: list[Move]
    _board_size: int = 11

    def __init__(self, colour: Colour):
        super().__init__(colour)
        self._choices = [
            (i, j) for i in range(self._board_size) for j in range(self._board_size)
        ]
        
        self.legal_moves_count = self._board_size * self._board_size


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
        #SWAP i guess
        if turn == 1:
            pass

        #Remove moves made by other player
        if opp_move is not None:
            coord = opp_move._x, opp_move._y 
            if coord in self._choices:
                self._choices.remove(coord)
                self.legal_moves_count -= 1

        #Find best move
        best_move = self.MCTS(self._choices,board)
        
        #Remove moves made by agent
        self._choices.remove(best_move)
        best_move = Move(_x = best_move[0], _y = best_move[1])
        return best_move
    

    def MCTS(self,choices,board):
        root = Node(self.copy_board(board),self.colour, choices, move=None,parent=None)
        for i in range(5000):
            node = root
            board_state = self.copy_board(board)

            #SELECTION
            #Check all untried nodes and node is non-terminal
            while node.untried_moves == [] and node.child_nodes:
                child = node.best_child()
                move = child.move
                board_state.set_tile_colour(move[0], move[1], node.colour)  # Use parent node's colour
                node = child
            
        
            #EXPANSION
            #Add an extra child
            if node.untried_moves:
                move = random.choice(node.untried_moves)
                #next_colour = self.opp_colour()
                next_colour = Colour.BLUE if node.colour == Colour.RED else Colour.RED
                #print(f"next colour: {next_colour}")
                board_state.set_tile_colour(move[0], move[1], node.colour)
                child = node.expand(self.copy_board(board_state), next_colour, move)
                node = child
            

            #SIMULATION

            rollout_colour = node.colour             
             # --- FIX: Generate all possible moves, remove those already played ---
            all_possible_moves = [(x, y) for x in range(board.size) for y in range(board.size)]
            played_moves = [
                (x, y)
                for x in range(board.size)
                for y in range(board.size)
                if board_state.tiles[x][y].colour != None
            ]
            rollout_moves = [move for move in all_possible_moves if move not in played_moves]

            random.shuffle(rollout_moves)
            for legal_move in rollout_moves:
                board_state.set_tile_colour(legal_move[0], legal_move[1], rollout_colour) #Colour random legal move

                rollout_colour = Colour.RED if rollout_colour == Colour.BLUE else Colour.BLUE
                
               

            #BACKPROPAGATION
            # has_ended updates the board_state.winner in the method so they need to be called
            # Could be more efficient
            if board_state.has_ended(Colour.RED):
                # print(f"game ended winner is {board_state.get_winner()}")
                pass  
            elif board_state.has_ended(Colour.BLUE):
                #print(f"game ended winner is {board_state.get_winner()}")
                pass
            else:
                #print(f"game ended winner is {board_state.get_winner()}") 
                pass
            winner = board_state.get_winner()
            
            
            node.backpropagation(winner)
          
        best_child = max(root.child_nodes, key=lambda c: c.visits)
        return best_child.move
            
# Helper class to view game tree for debugging
def print_tree(node, depth=0):
    print("  " * depth + f"Move: {node.move}, Wins: {node.wins}, Visits: {node.visits}")
    for child in getattr(node, "child_nodes", []):
        print_tree(child, depth + 1)