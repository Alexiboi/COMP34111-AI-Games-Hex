import math
import random
from src.AgentBase import AgentBase
from src.Board import Board
from src.Colour import Colour
from src.Move import Move


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
        

    def ucb1(self, child):
        if child.visits == 0:
            return float("inf")
        #TWEAK 1.41
        return (child.wins / child.visits) + 1.41 * math.sqrt(
            math.log(self.visits) / child.visits
        )

    def best_child(self):

        unvisited = [child for child in self.child_nodes if child.visits == 0]
        if unvisited:
            return random.choice(unvisited)

        candidates = self.child_nodes[:]
        return max(candidates, key=self.ucb1)
    
    def backpropagation(self, result):
        node = self
        while node is not None:
            if node.move == None:
                # means we're at root node
                if node.colour == result:
                    node.wins += 1
                node.visits += 1
                break # root node reached
            node.visits += 1

            if node.parent.colour == result:
                node.wins += 1

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
        all_possible_moves = [(x, y) for x in range(next_board.size) for y in range(next_board.size)]
        child_untried_moves = [m for m in all_possible_moves if m not in played_moves]

        child = Node(next_board, next_colour, child_untried_moves, move=move, parent=self)
        self.child_nodes.append(child)
        self.untried_moves.remove(move)
        return child


