#
# SUCHAI CONSTELLATION SOLVER
#
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ga import GA

targets = ["stgo", "tokyo"]
satellites = ["STARLINK-1244", "STARLINK-1102", "STARLINK-1032"]
col_start = "start"
col_end = "end"
col_from = "from"
col_to = "to"
col_dt = "duration"

fitness_vars = []
fitness_vars_adj = []
tmp_fit = []
objective = []
df = pd.DataFrame()
max_time = 0


def fitness(anIndividual):
    # Start time: the earlier the better
    start = 1-df.loc[anIndividual[0], col_start]
    # Total time: the shortest te better
    time = 1-(df.loc[anIndividual[-1], col_end] - df.loc[anIndividual[0], col_start])
    # Validity: more valid the sequence the better (starts 100% valid)
    valid = len(anIndividual)
    max_valid = valid

    # Calculate sequence validity (decreasing if not follows the criteria)
    from_list = df.loc[anIndividual, col_from].values
    to_list = df.loc[anIndividual, col_to].values

    # R1: Should start, finish and contain the target!
    if from_list[0] != objective[0]:
        valid -= 1
    if to_list[-1] != objective[-1]:
        valid -= 1
    for t in objective[1:-1]:
        if t not in list(to_list)[1:-1]:
            valid -= 1

    # R2: Interlink rules
    for i in range(len(from_list)-1):
        # R2.A Satellite to satellite. from[:]->to[2] then from[2]->to[:]
        if (to_list[i] in satellites) and (to_list[i] != from_list[i + 1]):
            valid -= 2
        # R2.B Satellite to target. from[1]->to[x] then from[1]->to[:]
        if (to_list[i] in targets) and (from_list[i] != from_list[i + 1]):
            valid -= 2

    valid = 0 if valid < 0 else valid
    valid = valid/max_valid

    a, b, c = (0.70, 0.28, 0.02)
    fitness_vars.append((valid, time, start))
    fitness_vars_adj.append((a*valid, b*time, c*start))
    result = a*valid + b*time + c*start
    return result


def gene_factory():
    return np.random.randint(df.index[0], df.index[-1])


def sequence_factory():
    seq = sorted(set([gene_factory() for i in range(np.random.randint(len(objective), 2*len(objective)))]))
    #print(seq)
    return seq


def termination_condition(fitness):
    tmp_fit.append(fitness)
    if len(tmp_fit) < 20:
        return False
    else:
        std = np.std(tmp_fit[-10:-1])
        print("Tmp fitness std:", std)
        return fitness > 0.94 or (fitness > 0.85 and std < 1e-10)


def plot_solution(df_all, df_solution, fitness, fitness_adj):
    """"
    Show and plot results
    """
    # Contact Plan
    access = df_all.set_index(col_start, inplace=False, drop=False)
    access_x = access.loc[:, [col_start, col_start]].values
    access_y = access.loc[:, [col_from, col_to]].values
    access_dt = np.log10(access.loc[:, col_dt].values * 0.0001+1e-6)

    plt.figure()
    for i in range(len(access_x)):
        res_plt, = plt.plot(access_x[i], access_y[i], 'o-', color='gray', alpha=0.7, linewidth=access_dt[i])

    results_x = df_solution.loc[:, [col_start, col_start]].values
    results_y = df_solution.loc[:, [col_from, col_to]].values

    for i in range(len(results_x)):
        res_plt, = plt.plot(results_x[i], results_y[i], 'r.--')

    plt.grid()
    plt.title("Contact plan")
    plt.xlabel("Time (s)")
    plt.ylabel("Satellites and targets")

    # Plot genetic algorithm variables
    vars = ["Valid", "Total time", "Start time"]
    global fitness_vars
    fitness_vars = np.array(fitness_vars).T
    plots = len(fitness_vars)
    plt.figure()
    plt.title("Fitness variables")
    for i, var in enumerate(fitness_vars):
        plt.subplot(plots, 1, i + 1)
        plt.plot(var)
        plt.grid()
        plt.ylabel(vars[i])

    global fitness_vars_adj
    fitness_vars_adj = np.array(fitness_vars_adj).T
    plots = len(fitness_vars_adj)
    plt.figure()
    plt.title("Fitness variables adjusted")
    for i, var in enumerate(fitness_vars_adj):
        plt.subplot(plots, 1, i + 1)
        plt.plot(var)
        plt.grid()
        plt.ylabel(vars[i])

    plt.figure()
    plt.plot(fitness)
    plt.plot(fitness_adj)
    plt.grid()
    plt.title("Fitness functions")
    plt.legend(["Best", "Average"])

    plt.show()


def solve(contacts, target, size=100, mut=0.3, iter=100):
    global objective
    objective = target
    global df
    df = contacts
    global targets
    targets = target
    global satellites
    satellites = [s for s in set(contacts[col_from].to_list() + contacts[col_to].to_list()) if s not in targets]

    # Normalize values (times: earlier are better, duration less is better)
    df = df.sort_values(col_start, ignore_index=True)
    _df = df.copy()
    df[[col_start, col_end]] -= df[[col_start, col_end]].min().min()
    df[[col_start, col_end]] /= df[[col_start, col_end]].max().max()
    df[col_dt] -= df[col_dt].min()
    df[col_dt] /= df[col_dt].max()

    ga = GA(pop_size=size, mutation_rate=mut, fitness=fitness, individual_factory=sequence_factory,
            gene_factory=gene_factory, termination_condition=termination_condition, silent=False, max_iter=iter)
    best_fitness_list, avg_list, best_individual = ga.run()

    print(df.iloc[best_individual])
    df[[col_start, col_end, col_dt]] = _df[[col_start, col_end, col_dt]]
    #df[[col_start, col_end]] -= df[[col_start, col_end]].min().min()

    return df.iloc[best_individual], best_fitness_list, avg_list


def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", metavar='FILE', help="File with access list")
    parser.add_argument("target", metavar='TGT', nargs='+', help="Target list")
    parser.add_argument("-s", "--size", default=50, type=int, help="Population size")
    parser.add_argument("-m", "--mut", default=0.3, type=float, help="Mutation rate")
    parser.add_argument("-i", "--iter", default=100, type=int, help="Max. iterations")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_parameters()
    contacts = pd.read_csv(args.filename)
    solution, fitness_best, fitness_avg = solve(contacts, args.target, args.size, args.mut, args.iter)
    solution.to_csv(args.filename+"_solution.csv")
    print(solution)
    plot_solution(df, solution, fitness_best, fitness_avg)

