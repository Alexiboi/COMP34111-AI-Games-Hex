#from random import choice, random
import copy
import random
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move
from .AMAF_node2 import Node
import time

HEX_DIRS = [
    (-1, 0), (1, 0),
    (0, -1), (0, 1),
    (-1, 1), (1, -1)
]
safe_first_moves = [Move(0, 1), Move(0, 9), Move(10, 1), Move(10, 9)] 

class amafTimed_agent2(AgentBase):
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.

    The class inherits from AgentBase, which is an abstract class.
    The AgentBase contains the colour property which you can use to get the agent's colour.
    You must implement the make_move method to make the agent functional.
    You CANNOT modify the AgentBase class, otherwise your agent might not function.
    """
    _choices: list[Move]
    _board_size: int = 11
    

    def __init__(self, colour: Colour):
        super().__init__(colour)
        self._choices = [
            Move(i, j) for i in range(self._board_size) for j in range(self._board_size)
        ]
        
        self.time_used = 0.0
        self.TOTAL_TIME = 300.0
        self.RESERVE = 2.0



        
        
        
        
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
        remaining = self.TOTAL_TIME - self.time_used
        

        
        if remaining <= self.RESERVE:
            move = random.choice(self._choices)
            self._choices.remove(move)
            self.time_used += time.perf_counter() - t0
            return move

        
        
        print(f"We are moving for colour {self.colour}")
        
        # TURN 1: we move first (opp_move is None by contract)
        if opp_move == None:
            safe_moves = [m for m in safe_first_moves if m in self._choices]
            opening_move = random.choice(safe_moves)
            safe_move = self.make_legal_move(opening_move, board, self._choices, turn)
            self._choices.remove(safe_move)
            self.time_used += time.perf_counter() - t0
            return safe_move

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
                    proposed_move = Move(-1, -1)
                    self.time_used += time.perf_counter() - t0
                    return self.make_legal_move(proposed_move, board, self._choices, turn)
        
       
                
        forced_move = self.forced_move(board, self._choices)
        
        if forced_move:
            safe_move = self.make_legal_move(forced_move, board, self._choices, turn)
            self._choices.remove(safe_move)
            board.set_tile_colour(safe_move.x, safe_move.y, self.colour)
            self.time_used += time.perf_counter() - t0
            return safe_move

        
        # budget = min(max(base, self.MIN_BUDGET), self.MAX_BUDGET)
        
        remaining = self.TOTAL_TIME - self.time_used

        budget = remaining * 0.08   # 8%

        # Safety clamp
        budget = max(2.0, min(budget, 20.0))



        
        print(
            f"remaining={remaining:.1f}s choices={len(self._choices)} "
            f"budget={budget:.2f}s"
        )
        
        #Find best move
        print(f"MCTS running with budget: {budget}")
        best_move = self.MCTS(self._choices, board, deadline = time.perf_counter() + budget)
        
        safe_move = self.make_legal_move(best_move, board, self._choices, turn)
        
        #Remove moves made by agent
        self._choices.remove(safe_move)
        
        # update board for bridge detection
        board.set_tile_colour(safe_move.x, safe_move.y, self.colour)


        self.time_used += time.perf_counter() - t0


        # only now convert to Move
        return safe_move
    
    

    def MCTS(self,choices,board, deadline) -> Move:
        root = Node(self.copy_board(board),self.colour, choices, move=None,parent=None)
        while time.perf_counter() < deadline:
            node = root
            board_state = self.copy_board(board)
            path = [node] #Track the path for UCT backpropogation

            #SELECTION
            #Check all untried nodes and node is non-terminal
            #print(node.untried_moves)
            while node.untried_moves == [] and node.child_nodes:
                child = node.best_child()
                move = child.move
                board_state.set_tile_colour(move.x, move.y, node.colour)  # type: ignore # Use parent node's colour
                node = child
                path.append(node) # for AMAF
        
            #EXPANSION
            #Add an extra child
            if node.untried_moves:
                move = random.choice(node.untried_moves)
                #next_colour = self.opp_colour()
                next_colour = Colour.BLUE if node.colour == Colour.RED else Colour.RED
                #print(f"next colour: {next_colour}")
                board_state.set_tile_colour(move.x, move.y, node.colour)
                
                child = node.expand(self.copy_board(board_state), next_colour, move)
                node = child
                path.append(node)

            #SIMULATION
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
            rollout_trace = []  # list of (move, played_by_colour)
            for legal_move in rollout_moves:
                board_state.set_tile_colour(legal_move.x, legal_move.y, rollout_colour) #Colour random legal move
                rollout_trace.append((legal_move, rollout_colour))     
                if board_state.has_ended(rollout_colour):
                    break
                rollout_colour = Colour.RED if rollout_colour == Colour.BLUE else Colour.BLUE
                        
            winner = board_state.get_winner()
                
            tree_trace = []
            for idx in range(1, len(path)):
                move_played = path[idx].move
                played_by = path[idx-1].colour   # parent was to-play and made the move
                tree_trace.append((move_played, played_by))    
               
            full_trace = tree_trace + rollout_trace

            #BACKPROPAGATION
            # has_ended updates the board_state.winner in the method so they need to be called
            # Could be more efficient
            self.backprop_with_amaf(path, full_trace, winner)
            #node.backpropagation(winner)
            
            
        best_child = max(root.child_nodes, key=lambda c: c.visits)
        return best_child.move # type: ignore

    def backprop_with_amaf(self, path, full_trace, winner):
        # path[0]=root depth 0, path[1]=depth1, ...
        for d, node in enumerate(path):
            # --- node stats (optional for root decision, but fine to keep) ---
            node.visits += 1
            # if you want node.wins to mean "wins for player who played into this node":
            if node.parent is not None and winner == node.parent.colour:
                node.wins += 1

            # --- AMAF at this node ---
            # moves that happened after this node's position
            # index d in full_trace corresponds to the move played FROM this node (depth d -> d+1)
            moves_after = full_trace[d:]  # includes the move chosen from this node

            player_to_move = node.colour

            for (mv, played_by) in moves_after:
                if played_by != player_to_move:
                    continue

                # only update if mv is legal from this node (either untried or already a child)
                if (mv in node.untried_moves) or any(c.move == mv for c in node.child_nodes):
                    node.amaf_visits[mv] += 1
                    if winner == player_to_move:
                        node.amaf_wins[mv] += 1                
        
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

    def forced_move(self, board : Board, choices : list[Move]) -> Move | None:
        
        terminal_move = self.apply_terminal_protocol(board, choices)
        if terminal_move is not None:
            print("FOUND FORCED WIN...MOVING TO TAKE/BLOCK...")
            return Move(terminal_move.x, terminal_move.y)


    def make_legal_move(
    self,
    proposed: Move | None,
    board: Board,
    choices: list[Move],
    turn: int, ) -> Move:
        """
        Final safety check before returning a move to the engine.
        Always returns a legal Move.
        """

        # --- 1. Fallback: no proposal ---
        if proposed is None:
            return random.choice(choices)

        # --- 2. Swap move handling ---
        if proposed.x == -1 and proposed.y == -1:
            # Swap is only legal on turn 2
            if turn == 2:
                return proposed
            # Otherwise illegal → fallback
            return random.choice(choices)

        x, y = proposed.x, proposed.y
        size = board.size

        # --- 3. Bounds check ---
        if not (0 <= x < size and 0 <= y < size):
            return random.choice(choices)

        # --- 4. Occupancy check ---
        if board.tiles[x][y].colour is not None:
            return random.choice(choices)

        # --- 5. Consistency with choices list ---
        # (important: engine legality + your internal state)
        if proposed not in choices:
            return random.choice(choices)

        # --- 6. Passed all checks ---
        return proposed
