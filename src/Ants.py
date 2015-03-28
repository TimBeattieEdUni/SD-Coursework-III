import math
import random

class Ant():
    """
        Implements an "ant" which wanders randomly along paths obtained from its colony.
        Part of an "Ant Colony" algorithm for finding paths through graphs.
        For algorithm detail and descriptions of variable meanings, see this link:
        http://en.wikipedia.org/wiki/Ant_colony_optimization_algorithms
    """

    def __init__(self, ID, start_node, colony):
        """
            Initialises the ant at a node in the matrix.
            Stores a reference to the colony for updates and matrix access.
        """
        self.ID = ID
        self.start_node = start_node
        self.colony = colony
        self.curr_node = self.start_node
        self.graph = self.colony.graph
        self.path_vec = []
        self.path_vec.append(self.start_node)
        self.path_cost = 0
        self.Beta = 1.0
        self.Q0 = 0.5
        self.Rho = 0.99
        self.nodes_to_visit = {}
        for i in range(0, self.graph.num_nodes):
            if i != self.start_node:
                self.nodes_to_visit[i] = i
        self.path_mat = []
        for i in range(0, self.graph.num_nodes):
            self.path_mat.append([0] * self.graph.num_nodes)

    def run(self):
        """
            Walks the ant through all nodes in the graph, recording the path it takes.
            Updates the colony when done.
            TODO: Not yet clear why this function resets the object when done.
        """
        graph = self.colony.graph
        while self.nodes_to_visit:
            new_node = self.state_transition_rule(self.curr_node)
            self.path_cost += graph.delta(self.curr_node, new_node)
            self.path_vec.append(new_node)
            self.path_mat[self.curr_node][new_node] = 1 
            self.local_updating_rule(self.curr_node, new_node)
            self.curr_node = new_node
        self.path_cost += graph.delta(self.path_vec[-1], self.path_vec[0])
        self.colony.update(self)
        self.__init__(self.ID, self.start_node, self.colony)

    def state_transition_rule(self, curr_node):
        """
            Runs the ant through the set of nodes in the graph.
            Chooses next node at random, weighted by pheromone levels.
            TODO: This function is a little long and "math-y"; it might benefit from being separated into subroutines.
        """
        graph = self.colony.graph
        q = random.random()
        max_node = -1
        if q < self.Q0:
            print "Exploitation"
            max_val = -1
            val = None
            for node in self.nodes_to_visit.values():
                if graph.tau(curr_node, node) == 0:
                    raise Exception("tau = 0")
                val = graph.tau(curr_node, node) * math.pow(graph.etha(curr_node, node), self.Beta)
                if val > max_val:
                    max_val = val
                    max_node = node
        else:
            print "Exploration"
            sum = 0
            node = -1
            for node in self.nodes_to_visit.values():
                if graph.tau(curr_node, node) == 0:
                    raise Exception("tau = 0")
                sum += graph.tau(curr_node, node) * math.pow(graph.etha(curr_node, node), self.Beta)
            if sum == 0:
                raise Exception("sum = 0")
            avg = sum / len(self.nodes_to_visit)
            print "avg = %s" % (avg,)
            for node in self.nodes_to_visit.values():
                p = graph.tau(curr_node, node) * math.pow(graph.etha(curr_node, node), self.Beta)
                if p > avg:
                    print "p = %s" % (p,)
                    max_node = node
            if max_node == -1:
                max_node = node
        if max_node < 0:
            raise Exception("max_node < 0")
        del self.nodes_to_visit[max_node]
        return max_node

    def local_updating_rule(self, curr_node, next_node):
        """
            Updates the pheromones on the tau matrix to represent transitions of the ants
        """
        graph = self.colony.graph
        val = (1 - self.Rho) * graph.tau(curr_node, next_node) + (self.Rho * graph.tau0)
        graph.update_tau(curr_node, next_node, val)


import random
import sys


class Colony:
    """
        Manages a set of ants which do the exploring and gathers their results.
    """
    def __init__(self, graph, num_ants, num_iterations):
        """
            Stores the given parameters and resets the object.
            TODO: Not yet clear what Alpha is.
        """
        self.graph = graph
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.Alpha = 0.1
        self.reset()

    def reset(self):
        """
            Clears all values obtained from previous calculations.
        """
        self.best_path_cost = sys.maxint
        self.best_path = None
        self.best_path_matrix = None

    def run(self):
        """Creates the set of ants and runs the colony."""
        self.ants = self.create_ants()
        self.iter_counter = 0
        while self.iter_counter < self.num_iterations:
            self.iteration()
            self.pheromone_update()

    def iteration(self):
        """
            Resets average calculation and runs all ants.
            Ants will call this class's update() method.
        """
        self.avg_path_cost = 0
        self.ant_counter = 0
        self.iter_counter += 1
        for ant in self.ants:
            ant.run()

    def update(self, ant):
        """
            Called by ants to report their results.
        """
        print "Update called by %s" % (ant.ID,)
        self.ant_counter += 1
        self.avg_path_cost += ant.path_cost
        if ant.path_cost < self.best_path_cost:
            self.best_path_cost = ant.path_cost
            self.best_path_matrix = ant.path_mat
            self.best_path = ant.path_vec
        if self.ant_counter == len(self.ants):
            self.avg_path_cost /= len(self.ants)
            print "Best: %s, %s, %s, %s" % (
                self.best_path, self.best_path_cost, self.iter_counter, self.avg_path_cost,)

    def create_ants(self):
        """
            Initialises the set of ants.
            TODO: This probably doesn't need to be a separate function.
        """
        self.reset()
        ants = []
        for i in range(0, self.num_ants):
            ant = Ant(i, random.randint(0, self.graph.num_nodes - 1), self)
            ants.append(ant)
        return ants
 
    def pheromone_update(self):
        """Updates matrix of path pheromone levels."""
        for r in range(0, self.graph.num_nodes):
            for s in range(0, self.graph.num_nodes):
                if r != s:
                    delta_tau = self.best_path_matrix[r][s] / self.best_path_cost
                    evaporation = (1 - self.Alpha) * self.graph.tau(r, s)
                    deposition = self.Alpha * delta_tau
                    self.graph.update_tau(r, s, evaporation + deposition)

class GraphBit:
    """Stores delta and tau matrices and provides operations on matrix elements."""

    def __init__(self, delta_mat, tau_mat=None):
        """Stores the given matrices (generating zeroes in tau matrix if not provided.)"""
        self.num_nodes = len(delta_mat)
        self.delta_mat = delta_mat 
        if tau_mat is None:
            self.tau_mat = []
            for i in range(0, self.num_nodes):
                self.tau_mat.append([0] * self.num_nodes)

    def delta(self, r, s):
        """Element access for delta matrix."""
        return self.delta_mat[r][s]

    def tau(self, r, s):
        """Element access for tau matrix."""
        return self.tau_mat[r][s]

    def etha(self, r, s):
        """Returns reciprocal of element in delta matrix.  Not yet clear what this is for - part of the ant colony algorithm."""
        return 1.0 / self.delta(r, s)

    def update_tau(self, r, s, val):
        """Sets the given element in the tau matrix."""
        self.tau_mat[r][s] = val

    def reset_tau(self):
        """Calculates a value and assigns every element of the tau matrix that value.  Not yet clear how the value is chosen."""
        avg = self.average(self.delta_mat)
        self.tau0 = 1.0 / (self.num_nodes * 0.5 * avg)
        print "Average = %s" % (avg,)
        print "Tau0 = %s" % (self.tau0)
        for r in range(0, self.num_nodes):
            for s in range(0, self.num_nodes):
                self.tau_mat[r][s] = self.tau0

    def average(self, matrix):
        """Returns the average of all values in the given matrix."""
        sum = 0
        for r in range(0, self.num_nodes):
            for s in range(0, self.num_nodes):
                sum += matrix[r][s]

        avg = sum / (self.num_nodes * self.num_nodes)
        return avg
