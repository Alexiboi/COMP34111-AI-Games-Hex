import math
import random


class Node:

    def __init__(self, state, parent=None):
        self.parent = parent              
        self.visits = 0
        self.child_nodes = []
        self.wins = 0
        self.state = state

    def ucb1(self, child):
        if child.visits == 0:
            return float("inf")
        #TWEAK 1.41
        return (child.wins / child.visits) + 1.41 * math.sqrt(
            math.log(self.visits) / child.visits
        )

    def best_child(self, c=1.41):

        # 1. unvisited children
        unvisited = [child for child in self.child_nodes if child.visits == 0]
        if unvisited:
            return random.choice(unvisited)


        candidates = self.child_nodes[:]
        return max(candidates, key=self.ucb1)
    
    def backpropagation(self, result):

        node = self
        while node is not None:
            node.visits += 1

            if node.state.player == result:
                node.wins += 1

            node = node.parent

