#!/usr/bin/env python3

"""Investigates the distribution of (graph) Shannon entropy.

This script investigates the distribution of (graph) Shannon entropy
across dfferent Markov models.

"""

import argparse # For command line parsing.
import numpy as np # For matrices.
import time # For getting the time to use as a random seed.
import math # For modf.
import json # For manipulating json files.
import matplotlib.pyplot as plt # For graphing.
import markov.Model as markel
import linkograph.stats as lstats

def genSingleOntologyStats(ontNext, ontLink, minLinkoSize,
                           maxLinkoSize, stepLinkoSize, modelNum,
                           runNum, precision=2, seeds=None):
    """Generate the stats on link models for a given ontology.

    inputs:

    ontNext: ontology used to generate Markov model that create the
    next state.

    ontLink: ontology used for constructing linkographs.

    minLinkoSize: the minimun number of nodes in the linkographs to
    consider.

    maxLinkoSize: the maximum number of nodes in the linkographs to
    consider. Note that the max is not included to match pythons
    convertions on lists and ranges.

    stepLinkoSize: the step size between minLinkoSize to maxLinkoSize
    for the number of linkographs to Consider.

    modelNum: the number of models.

    runNum: the number of linkographs to consider for each linkograph
    size.

    precision:  the number of decimals places to use for the Markov
    models.

    seeds: a list of seeds to use for the generated next Markov
    models. The size of the list should be the same as the number of
    runs.

    output:

    a number_of _linkographs x 2. For each linkograph size i, the
    average value for each model is calculated. The (i, 0) then
    provides the mean of the model averages and (i, 1) provides the
    standard deviation of the model averages.

    """

    linkoSizes = range(minLinkoSize, maxLinkoSize, stepLinkoSize)

    ontSize = len(ontNext)
    absClasses = list(ontNext.keys())
    absClasses.sort()

    results = np.zeros((len(linkoSizes), 2))

    if seeds is None:
        seeds = [time.time()*i for i in range(modelNum)]

    models = []
    # Create the generating models
    for i in range(modelNum):
        m = markel.genModelFromOntology(ontology=ontNext,
                                        precision=2,
                                        seed=seeds[i])

        # Storing the model and the current state
        models.append(m)

    # For each size linkograph, generate the runNum links and
    # caculate the needed statistics.
    for size in linkoSizes:

        print('size: {0}'.format(size))

        metrics = np.zeros((modelNum, runNum))

        for modelIndex, m in enumerate(models):

            for i in range(runNum):

                # Randomize the initial state
                m.state = m.random.randint(1, len(m.absClasses)) - 1

                linko = m.genLinkograph(size, ontology=ontLink)

                entropy = lstats.graphEntropy(linko)

                metrics[modelIndex, i] = entropy

        index = (size - minLinkoSize)//stepLinkoSize

        # Calculate the mean and standard deviation for each model
        # across the different runs.
        meanAcrossRuns = np.mean(metrics, axis=1)

        # Calculate the mean and standard deviation across the model
        # means. The mean is the same as taking the mean over all of
        # the metrics matrix, but the standard deviation will be
        # different.
        results[index, 0] =  np.mean(meanAcrossRuns)
        results[index, 1] =  np.std(meanAcrossRuns)

    return results


def genLinkMarkov(linkoSize, model, precision=2, timeSize=7):
    """Generates a link Markov from model generated linkograph.

    inputs:

    linkoSize: the size of linkograph to base the link Markov model
    off of.

    model: the Markov model to use. Note that the model must have an
    ontology in order to generate the linkgraphs.

    precicision: the number of decimal places to use for the
    link Markov model.

    timeSize = the size of integers to use for seeding the random
    number generator of the returned Markov model.

    output:

    A link Markov model based off a linkoSize linkograph generated by
    the provided Markov model.

    """

    seed = int(math.modf(time.time())[0]*(10**timeSize))

    # generate the linkograph
    linko = model.genLinkograph(linkoSize)

    # create the link model
    model = genModelFromLinko(linko, precision=precision,
                              ontology=model.ontology, seed=seed,
                              method='link_predictor', linkNum=1)
    
    return model

if __name__ == '__main__':

    info = """Investigates the graph Shannon Entrpoy for random Markov
    models."""

    parser = argparse.ArgumentParser(description=info)
    parser.add_argument('ontNext', metavar='ONTOLOGY_NEXT.json',
                        nargs=1,
                        help='the ontology file for producing.')

    parser.add_argument('ontLink', metavar='ONTOLOGY_LINK.json',
                        nargs=1,
                        help='the ontology file for learning.')

    parser.add_argument('-m', '--minimum', type=int, default = 2,
                       help='minimum size of linkographs.')

    parser.add_argument('-M', '--maximum', type=int, default = 100,
                       help='maximum size of linkographs.')

    parser.add_argument('-s', '--step', type=int, default = 1,
                       help='step size of linkographs.')

    parser.add_argument('-n', '--modelNum', type=int, default = 100,
                       help='number of generating models.')

    parser.add_argument('-r', '--runs', type=int, default = 100,
                        help='the number of runs.')

    parser.add_argument('-p', '--precision', type=int, default = 2,
                        help='the number of runs.')

    args = parser.parse_args()

    # Extract the ontology
    ontNext = None
    with open(args.ontNext[0], 'r') as ontNextFile:
        ontNext = json.load(ontNextFile)

    ontLink = None
    with open(args.ontLink[0], 'r') as ontLinkFile:
        ontLink = json.load(ontLinkFile)

    seed = int(math.modf(time.time())[0]*(10**7))

    results = genSingleOntologyStats(ontNext=ontNext,
                                     ontLink=ontLink,
                                     minLinkoSize=args.minimum,
                                     maxLinkoSize=args.maximum,
                                     stepLinkoSize=args.step,
                                     modelNum=args.modelNum,
                                     runNum=args.runs,
                                     precision=args.precision)

    absClasses = list(ontNext.keys())
    absClasses.sort()

    plt.figure(1)

    linkoSizes = range(args.minimum, args.maximum, args.step)

    plt.subplot(211)
    plt.plot(linkoSizes, results[:, 0])
    plt.xlabel("Size of Linkograph")
    plt.ylabel("Mean Shannon Entropy")
    plt.title("Mean Shannon Entropy vs. Linkograph Sizes")
    plt.grid(axis='both')

    plt.subplot(212)
    plt.plot(linkoSizes, results[:, 1])
    plt.xlabel("Size of Linkograph")
    plt.ylabel("Standard Deviation Shannon Entropy")
    plt.title("Standard Deviation Shannon Entropy vs. Linkograph Sizes")

    plt.tight_layout()

    plt.show()
