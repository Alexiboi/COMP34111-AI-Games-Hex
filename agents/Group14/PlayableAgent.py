from random import choice

from agents.Group14.MyAgentTerminal import MyAgentTerminal
from agents.TestAgents.utils import make_valid_move
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move


class PlayableAgent(AgentBase):
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.

    The class inherits from AgentBase, which is an abstract class.
    The AgentBase contains the colour property which you can use to get the agent's colour.
    You must implement the make_move method to make the agent functional.
    You CANNOT modify the AgentBase class, otherwise your agent might not function.
    """

    _agent : AgentBase
    _simulate : int = 0
    
    def __init__(self, colour: Colour):
        self._agent = MyAgentTerminal(colour)

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
        
        
        if self._simulate > 0:
            self._simulate -= 1
            return self._agent.make_move(turn, board, opp_move)
        
        move = input("enter your move in this format: x,y. For example if input == 5,3 then move is x=5, y=3, to simlate to sim20: ")
        
        if "sim" in move:
            self._simulate = int(move.strip().split("im")[1])
            return self._agent.make_move(turn, board, opp_move)
            
        x_coord, y_coord = move.strip().split(",")
        
        return Move(_x = int(x_coord), _y = int(y_coord))
