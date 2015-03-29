
"""
    Uses an Ant Colony algorithm to solve the Travelling Salesman problem.
    TODO: Pickle file format needs to be documented - or replaced with something simpler.
"""


# Standard modules
import pickle
import random
import sys
import traceback

# Local modules
import Ants


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
    # TODO: Make these optional command-line arguments.
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

    # sanity check number of cities
    if num_cities > len(city_matrix):
        num_cities = len(city_matrix)
        print("warning: database only contains " + str(num_cities) + " cities")

    # truncate the city matrix to just those cities we'll be visiting
    if num_cities < len(city_matrix):
        city_matrix = city_matrix[0:num_cities]
        for i in range(0, num_cities):
            city_matrix[i] = city_matrix[i][0:num_cities]

    try:
        # set up data structure and colony
        graph = Ants.GraphBit(city_matrix)
        best_path_indices = None
        best_distance = sys.maxint

        graph.reset_tau()
        workers = Ants.Colony(graph, num_ants, num_iters)
        
        print "Colony created"

        # run the calculation
        workers.run()
        if workers.best_path_cost < best_distance:
            print "Colony Path"
            best_path_indices = workers.best_path
            best_distance = workers.best_path_cost

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

    # current approach to error handling is to report any error and give up
    except Exception, e:
        print "exception: " + str(e)
        traceback.print_exc()


if __name__ == "__main__":
    main(sys.argv[1:])
