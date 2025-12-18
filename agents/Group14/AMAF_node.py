import math
import random
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move
from collections import defaultdict


class Node:

    def __init__(self, board, colour,legal_moves,move = None,parent=None):
        self.parent:Node = parent  #parent node(none = root)             
        self.visits:int = 0 #times node has been visited
        self.child_nodes = [] #child nodes
        self.wins:int = 0 #amount of wins
        self.board:Board = board #copy of board
        self.move:Move = move #move prior to node
        self.colour:Colour = colour #who made the move
        self.untried_moves = legal_moves[:]

        # AMAF/RAVE statistics
        # self.AMAF_visits: int = 0
        # self.AMAF_wins: int = 0

        self.amaf_visits = defaultdict(int)   # key: (x,y)
        self.amaf_wins   = defaultdict(int)
        

    def ucb1(self, child):
        if child.visits == 0:
            return float("inf")
        
        # UCT value (standard win rate)
        q_uct = child.wins / child.visits

        n_amaf = self.amaf_visits[child.move]
        q_amaf = (self.amaf_wins[child.move] / n_amaf) if n_amaf > 0 else 0.5

        n_uct = child.visits
        k = 50  # typical RAVE bias constant
        w = n_amaf / (n_uct + n_amaf + k)

        return (1 - w) * q_uct + w * q_amaf


        # # AMAF / RAVE value (win rate from AMAF stats)
        # if child.AMAF_visits > 0:
        #     q_amaf = child.AMAF_wins / child.AMAF_visits
        # else:
        #     q_amaf = 0.0

        # # RAVE weight w based on ratio of AMAF visits to total visits
        # # w in [0,1]; when AMAF_visits >> visits, w → 1
        # n_uct = child.visits
        # n_amaf = child.AMAF_visits
        # if n_uct + n_amaf > 0:
        #     w = n_amaf / (n_uct + n_amaf)
        # else:
        #     w = 0.0


        # c = 0.0  # no exploration term as requested

        # # AMAF / RAVE score
        # score = (1.0 - w) * q_uct + w * q_amaf
        # # + c * math.sqrt(math.log(self.visits) / child.visits)  # if you ever re‑enable exploration

        # return score

    def best_child(self):

        unvisited = [child for child in self.child_nodes if child.visits == 0]
        if unvisited:
            return random.choice(unvisited)

        candidates = self.child_nodes[:]
        return max(candidates, key=self.ucb1)
    
    def backpropagation(self, result, amaf_moves, root):
        node = self
        while node is not None:
            if node.move == None:
                # means we're at root node
                if node.colour == result:
                    node.wins += 1
                    node.AMAF_wins += 1
                node.visits += 1
                node.AMAF_visits += 1
                break # root node reached

            node.visits += 1

            if node.parent.colour == result:
                node.wins += 1

            # AMAF update: for all child nodes of root, if their move was played in rollout, update AMAF stats
            for child in root.child_nodes:
                if child.move in amaf_moves:
                    child.AMAF_visits += 1
                    if child.colour == result:
                        child.AMAF_wins += 1    

            node = node.parent

    #Expansion
    def expand(self, next_board, next_colour, move):
        # Get all moves played so far (by traversing up the parent chain)
        played_moves = set()
        node = self
        while node is not None and node.move is not None:
            played_moves.add(node.move)
            node = node.parent

        played_moves.add(move)  # Add the move just played

        # All possible moves for the board size
        all_possible_moves = [Move(x, y) for x in range(next_board.size) for y in range(next_board.size)]
        child_untried_moves = [m for m in all_possible_moves if m not in played_moves]

        child = Node(next_board, next_colour, child_untried_moves, move=move, parent=self)
        self.child_nodes.append(child)
        self.untried_moves.remove(move)
        return child
