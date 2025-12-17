#from random import choice, random
import random
from agents.Group14.VirtualBridge import VirtualBridge
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move
from .Node import Node
import time

HEX_DIRS = [
    (-1, 0), (1, 0),
    (0, -1), (0, 1),
    (-1, 1), (1, -1)
]
safe_first_moves = [Move(0, 1), Move(0, 9), Move(10, 1), Move(10, 9)] 

class MyAgent(AgentBase):
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.

    The class inherits from AgentBase, which is an abstract class.
    The AgentBase contains the colour property which you can use to get the agent's colour.
    You must implement the make_move method to make the agent functional.
    You CANNOT modify the AgentBase class, otherwise your agent might not function.
    """
    _iterations: int = 5000
    _choices: list[Move]
    _board_size: int = 11
    virtual_bridges: list[VirtualBridge] = []
    

    def __init__(self, colour: Colour):
        super().__init__(colour)
        self._choices = [
            Move(i, j) for i in range(self._board_size) for j in range(self._board_size)
        ]
        self._hexes = self._board_size * self._board_size
        self.virtual_bridges = []
        
        self.t_copy = 0.0
        self.t_select = 0.0
        self.t_expand = 0.0
        self.t_sim = 0.0
        self.t_backprop = 0.0
        self.rollouts = 0
        self.forced = 0.0
        self.others = 0.0
        self.total = 0.0

        
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
        t0 = time.perf_counter()
        # TURN 1: we move first (opp_move is None by contract)
        if opp_move == None:
            safe_moves = [m for m in safe_first_moves if m in self._choices]
            move = random.choice(safe_moves)
            self._choices.remove(move)
            return move

        # Case 1: opponent played a normal move
        if opp_move is not None and opp_move.x != -1:
            if opp_move in self._choices:
                self._choices.remove(opp_move)

            # TURN 2 only: decide whether *we* should swap
            if turn == 2:
                ox, oy = opp_move.x, opp_move.y
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
            self.update_bridges(board, forced_move)
            return forced_move

        
        
        #Find best move
        best_move = self.MCTS(self._choices,board)
        
        #Remove moves made by agent
        self._choices.remove(best_move)
        # update board for bridge detection
        board.set_tile_colour(best_move.x, best_move.y, self.colour)

        # check bridges using tuple
        self.update_bridges(board, best_move)
        
        self.total += time.perf_counter() - t0
        
        self.others += self.total - ( self.t_copy + self.t_select + self.t_expand + self.t_sim + self.t_backprop )

        print("\n=== MCTS PROFILE ===")
        print(f"Rollouts: {self.rollouts}")
        print(f"copy_board: {self.t_copy/self.total:.2%}")
        print(f"selection:  {self.t_select/self.total:.2%}")
        print(f"expansion:  {self.t_expand/self.total:.2%}")
        print(f"simulation: {self.t_sim/self.total:.2%}")
        print(f"backprop:   {self.t_backprop/self.total:.2%}")
        print(f"forced:   {self.forced/self.total:.2%}")
        print(f"Other:  {self.others/self.total:.2%}")
        print("====================\n")

        
        # only now convert to Move
        return Move(_x=best_move.x, _y=best_move.y)
    

    def MCTS(self,choices,board) -> Move:
        root = Node(self.copy_board(board),self.colour, choices, move=None,parent=None)
        for i in range(5000):
            node = root
            t0 = time.perf_counter()
            board_state = self.copy_board(board)
            self.t_copy += time.perf_counter() - t0


            #SELECTION
            #Check all untried nodes and node is non-terminal
            t0 = time.perf_counter()
            while node.untried_moves == [] and node.child_nodes:
                child = node.best_child()
                move = child.move
                board_state.set_tile_colour(move.x, move.y, node.colour)  # type: ignore # Use parent node's colour
                node = child
            self.t_select += time.perf_counter() - t0
            
        
            #EXPANSION
            #Add an extra child
            t0 = time.perf_counter()    
            if node.untried_moves:
                move = random.choice(node.untried_moves)
                #next_colour = self.opp_colour()
                next_colour = Colour.BLUE if node.colour == Colour.RED else Colour.RED
                #print(f"next colour: {next_colour}")
                board_state.set_tile_colour(move.x, move.x, node.colour)
                
                t0 = time.perf_counter()
                child = node.expand(self.copy_board(board_state), next_colour, move)
                self.t_copy += time.perf_counter() - t0

                node = child
            self.t_expand += time.perf_counter() - t0   
            

            #SIMULATION
            t0 = time.perf_counter()
            rollout_colour = node.colour             
             # --- FIX: Generate all possible moves, remove those already played ---
            all_possible_moves = [Move(x, y) for x in range(board.size) for y in range(board.size)]
            played_moves = [
                Move(x, y)
                for x in range(board.size)
                for y in range(board.size)
                if board_state.tiles[x][y].colour != None
            ]
            rollout_moves = [move for move in all_possible_moves if move not in played_moves]

            random.shuffle(rollout_moves)
            for legal_move in rollout_moves:
                board_state.set_tile_colour(legal_move.x, legal_move.y, rollout_colour) #Colour random legal move

                rollout_colour = Colour.RED if rollout_colour == Colour.BLUE else Colour.BLUE
            self.t_sim += time.perf_counter() - t0    
               

            #BACKPROPAGATION
            # has_ended updates the board_state.winner in the method so they need to be called
            # Could be more efficient
            t0 = time.perf_counter()
            
            winner = board_state.get_winner()

            node.backpropagation(winner)
            
            self.t_backprop += time.perf_counter() - t0
            
        best_child = max(root.child_nodes, key=lambda c: c.visits)
        return best_child.move # type: ignore
            
    def check_edge_bridges(self, board: Board, our_move: Move):
        x, y = our_move.x, our_move.y
        N = self._board_size

        # Determine connection axis
        # RED connects top/bottom → x axis
        # BLUE connects left/right → y axis
        if self.colour == Colour.RED:
            axis = 0  # x
        else:
            axis = 1  # y

        coord = (x, y)[axis]

        # Determine which goal edge we're near
        if coord == 1:
            edge_coord = 0
        elif coord == N - 2:
            edge_coord = N - 1
        else:
            return  # not near a relevant goal edge

        links : list[Move] = []

        # iterate possible bridge links along the other axis
        for d in (-1, 0, 1):
            other_coord = (x, y)[1 - axis] + d
            if 0 <= other_coord < N:
                pos = (
                    (edge_coord, other_coord) if axis == 0
                    else (other_coord, edge_coord)
                )
                if board.tiles[pos[0]][pos[1]].colour is None:
                    links.append(Move(*pos))

        if len(links) == 2:
            
            print("  *** EDGE BRIDGE FOUND ***")
                    
            print("Between:", (x,y))
            print("Link = ", links)
            
            self.virtual_bridges.append(
                VirtualBridge(
                    our_move,
                    None,          # edge-side endpoint
                    links[:2]
                )
            )

    
    def check_bridges(self, board: Board, our_move: Move):

        print("OUR MOVE:", our_move)
        x, y = our_move.x, our_move.y
        colour = self.colour

        if board.tiles[x][y].colour != colour:
            return
        
        nbrs_xy = set(self.neighbours(x, y))

        dirs = HEX_DIRS

        for i in range(len(dirs)):
            
            dx1, dy1 = dirs[i]
            
            for j in range(i + 1, len(dirs)):
                
                dx2, dy2 = dirs[j]
                
                if (dx1, dy1) == (dx2, dy2):
                    continue

                tx = x + dx1 + dx2
                ty = y + dy1 + dy2


                if not (0 <= tx < self._board_size and 0 <= ty < self._board_size):
                    continue


                if board.tiles[tx][ty].colour != colour:
                    continue
                
                if tx == x and ty == y:
                    continue
                
                # reject adjacent endpoints
                if (tx, ty) in nbrs_xy:
                    continue


                common : list[Move] = []
                nbrs_tx_ty = set(self.neighbours(tx, ty))

                for nx, ny in nbrs_xy:

                    if (nx, ny) in nbrs_tx_ty:

                        if board.tiles[nx][ny].colour is None:
                            common.append(Move(nx, ny))


                if len(common) == 2:
                    print("  *** BRIDGE FOUND ***")
                    
                    print("Between:", (x,y), (tx,ty))
                    print("Link = ", common)

                    bridge = VirtualBridge(Move(x, y), Move(tx, ty), common)
                    self.virtual_bridges.append(bridge)


    def neighbours(self, x : int, y : int):
        for dx, dy in HEX_DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self._board_size and 0 <= ny < self._board_size:
                yield nx, ny

    def check_bridge_invasion(self, opp_move : Move) -> Move | None:

        ox, oy = opp_move.x, opp_move.y
        
        print("Virtual bridge length right after opp_move:", len(self.virtual_bridges))
        
        RETALIATION_MOVE = None
        
        for bridge in self.virtual_bridges[:]:  # copy to allow removal
            
            
            l1 = bridge.links[0]
            l2 = bridge.links[1]
            
            if ox == l1.x and oy == l1.y:
                self.virtual_bridges.remove(bridge)                
                if not RETALIATION_MOVE:
                    RETALIATION_MOVE = l2

            elif ox == l2.x and oy == l2.y:
                self.virtual_bridges.remove(bridge)
                if not RETALIATION_MOVE:
                    RETALIATION_MOVE = l1

        return RETALIATION_MOVE
                    
    def remove_broken_bridges(self, move : Move):
        _ = self.check_bridge_invasion(move) 

            


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

        protect_bridge_move = self.check_bridge_invasion(opp_move)
        if protect_bridge_move and protect_bridge_move in self._choices:
            print("FOUND THREATENED BRIDGE...MOVING TO RETAIN...")
            self._choices.remove(protect_bridge_move)
            return Move(_x=protect_bridge_move.x, _y=protect_bridge_move.y)
        
        
    def update_bridges(self, board : Board, move : Move):
        
        t0 = time.perf_counter()
        self.remove_broken_bridges(move)
        self.check_edge_bridges(board, move)
        self.check_bridges(board, move)
        self.forced += time.perf_counter() - t0