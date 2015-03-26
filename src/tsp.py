import math
import random

class Work():
    def __init__(self, ID, start_node, colony):
        self.ID = ID
        self.start_node = start_node
        self.grouping = colony
        self.curr_node = self.start_node
        self.graph = self.grouping.graph
        self.path_vec = []
        self.path_vec.append(self.start_node)
        self.path_cost = 0
        self.Beta = 1.0
        self.Q0 = 0.5
        self.Rho = 0.99
        self.ntv = {}
        for i in range(0, self.graph.num_nodes):
            if i != self.start_node:
                self.ntv[i] = i
        self.path_mat = []
        for i in range(0, self.graph.num_nodes):
            self.path_mat.append([0] * self.graph.num_nodes)

    #could this be simpler?
    def run(self):
        graph = self.grouping.graph
        while not self.end():
            new_node = self.state_transition_rule(self.curr_node)
            self.path_cost += graph.delta(self.curr_node, new_node)
            self.path_vec.append(new_node)
            self.path_mat[self.curr_node][new_node] = 1 
            self.local_updating_rule(self.curr_node, new_node)
            self.curr_node = new_node
        self.path_cost += graph.delta(self.path_vec[-1], self.path_vec[0])
        self.grouping.update(self)
        self.__init__(self.ID, self.start_node, self.grouping)

    def end(self):
        return not self.ntv


    def state_transition_rule(self, curr_node):
        graph = self.grouping.graph
        q = random.random()
        max_node = -1
        if q < self.Q0:
            print "Exploitation"
            max_val = -1
            val = None
            for node in self.ntv.values():
                if graph.tau(curr_node, node) == 0:
                    raise Exception("tau = 0")
                val = graph.tau(curr_node, node) * math.pow(graph.etha(curr_node, node), self.Beta)
                if val > max_val:
                    max_val = val
                    max_node = node
        else:
            #Bob was here
            print "Exploration"
            sum = 0
            node = -1
            for node in self.ntv.values():
                if graph.tau(curr_node, node) == 0:
                    raise Exception("tau = 0")
                sum += graph.tau(curr_node, node) * math.pow(graph.etha(curr_node, node), self.Beta)
            if sum == 0:
                raise Exception("sum = 0")
            avg = sum / len(self.ntv)
            print "avg = %s" % (avg,)
            for node in self.ntv.values():
                p = graph.tau(curr_node, node) * math.pow(graph.etha(curr_node, node), self.Beta)
                if p > avg:
                    print "p = %s" % (p,)
                    max_node = node
            if max_node == -1:
                max_node = node
        if max_node < 0:
            raise Exception("max_node < 0")
        del self.ntv[max_node]
        return max_node

    def local_updating_rule(self, curr_node, next_node):
        #Update the pheromones on the tau matrix to represent transitions of the ants
        graph = self.grouping.graph
        val = (1 - self.Rho) * graph.tau(curr_node, next_node) + (self.Rho * graph.tau0)
        graph.update_tau(curr_node, next_node, val)


import random
import sys



class BigGroup:
    def __init__(self, graph, num_ants, num_iterations):
        self.graph = graph
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.Alpha = 0.1
        self.reset()

    def reset(self):
        self.bpc = sys.maxint
        self.bpv = None
        self.bpm = None
        self.lbpi = 0

    def start(self):
        self.ants = self.c_workers()
        self.iter_counter = 0

        while self.iter_counter < self.num_iterations:
            self.iteration()
            # Note that this will help refine the results future iterations.
            self.global_updating_rule()

    def iteration(self):
        self.avg_path_cost = 0
        self.ant_counter = 0
        self.iter_counter += 1
        for ant in self.ants:
            ant.run()

    def num_ants(self):
        return len(self.ants)

    def num_iterations(self):
        return self.num_iterations

    def iteration_counter(self):
        return self.iter_counter

    def update(self, ant):
        print "Update called by %s" % (ant.ID,)
        self.ant_counter += 1
        self.avg_path_cost += ant.path_cost
        if ant.path_cost < self.bpc:
            self.bpc = ant.path_cost
            self.bpm = ant.path_mat
            self.bpv = ant.path_vec
            self.lbpi = self.iter_counter
        if self.ant_counter == len(self.ants):
            self.avg_path_cost /= len(self.ants)
            print "Best: %s, %s, %s, %s" % (
                self.bpv, self.bpc, self.iter_counter, self.avg_path_cost,)


    def done(self):
        return self.iter_counter == self.num_iterations

    def c_workers(self):
        self.reset()
        ants = []
        for i in range(0, self.num_ants):
            ant = Work(i, random.randint(0, self.graph.num_nodes - 1), self)
            ants.append(ant)

        return ants
 
    def global_updating_rule(self):
        #can someone explain this
        evaporation = 0
        deposition = 0
        for r in range(0, self.graph.num_nodes):
            for s in range(0, self.graph.num_nodes):
                if r != s:
                    delt_tau = self.bpm[r][s] / self.bpc
                    evaporation = (1 - self.Alpha) * self.graph.tau(r, s)
                    deposition = self.Alpha * delt_tau
                    self.graph.update_tau(r, s, evaporation + deposition)

class GraphBit:
    def __init__(self, num_nodes, delta_mat, tau_mat=None):
        print len(delta_mat)
        if len(delta_mat) != num_nodes:
            raise Exception("len(delta) != num_nodes")
        self.num_nodes = num_nodes
        self.delta_mat = delta_mat 
        if tau_mat is None:
            self.tau_mat = []
            for i in range(0, num_nodes):
                self.tau_mat.append([0] * num_nodes)

    def delta(self, r, s):
        return self.delta_mat[r][s]

    def tau(self, r, s):
        return self.tau_mat[r][s]

    def etha(self, r, s):
        return 1.0 / self.delta(r, s)

    def update_tau(self, r, s, val):
        self.tau_mat[r][s] = val

    def reset_tau(self):
        avg = self.average_delta()
        self.tau0 = 1.0 / (self.num_nodes * 0.5 * avg)
        print "Average = %s" % (avg,)
        print "Tau0 = %s" % (self.tau0)
        for r in range(0, self.num_nodes):
            for s in range(0, self.num_nodes):
                self.tau_mat[r][s] = self.tau0


    def average_delta(self):
        return self.average(self.delta_mat)


    def average_tau(self):
        return self.average(self.tau_mat)

    def average(self, matrix):
        sum = 0
        for r in range(0, self.num_nodes):
            for s in range(0, self.num_nodes):
                sum += matrix[r][s]

        avg = sum / (self.num_nodes * self.num_nodes)
        return avg

import pickle
import sys
import traceback


def PrintUsage():
    print("usage: " + sys.argv[0] + " <cities> <citiesfile> <solutionfile> [<seed>]")
    print("where:")
    print("    <cities>        is the number of cities to visit (must be 3 or greater).")
    print("    <citiesfile>    is a \"pickle\" file containing cities and distances.")
    print("    <solutionfile>  is the file to write the solution to.")
    print("    <seed>          is an optional seed for the random number generator.")


def main(argv):
    # check number of command line arguments
    if len(argv) > 4 or len(argv) < 3:
        PrintUsage()
        sys.exit(-1)
    
    # check number of cities is sane: a number, 3 or more
    num_cities = int(argv[0])
    if (3 > num_cities):
        print("error: invalid number of cities")
        sys.exit(-1)
    
    # check input file exists
    infilename = argv[1]
    try:
        infile = open(infilename, "r")
    except:
        print("error: unable to open input file " + infilename)
        sys.exit(-1)

    # check output file can be opened
    outfilename = argv[2]
    try:
        outfile = open(outfilename, 'w+')
    except:
        print("error: unable to open output file " + infilename)
        sys.exit(-1)

    # check for optional random seed argument and apply if found
    if 4 == len(argv):
        seed = argv[3]
        print("seeding random number generator with value " + seed)
        random.seed(seed)

    # configuration
    # leaving these magic numbers in place for now until they're understood better
    
    if num_cities <= 10:
        num_ants = 20
        num_iters = 12
    else:
        num_ants = 28
        num_iters = 20

    # load cities and distances
    city_data = pickle.load(infile)
    cities = city_data[0]
    city_matrix = city_data[1]

    # truncate the city matrix to just those cities we'll be visiting
    if num_cities < len(city_matrix):
        city_matrix = city_matrix[0:num_cities]
        for i in range(0, num_cities):
            city_matrix[i] = city_matrix[i][0:num_cities]

    try:
        # set up data structure and colony
        graph = GraphBit(num_cities, city_matrix)
        best_path_indices = None
        best_distance = sys.maxint

        graph.reset_tau()
        workers = BigGroup(graph, num_ants, num_iters)
        
        print "Colony Started"

        # run the calculation
        workers.start()
        if workers.bpc < best_distance:
            print "Colony Path"
            best_path_indices = workers.bpv
            best_distance = workers.bpc

        # print results
        print "\n------------------------------------------------------------"
        print "                     Results                                "
        print "------------------------------------------------------------"
        print "\nBest path = %s" % (best_path_indices,)

        best_path = []
        for index in best_path_indices:
            print cities[index] + " ",
            best_path.append(cities[index])

        print "\nBest path distance = %s\n" % (best_distance,)
        results = [best_path_indices, best_path, best_distance]
        pickle.dump(results, outfile)

    # current approach to error handling is to report the error and give up
    except Exception, e:
        print "exception: " + str(e)
        traceback.print_exc()


if __name__ == "__main__":
    main(sys.argv[1:])
