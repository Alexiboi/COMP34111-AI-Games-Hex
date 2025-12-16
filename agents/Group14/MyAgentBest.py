#from random import choice, random
import random
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move
from .Node import Node

HEX_DIRS = [
    (-1, 0), (1, 0),
    (0, -1), (0, 1),
    (-1, 1), (1, -1)
]
safe_first_moves = [Move(0, 1), Move(0, 9), Move(10, 1), Move(10, 9)] 

class MyAgentBest(AgentBase):
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.

    The class inherits from AgentBase, which is an abstract class.
    The AgentBase contains the colour property which you can use to get the agent's colour.
    You must implement the make_move method to make the agent functional.
    You CANNOT modify the AgentBase class, otherwise your agent might not function.
    """
    _iterations: int = 1000
    _choices: list[Move]
    _board_size: int = 11
    virtual_bridges = []

    def __init__(self, colour: Colour):
        super().__init__(colour)
        self._choices = [
            Move(i, j) for i in range(self._board_size) for j in range(self._board_size)
        ]
        self._hexes = self._board_size * self._board_size
        self.virtual_bridges = []
        
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
        
        # TURN 1: we move first (opp_move is None by contract)
        if opp_move == None:
            safe_moves = [m for m in safe_first_moves if m in self._choices]
            move = random.choice(safe_moves)
            self._choices.remove(move)
            return move

        # Case 1: opponent played a normal move
        if opp_move is not None and opp_move._x != -1:
            if opp_move in self._choices:
                self._choices.remove(opp_move)

            # TURN 2 only: decide whether *we* should swap
            if turn == 2:
                ox, oy = opp_move._x, opp_move._y
                centre_min, centre_max = 3, 7

                is_central = (
                    centre_min <= ox <= centre_max and
                    centre_min <= oy <= centre_max
                )

                is_strong_edge = (
                    (ox in {0, self._board_size - 1} and centre_min <= oy <= centre_max) or
                    (oy in {0, self._board_size - 1} and centre_min <= ox <= centre_max)
                )

                if is_central or is_strong_edge:
                    return Move(-1, -1)
        
       
                
        forced_move = self.forced_move(board, self._choices, opp_move)
        
        if forced_move:
            return forced_move

                 
        
        #Find best move
        best_move = self.MCTS(self._choices,board)
        
        #Remove moves made by agent
        self._choices.remove(best_move)
        # update board for bridge detection
        board.set_tile_colour(best_move.x, best_move.y, self.colour)

        # check bridges using tuple
        self.check_virtual_bridges(board, best_move)

        # only now convert to Move
        return Move(_x=best_move.x, _y=best_move.y)
    

    def MCTS(self, choices: list[Move], board : Board):
        root = Node(self.copy_board(board),self.colour,choices, move=None,parent=None)
        for i in range(self._iterations):
            node = root
            board_state = self.copy_board(board)

            #SELECTION
            #Check all untried nodes and node is non-terminal
            while node.untried_moves == [] and node.child_nodes:
                node = node.best_child()
                move = node.move
                board_state.set_tile_colour(move.x, move.y, node.colour)

            #EXPANSION
            #Add an extra child
            if node.untried_moves:
                move = random.choice(node.untried_moves)
                next_colour = self.opp_colour()
                board_state.set_tile_colour(move.x, move.y, node.colour)
                child = node.expand(self.copy_board(board_state), next_colour, move)
                node = child

            #SIMULATION
            rollout_colour = node.colour 
            rollout_moves = node.untried_moves[:]  # remaining legal moves

            random.shuffle(rollout_moves)

            for legal_move in rollout_moves:
                board_state.set_tile_colour(legal_move.x, legal_move.y, rollout_colour) #Colour random legal move
                rollout_colour = self.opp_colour()

                if board_state.has_ended(rollout_colour): #Check if game has ended
                    break

            #BACKPROPAGATION
            winner = board_state.get_winner()
            node.backpropagation(winner)

        #Return most visited node
        best_child = max(root.child_nodes, key=lambda c: c.visits)
        return best_child.move
            
    
    
    def check_virtual_bridges(self, board: Board, our_move: Move):

        x, y = our_move.x, our_move.y
        colour = self.colour

        if board.tiles[x][y].colour != colour:
            return

        for dx1, dy1 in HEX_DIRS:
            for dx2, dy2 in HEX_DIRS:
                if (dx1, dy1) == (dx2, dy2):
                    continue

                tx = x + dx1 + dx2
                ty = y + dy1 + dy2


                if not (0 <= tx < self._board_size and 0 <= ty < self._board_size):
                    continue


                if board.tiles[tx][ty].colour != colour:
                    continue

                common = []
                nbrs_tx_ty = set(self.neighbours(tx, ty))

                for nx, ny in self.neighbours(x, y):

                    if (nx, ny) in nbrs_tx_ty:

                        if board.tiles[nx][ny].colour is None:
                            common.append(Move(nx, ny))


                if len(common) == 2:
                    print("  *** BRIDGE FOUND ***")

                    bridge = {
                        "ends": (Move(x, y), Move(tx, ty)),
                        "links": tuple(common)
                    }

                    if bridge not in self.virtual_bridges:
                        print("  -> Adding bridge")
                        self.virtual_bridges.append(bridge)


    def neighbours(self, x : int, y : int):
        for dx, dy in HEX_DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self._board_size and 0 <= ny < self._board_size:
                yield nx, ny

    def check_bridge_invasion(self, opp_move : Move) -> Move | None:

        ox, oy = opp_move._x, opp_move._y
        
        print("Virtual bridge length:", len(self.virtual_bridges))

        for bridge in self.virtual_bridges[:]:  # copy to allow removal
            
            
            l1, l2 = bridge["links"]
            
            if (ox, oy) == l1:
                self.virtual_bridges.remove(bridge)
                return l2

            if (ox, oy) == l2:
                self.virtual_bridges.remove(bridge)
                return l1
            


    def apply_terminal_protocol(self, board: Board, choices: list[Move]) -> Move | None:
        # 1) Immediate winning move
        for move in choices:
            b = self.copy_board(board)
            b.set_tile_colour(move.x, move.y, self.colour)
            if b.has_ended(self.colour):
                return move

        # 2) Immediate blocking move
        opp = self.opp_colour()
        for move in choices:
            b = self.copy_board(board)
            b.set_tile_colour(move.x, move.y, opp)
            if b.has_ended(opp):
                return move

        return None

    def forced_move(self, board : Board, choices : list[Move], opp_move : Move) -> Move | None:
        terminal_move = self.apply_terminal_protocol(board, choices)
        if terminal_move is not None:
            self._choices.remove(terminal_move)
            print("FOUND FORCED WIN...MOVING TO TAKE/BLOCK...")
            return Move(terminal_move.x, terminal_move.y)

        forced_move = self.check_bridge_invasion(opp_move)
        if forced_move and forced_move in self._choices:
            print("FOUND THREATENED BRIDGE...MOVING TO RETAIN...")
            self._choices.remove(forced_move)
            return Move(_x=forced_move.x, _y=forced_move.y)