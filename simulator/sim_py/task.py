import argparse
import pandas as pd
from collections import namedtuple
from contacts import generate_contact_plan
from solver import solve, plot_solution
from simulator import run_simulation


scenario1 = {
    "id": 1,
    "start": 1588054885,  # 1588050345,
    "duration": 12*3600,
    "step": 30,
    "satellites": [
        {"id": "STARLINK-1244", "node": 1, "tle1": "1 45196U 20012U   20094.58334491 -.00029761  00000-0 -20303-2 0  9999", "tle2": "2 45196  52.9956  50.6558 0001754  72.9283 341.9461 15.05609076  1716"},
        {"id": "STARLINK-1102", "node": 2, "tle1": "1 44920U 20001G   20094.58334491  .00050489  00000-0  34604-2 0  9999", "tle2": "2 44920  53.0009 350.6416 0001892  65.4641  85.7463 15.05571452 13382"},
        {"id": "STARLINK-1032", "node": 3, "tle1": "1 44737U 19074AA  20094.58334491 -.00005148  00000-0 -33442-3 0  9997", "tle2": "2 44737  53.0002 210.6425 0001072  82.8131 134.9394 15.05576243 22184"},
    ],
    "targets": [
        {"id": "stgo", "node": 10, "lat": -33.3833, "lon": -70.7833, "alt": 476},
        {"id": "saa", "lat": -15.0, "lon": -15, "alt": 0},
        {"id": "tokyo", "node": 11, "lat": 35.6830, "lon": 139.7670, "alt": 5},

    ],
    "tracks_file": "track_1_1588050345.csv",
    "contacts_file": "contacts_1_1588050345.csv"
}

task1 = {
    "id": 1,
    "start": {"id": "stgo", "cmd": None, "time": None},
    "end": {"id": "tokyo", "result": "data1", "time": None},
    "targets": [
        {"id": "saa", "cmd": "sim_take_data data1", "result": "data1", "time": None},
    ],
    "solution": [4, 6, 17, 51],  # None,
    "command": None
}

""" Example result for Task1
    Unnamed: 0           from             to       start         end  duration
7            4           stgo  STARLINK-1244  1588054905  1588055325       420
10           6  STARLINK-1244            saa  1588055655  1588056165       510
35          18  STARLINK-1244  STARLINK-1032  1588069935  1588070415       480
36          51  STARLINK-1032          tokyo  1588070715  1588071165       450

---> Example commands for Task1
fp_set_cmd_unix 1 0 1588054905 com_send_cmd STARLINK-1244 <- sat change
fp_set_cmd_unix 1 0 1588055655 take_daa data1; <- target command, data
                                v------<--- sat change, data;
fp_set_cmd_unix 1 0 1588069935 com_send_tm STARLINK-1032 data1; fp_set_cmd_unix 1 0 1588069935 com_send_cmd STARLINK-1032  <--- sat change
fp_set_cmd_unix 1 0 1588070715 com_send_tm tokyo data1 <- sat change, data


fp_set_cmd_unix 1 0 1588054905 com_send_cmd STARLINK-1244
    fp_set_cmd_unix 1 0 1588055655 take_daa data1;
    fp_set_cmd_unix 1 0 1588069935 com_send_tm STARLINK-1032 data1;
    fp_set_cmd_unix 1 0 1588069935 com_send_cmd STARLINK-1032
        fp_set_cmd_unix 1 0 1588070715 com_send_tm tokyo data1

----> Example result 2 for Task 1

    Unnamed: 0           from             to       start         end  duration
48          61           stgo  STARLINK-1032  1588079475  1588079745       270
58          66  STARLINK-1032            saa  1588086435  1588086885       450
62          69  STARLINK-1032          tokyo  1588088865  1588089405       540

fp_set 1588079475 com_send_cmd STARLINK-1032
fp_set 1588086435 take_data
fp_set 1588088865 com_send_tm tokyo DATA

[GND executes                                [ STARLINK-1032 CMD1       ][STARLINK-1032 CMD2                    ]]
fp_set 1588079475 com_send_cmd STARLINK-1032 fp_set 1588086435 take_data;fp_set 1588088865 com_send_tm tokyo DATA


    Unnamed: 0           from             to     start       end  duration
29          16           stgo  STARLINK-1244  0.374646  0.383853  0.500000
42          20  STARLINK-1244  STARLINK-1032  0.582153  0.593484  0.714286
58          66  STARLINK-1032            saa  0.836402  0.847025  0.642857
62          69  STARLINK-1032          tokyo  0.893768  0.906516  0.857143
Valid sequence
Backend Qt5Agg is interactive backend. Turning interactive mode on.
['fp_set_cmd_unix 1 0 1588066875 com_send_cmd STARLINK-1244 ', 'fp_set_cmd_unix 1 0 1588075665 com_send_cmd STARLINK-1032 ', 'fp_set_cmd_unix 1 0 1588086435 take_data;', '']


    Unnamed: 0           from             to     start       end  duration
7            4           stgo  STARLINK-1244  0.092068  0.101983  0.571429
10           6  STARLINK-1244            saa  0.109773  0.121813  0.785714
17          10  STARLINK-1244  STARLINK-1032  0.176346  0.187677  0.714286
19          41  STARLINK-1032          tokyo  0.184136  0.192635  0.428571
Valid sequence
Backend Qt5Agg is interactive backend. Turning interactive mode on.
['fp_set_cmd_unix 1 0 1588054905 com_send_cmd STARLINK-1244 ', 'fp_set_cmd_unix 1 0 1588055655 take_data;', 'fp_set_cmd_unix 1 0 1588058475 com_send_tm data1 fp_set_cmd_unix 1 0 1588058475 com_send_cmd STARLINK-1032 ', 'fp_set_cmd_unix 1 0 1588058805 com_send_tm tokyo data1 ']

"""
def generate_commands(solution, task, scenario):
    satellites = [sat["id"] for sat in scenario.get("satellites")]
    targets = [tgt["id"] for tgt in task.get("targets")]
    targets_dict = {tgt["id"]: tgt for tgt in task.get("targets")}
    data = None
    commands = []

    for i, row in solution.iterrows():
        time = row['start']
        # line = "fp_set {} ".format(row['start'])
        line = ""
        # Case: X->SAT use 'com_send_cmd SAT'
        if row['to'] in satellites:
            if data:
                line += "fp_set_cmd_unix 1 0 {} sim_send_data {} {}".format(time, row['to'], data)
            line += "fp_set_cmd_unix 1 0 {} com_send_cmd {} ".format(time, row['to'])

        # Case: target SAT->TGT use 'task target command'
        elif row['to'] in targets:
            line += "fp_set_cmd_unix 1 0 {} {};".format(time, targets_dict[row['to']]['cmd'])
            # DATA <- data
            _data = targets_dict[row['to']].get('result', None)
            data = _data if _data is not None else data

        # Case: SAT -> GND use 'send_tm
        else:
            if data:
                line += "fp_set_cmd_unix 1 0 {} sim_send_data {} {} ".format(time, row['to'], data)
                data = None

        commands.append(line)

    print(commands)
    return "".join(commands)


def main(scenario=scenario1, task=task1):
    # scenario = namedtuple("Scenario", scenario.keys())(*scenario.values())
    # task = namedtuple("Task", task.keys())(*task.values())

    # Generate or load track and contact plan
    if scenario.get("tracks_file") is None or scenario.get("contacts_file") is None:
        tracks, contacts = generate_contact_plan(scenario.get("satellites"), scenario.get("targets"), scenario.get("start"), scenario.get("duration"), scenario.get("step"))
        track_filename = "track_{}_{}.csv".format(scenario.get("id"), scenario.get("start"))
        contacts_filename = "contacts_{}_{}.csv".format(scenario.get("id"), scenario.get("start"))
        tracks.to_csv(track_filename, index=False)
        contacts.to_csv(contacts_filename, index=False)
    else:
        tracks, contacts = pd.read_csv(scenario.get("tracks_file")), pd.read_csv(scenario.get("contacts_file"))

    if task.get("solution") is None:
        seq = [task.get("start")] + task.get("targets") + [task.get("end")]
        seq = [s["id"] for s in seq]
        solution_seq, fitness, average = solve(contacts, seq, mut=0.6, size=70)
        solution = contacts.iloc[solution_seq]
        task["solution"] = solution
    else:
        solution = contacts.iloc[task.get("solution")]

    #plot_solution(contacts, solution)
    check_solution(solution, task)

    if task.get("command") is None:
        commands = generate_commands(solution, task, scenario)
        task["command"] = commands
    print(task["command"])

    run_simulation(task, scenario, tty=8)


def check_solution(solution, task):
    assert solution.iloc[0]['from'] == task["start"]["id"]
    assert solution.iloc[-1]['to'] == task["end"]["id"]
    for tgt in task["targets"]:
        assert tgt["id"] in solution.iloc[1:-1]['to'].to_list()
    print("Valid sequence")


def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", metavar='FILE', help="File with access list")
    parser.add_argument("target", metavar='TGT', nargs='+', help="Target list")
    parser.add_argument("-s", "--size", default=50, type=int, help="Population size")
    parser.add_argument("-m", "--mut", default=0.3, type=float, help="Mutation rate")
    parser.add_argument("-i", "--iter", default=100, type=int, help="Max. iterations")
    return parser.parse_args()


if __name__ == '__main__':
    # args = get_parameters()
    main()