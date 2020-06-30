# -*- coding: utf-8 -*-
"""Taller Clase 2.ipynb

Original file is located at
    https://colab.research.google.com/drive/1dWmbE09BeRSYnECNecOwvBYoHaklB0HZ

**Session 2: Genetic Algorithm**

This practical session provides the complete implementation of a genetic algorithm.

Feedback may be sent to Juan-Pablo Silva (jpsilva@dcc.uchile.cl), Alexandre Bergel (abergel@dcc.uchile.cl)

The class `GA` given above provides all the necessary to use genetic algorithm to solve a particular problem.

## Changelog

# 03-06-2020
 - Authors: Carlos Gonzalez C. carlgonz@uchile.cl
 - Changes:
    - Use numpy.
    - get_best_individual also return best index
    - eval_population method
    - Add some instance variables
    - Style fixes
"""

import time
import random
import numpy as np


# Define the main class of the genetic algorithm
class GA(object):
    # pop_size is the size of the population. E.g., 1000
    # mutation_rate is the rate of a gene mutation. E.g., 0.1
    # fitness is a function that takes an individual as argument.
    #   E.g. lambda genes: sum(collections.Counter(genes))
    # individual_factory is a lambda that creates an individual.
    #   E.g., lambda : [ random.randint(0,10) for i in range(4) ]
    # gene_factory is a function that produces a new gene
    # termination_condition is the termination condition that takes as argument the fitness of the best element.
    # If it returns True, then the algorithm ends
    #   E.g., lambda fitness : fitness >= 3
    # max_iter is the maximum number of iterations
    def __init__(self, pop_size, mutation_rate, fitness, individual_factory, gene_factory, termination_condition,
                 max_iter=100, silent=False):
        self.population_size = pop_size
        self.mutation_rate = mutation_rate
        self.fitness_function = fitness
        self.individual_factory = individual_factory
        self.max_iterations = max_iter
        self.termination_condition = termination_condition
        self.gene_factory = gene_factory
        self.population = list()
        self.individual_fitnesses = list()
        self.silent = silent
        self.best_index = None
        self.best_individual = None

        # Internal variables
        self._best_fitness_list = list()
        self._avg_list = list()

    # main method to actually run the algorithm
    # return a tupple best_fitness_list, avg_list, best_individual
    def run(self):
        current_iteration = 0

        # We generate the initial population
        ti = time.time()
        self.population = self.generate_population()
        # Evaluate current population
        self.eval_population()

        # We loop if we have not reached the maximum number of iterations and if the termination condition is not met
        while current_iteration <= self.max_iterations and not self.termination_condition(self.fitness_function(self.best_individual)):
            self.log("Iter {} of {}. Took {} s".format(current_iteration, self.max_iterations, time.time()-ti))
            ti = time.time()

            # Create a new population
            new_population = []
            for _ in range(self.population_size):
                parent1 = self.tournament(self.population)
                parent2 = self.tournament(self.population)
                new_population.append(self.create_new_individual(parent1, parent2))
            self.population = new_population

            # Evaluate new population
            self.eval_population()
            current_iteration += 1

        self.log("Best found is: {}\nFitness: {}. Avg: {}".format(self.best_individual, self._best_fitness_list[-1], self._avg_list[-1]))
        return self.best_individual

    # Logging 
    def log(self, aString):
        if not self.silent:
            print(aString)

    # Evaluate current population (self.population)
    # Update individuals fitness list, best individual and best index
    # Also update performance metrics (for further analysis)
    def eval_population(self):
        self.individual_fitnesses = self.get_fitness(self.population)
        self.best_index, self.best_individual = self.get_best_individual()
        self._best_fitness_list.append(self.individual_fitnesses[self.best_index])
        self._avg_list.append(np.mean(self.individual_fitnesses))
        self.log("Best is: {}. Fitness: {:01.4f}. Avg: {:01.4f}".format(self.best_individual, self._best_fitness_list[-1], self._avg_list[-1]))

    # return the best individual of the current population
    def get_best_individual(self):
        index = np.argmax(self.individual_fitnesses)
        return index, self.population[index]

    # generate the population, made of individuals
    def generate_population(self):
        _population = list()
        for _ in range(self.population_size):
            _population.append(self.individual_factory())
        return _population

    # Return the list of the fitness values for the population
    def get_fitness(self, aPopulation):
        res = np.array(list(map(self.fitness_function, aPopulation)))
        return res

    # Obtain the best individual from a tournament on the population
    def tournament(self, a_population, k=5):
        best = None
        best_fitness = -1
        for _ in range(1, k):
            ind = random.choice(a_population)
            if best is None or (self.fitness_function(ind) > best_fitness):
                best = ind
                best_fitness = self.fitness_function(ind)
        return best

    # create a new individual from two parents elements
    def create_new_individual(self, parent1, parent2):
        final_child = self.crossover(parent1, parent2)
        # mutation
        if random.random() < self.mutation_rate:
            self.mutate(final_child)
        return final_child

    # crossover operation
    # crossover([1,2,3,4], [10,20,30,40])
    # => [1, 20, 30, 40]
    def crossover(self, individual1, individual2):
        _tmp = random.randint(1, len(individual1))
        return individual1[:_tmp] + individual2[_tmp:]

    # Mutate an individual
    # Note that this method does a side effect. I.e., it does not create a new individual
    def mutate(self, an_individual):
        index = random.randrange(len(an_individual))
        an_individual[index] = self.gene_factory()
