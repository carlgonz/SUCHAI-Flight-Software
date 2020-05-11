# -*- coding: utf-8 -*-
"""Taller Clase 2.ipynb

Original file is located at
    https://colab.research.google.com/drive/1dWmbE09BeRSYnECNecOwvBYoHaklB0HZ

**Session 2: Genetic Algorithm**

This practical session provides the complete implementation of a genetic algorithm.

Feedback may be sent to Juan-Pablo Silva (jpsilva@dcc.uchile.cl), Alexandre Bergel (abergel@dcc.uchile.cl)

The class `GA` given above provides all the necessary to use genetic algorithm to solve a particular problem.
"""

import copy
import random
import string
import numpy as np


# Define the main class of the genetic algorithm
class GA:
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
        self.individualFactory = individual_factory
        self.max_iterations = max_iter
        self.termination_condition = termination_condition
        self.gene_factory = gene_factory
        self.population = list()
        self.individual_fitnesses = list()
        self.silent = silent

    # main method to actually run the algorithm
    # return a tupple best_fitness_list, avg_list, best_individual
    def run(self):
        current_iteration = 0
        best_fitness_list = list()
        avg_list = list()

        # We generate the initial population
        self.population = self.generate_population()

        # We compute all the fitnesses. It is a collection of fitness values, of the same size than the population
        self.individual_fitnesses = self.get_fitness(self.population)

        # We get the best_individual of the current population
        best_individual = self.get_best_individual()

        # We loop if we have not reached the maximum number of iterations and if the termination condition is not met
        while current_iteration <= self.max_iterations and not self.termination_condition(self.fitness_function(best_individual)):
            self.log("iter {} of {}".format(current_iteration, self.max_iterations))

            best_fitness_list.append(max(self.individual_fitnesses))
            avg_list.append(np.mean(self.individual_fitnesses))

            self.log("best is: {}\nwith {} acc. Avg: {}".format(best_individual, best_fitness_list[-1], avg_list[-1]))

            # self.log("Poulation\n {}".format(self.population))

            # we create a new population
            new_population = []
            for _ in range(self.population_size):
                parent1 = self.tournament(self.population)
                parent2 = self.tournament(self.population)
                new_population.append(self.create_new_individual(parent1, parent2))

            self.population = new_population
            self.individual_fitnesses = self.get_fitness(self.population)
            current_iteration += 1
            best_individual = self.get_best_individual()

        last_fitness = self.get_fitness(self.population)
        best_individual = self.population[last_fitness.index(max(last_fitness))]

        best_fitness_list.append(max(last_fitness))
        avg_list.append(np.mean(last_fitness))

        self.log("best found is: {}\nwith {} acc. Avg: {}".format(best_individual, best_fitness_list[-1], avg_list[-1]))

        return best_fitness_list, avg_list, best_individual

    # Logging 
    def log(self, aString):
        if not self.silent:
            print(aString)

    # return the best individual of the current population
    def get_best_individual(self):
        return self.population[self.individual_fitnesses.index(max(self.individual_fitnesses))]

    # generate the population, made of individuals
    def generate_population(self):
        _population = list()
        for _ in range(self.population_size):
            _population.append(self.individualFactory())
        return _population

    # Return the list of the fitness values for the population
    def get_fitness(self, aPopulation):
        return list(map(self.fitness_function, aPopulation))

    # Obtain the best individual from a tournament on the population
    def tournament(self, aPopulation, k=5):
        best = None
        best_fitness = -1
        for _ in range(1, k):
            ind = random.choice(aPopulation)
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
        # return final_child
        return sorted(set(final_child))

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
