#!/usr/bin/env python3
"""
Constellation Control Framework
--------------------------------
Evolutive Contact Plan Design

:Date: 2002-06
:Version: 1
:Author: Carlos Gonzalez C. carlgonz@uchile.cl
"""

import time
import argparse
import numpy as np
import pandas as pd
from random import choices
import matplotlib.pyplot as plt
from ga import GA
from definitions import *
from plot_results import plot_contact_list


class GeneticCPD(GA):
    def __init__(self, contact_list: pd.DataFrame, scenario: Scenario, task: Task, pop_size: int, mutation_rate: float,
                 max_iter: int = 100, silent: bool = False):
        """
        Contact plan design using genetic algorithm
        :param contact_list: DataFrame. Contact list table
        :param task_nodes: List. List of task target node numbers (start, <targets>, end)
        :param relays: List. List of node numbers that are relays (satellites and stations)
        :param targets: List. List of node numbers that are not relays (targets)
        :param pop_size: Int. Initial population size
        :param mutation_rate: Float. Mutation rate
        :param max_iter: Int. Max. number of iterations
        :param silent: Bool. Mute logs
        """
        # GA variables
        self.population_size = pop_size
        self.mutation_rate = mutation_rate
        self.max_iterations = max_iter
        self.population = list()
        self.silent = silent
        self.individual_fitnesses = list()
        self.best_index = None
        self.best_individual = None

        # Contact list and contact plan
        self.scenario = scenario
        self.task = task
        self.contact_list = contact_list
        self.contact_plan = None

        # Internal performance variables
        self._time = -1
        self._tmp_fit = list()
        self._best_fitness_list = list()
        self._avg_list = list()
        self._multi_fitness_list = list()

    def individual_factory(self):
        """
        Creates a new individual: random length list with random values,
        ie, a random set of contact index
        :return: List
        """
        # len_task = len(self.task_nodes)  # Targets + start + end
        # seq = sorted(set([self.gene_factory() for i in range(np.random.randint(len_task, 3*len_task))]))
        # print(seq)
        seq = choices([True, False], [1, 10], k=len(self.contact_list))
        return seq

    def gene_factory(self):
        """
        Return a gene: a random contact list index
        :return: Int
        """
        # return np.random.randint(self.contact_list.index[0], self.contact_list.index[-1])
        return choices([True, False], [2, 1])[0]

    def termination_condition(self, fitness):
        """
        Evaluate stopping the algorithm.
        Check if a local maximum was reached (std==0) or fitness > 0.95
        :param fitness: Float. Current fitness value
        :return: Bool.
        """
        valid = fitness[1]
        fitness = fitness[0]
        self._tmp_fit.append(fitness)
        if len(self._tmp_fit) < 20:
            return False
        else:
            std = np.std(self._tmp_fit[-10:-1])
            print("Tmp fitness std:", std)
            if fitness > 0.8 and valid > 0.99:
                return True
            elif std < 1e-10:
                self.log("Creating new population!")
                for i in self.population:
                    for j in range(10):
                        self.mutate(i)
                return False
            else:
                return False

    def eval_population(self):
        """
        Evaluate current population (self.population), multi-objective case
        Update individuals fitness list, best individual and best index
        Also update performance metrics (for further analysis)
        :return:  None
        """
        _individual_fitnesses = self.get_fitness(self.population)
        self.individual_fitnesses = _individual_fitnesses[:, 0]
        self.best_index, self.best_individual = self.get_best_individual()
        self._best_fitness_list.append(self.individual_fitnesses[self.best_index])
        self._avg_list.append(np.mean(self.individual_fitnesses))
        self._multi_fitness_list.append(_individual_fitnesses[self.best_index])
        self.log("Fitness: {:01.4f}. Avg: {:01.4f}. Variables: [{:01.4f}, {:01.4f}, {:01.4f}, {:01.4f}]".format(
            self._best_fitness_list[-1], self._avg_list[-1], *self._multi_fitness_list[-1]))

    def fitness_function(self, individual):
        """
        Evaluate fitness function:
        fitness = \alpha*(1-V_i)+\beta*(1-D_i)+\gamma*(1-I_i)
        \alpha + \beta + \gamma = 1
        V_i <= D_i <= S_i <= 1
        V_i &= \sum^5_{j=1}(\omega_jR_j)/length(S_i)

        :param individual: List. Individual to evaluate
        :return: Float.
        """
        contact_list = self.contact_list
        task_nodes = [self.scenario.get(tgt.id).node for tgt in self.task.targets]
        relay_nodes = [node.node for node in self.scenario.satellites+self.scenario.stations]
        target_nodes = [node.node for node in self.scenario.targets]

        individual = np.arange(len(contact_list))[individual]
        if len(individual) == 0:
            return 0, 0, 0, 0

        # Start time: the earlier the better
        start = 1 - contact_list.loc[individual[0], COL_START]
        # Total time: the shortest te better
        total_time = 1 - (contact_list.loc[individual[-1], COL_END] - contact_list.loc[individual[0], COL_START])
        # Validity: more valid the sequence the better (starts 100% valid)
        max_valid = len(individual)
        valid = max_valid
        penalty = 1

        # Calculate sequence validity (decreasing if not follows the criteria)
        from_list = contact_list.loc[individual, COL_FROM].values
        to_list = contact_list.loc[individual, COL_TO].values

        # R1-R2: Must start and finish according to task
        if from_list[0] != self.scenario.get(self.task.start).node:
            valid -= penalty
        if to_list[-1] != self.scenario.get(self.task.end).node:
            valid -= penalty
        # R3: Must contain the task targets
        to_targets = list(to_list)[1:-1]
        for task_node, target in zip(task_nodes, self.task.targets):
            # Penalty if target no in the list, except if the target priority is 0
            if task_node not in to_targets and target.prio > 0:
                valid -= penalty
            # Remove the target from the list, to check repeated targets
            else:
                to_targets.remove(task_node)

        # R4-R5: Interlink rules
        for i in range(len(from_list) - 1):
            # R5 Satellite to satellite. from[:]->to[2] then from[2]->to[:]
            if (to_list[i] in relay_nodes) and (to_list[i] != from_list[i + 1]):
                valid -= penalty
            # R5 Satellite to target. from[1]->to[x] then from[1]->to[:]
            if (to_list[i] in target_nodes) and (from_list[i] != from_list[i + 1]):
                valid -= penalty

        valid = 0 if valid < 0 else valid
        valid = valid / max_valid
        length = 1 - len(individual)/len(self.contact_list)

        a, b, c = (0.60, 0.20, 0.20)
        result = a*valid + b*total_time + c*length
        return result, valid, total_time, length

    def run(self):
        # Normalize values (times: earlier are better, duration less is better)
        self.contact_list = self.contact_list.sort_values(COL_START, ignore_index=True)
        _tmp_contact_list = self.contact_list.copy()
        self.contact_list[[COL_START, COL_END]] -= self.contact_list[[COL_START, COL_END]].min().min()
        self.contact_list[[COL_START, COL_END]] /= self.contact_list[[COL_START, COL_END]].max().max()
        self.contact_list[COL_DT] -= self.contact_list[COL_DT].min()
        self.contact_list[COL_DT] /= self.contact_list[COL_DT].max()

        ti = time.time()
        best_individual = GA.run(self)
        self._time = time.time() - ti

        self.contact_list[[COL_START, COL_END, COL_DT]] = _tmp_contact_list[[COL_START, COL_END, COL_DT]]
        best_individual_original = self.contact_list.iloc[best_individual]['access'].to_list()
        self.contact_plan = self.contact_list.iloc[self.best_individual]
        self.log("Solution is: {}, Fitness: {}. Time {}s".format(best_individual_original, self._best_fitness_list[-1], self._time))
        return best_individual_original, self._best_fitness_list[-1]

    def plot_results(self, scenario: Scenario = None):
        """"
        Show and plot results
        """
        plot_contact_list(self.contact_list, scenario, self.contact_plan)

        # Plot multi objective fitness values
        vars = ["Fitness", "Valid", "Total time", "Start time"]
        fitness_vars = np.array(self._multi_fitness_list).T
        fig, axs = plt.subplots(len(fitness_vars)+1, sharey=True, sharex=True)
        fig.suptitle("Fitness variables")
        for i, var in enumerate(fitness_vars):
            axs[i].plot(var)
            axs[i].grid()
            axs[i].set(ylabel=vars[i])
        axs[i+1].plot(self._avg_list)
        axs[i+1].grid()
        axs[i+1].set(xlabel='Generation', ylabel='Fitness avg.')

        plt.show()


def get_parameters():
    """
    Parse command line parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", metavar='SCENARIO', help="File with access list")
    parser.add_argument("task", metavar='TASK', help="Task file")
    parser.add_argument("-s", "--size", default=50, type=int, help="Population size")
    parser.add_argument("-m", "--mut", default=0.6, type=float, help="Mutation rate")
    parser.add_argument("-i", "--iter", default=100, type=int, help="Max. iterations")
    return parser.parse_args()


if __name__ == "__main__":
    import json
    args = get_parameters()

    # Load scenario and task definition
    with open(args.scenario) as scenario_file:
        scenario_json = json.load(scenario_file)
    with open(args.task) as task_file:
        task_json = json.load(task_file)

    # Load scenario, task and contact list
    scenario = Scenario(scenario_json)
    task = Task(task_json)
    assert(scenario.contacts is not None)
    contacts = pd.read_csv(scenario.contacts)

    # Run Genetic Algorithm
    cpd = GeneticCPD(contacts, scenario, task, args.size, args.mut, args.iter, False)
    solution, fitness = cpd.run()
    print(contacts.iloc[solution])
    cpd.plot_results(scenario)