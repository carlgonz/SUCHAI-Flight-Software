#!/usr/bin/env python3
"""
Constellation Control Framework
--------------------------------
Framework entry point

:Date: 2002-06
:Version: 1
:Author: Carlos Gonzalez C. carlgonz@uchile.cl
"""

import time
import json
import argparse
import pandas as pd
from datetime import datetime
from skyfield.api import EarthSatellite, Topos, load, utc
from definitions import *
from cpd import GeneticCPD
# from simulator import run_simulation


class ConstellationController(object):
    def __init__(self, scenario, task=None):
        self.scenario = scenario
        self.task = task
        self._contact_list = None
        self._contact_plan = None
        self._flight_plan = None

    def contact_list(self, track_fname=None, contacts_fname=None):
        """
        Generate the contact list of the scenario
        :param track_fname: String. Tracks filename
        :param contacts_fname: String. Contact list filename
        :return: DataFrame. Contact list
        """
        if not self.scenario:
            raise AttributeError("Scenario not initialized!")

        start = self.scenario.start
        sim_time = self.scenario.duration
        dt = self.scenario.step
        times = list(range(start, start + sim_time, dt))
        ts = load.timescale()

        stations = {gs.node: Topos(latitude_degrees=gs.lat, longitude_degrees=gs.lon, elevation_m=gs.alt) for gs in self.scenario.stations}
        targets = {tgt.node: Topos(latitude_degrees=tgt.lat, longitude_degrees=tgt.lon, elevation_m=tgt.alt) for tgt in self.scenario.targets}
        sats = {sat.node: EarthSatellite(sat.tle1, sat.tle2, sat.id, ts) for sat in self.scenario.satellites}

        dt = {t: ts.utc(datetime.fromtimestamp(t, utc)) for t in times}
        mi2 = pd.MultiIndex.from_product([sats.keys(), dt.keys()], names=['node', 'time'])

        # Satellite positions
        latlot = lambda topos: {"lat": topos.latitude.degrees, "lon": topos.longitude.degrees, "alt": topos.elevation.m}
        pos = [latlot(sats[s].at(dt[t]).subpoint()) for s, t in mi2]
        pos = pd.DataFrame(pos, index=mi2)

        # Satellite to ground station contacts
        gs_visible = lambda sat, t: {name: (sat - station).at(t).altaz()[0].degrees > 5 for name, station in stations.items()}
        gs_contacts = [gs_visible(sats[s], dt[t]) for s, t in mi2]
        gs_contacts = pd.DataFrame(gs_contacts, index=mi2)

        # Satellite to targets contacts
        tgt_visible = lambda sat, t: {name: (sat - target).at(t).altaz()[0].degrees > 5 for name, target in targets.items()}
        tgt_contacts = [tgt_visible(sats[s], dt[t]) for s, t in mi2]
        tgt_contacts = pd.DataFrame(tgt_contacts, index=mi2)

        # Satellite to satellite contacts
        interlink = lambda sat, t: {name: 0 < (sat - sat2).at(t).distance().km < 3000 for name, sat2 in sats.items()}
        isl_contacts = [interlink(sats[s], dt[t]) for s, t in mi2]
        isl_contacts = pd.DataFrame(isl_contacts, index=mi2)

        # Build tracks datafile
        tracks = pos.join(gs_contacts).join(tgt_contacts).join(isl_contacts)
        track_fname = "logs/" + time.strftime("%Y%m%d%H%M%S") + "_tracks.csv" if track_fname is None else track_fname
        tracks.to_csv(track_fname, index=False)

        # TODO: Optimize this code
        # Build contacts list datafile
        names = list(stations.keys()) + list(targets.keys()) + list(sats.keys())
        targets = list(stations.keys())
        tmp = {}
        contacts = []
        tracks.loc[mi2[0], names] = False  # Pre-condition
        for i in range(len(mi2) - 1):
            for to in names:
                if (tracks.loc[mi2[i], [to]] ^ tracks.loc[mi2[i + 1], [to]]).any():
                    if tmp.get(to, None):
                        tmp[to]['end'] = mi2[i][1]
                        tmp[to]['duration'] = tmp[to]['end'] - tmp[to]['start']
                        contacts.append(tmp[to].copy())
                        # Make sat to target bidirectional
                        if to in targets:
                            tmp[to]["to"] = tmp[to]["from"]
                            tmp[to]["from"] = to
                            contacts.append(tmp[to].copy())
                        del tmp[to]
                    else:
                        tmp[to] = {"from": mi2[i][0], "to": to, "start": mi2[i + 1][1], "end": None, "duration": None}

        contacts = pd.DataFrame(contacts)
        contacts['access'] = contacts.index
        # Save contact list to file
        contacts_fname = track_fname.replace("_tracks", "_contacts") if contacts_fname is None else contacts_fname
        contacts.to_csv(contacts_fname, index=False)

        self.scenario.contacts = contacts_fname
        self.scenario.tracks = track_fname
        self._contact_list = contacts

        return contacts

    def contact_plan(self, contact_fname=None):
        """
        Creates the contact plan using the evolutive contact plan design (CPD)
        :return: DataFrame
        """
        # Define target as node list
        task_nodes = [self.scenario.node(_id).node for _id in self.task.ids()]
        relay_nodes = [n.node for n in self.scenario.satellites+self.scenario.stations]
        target_nodes = [n.node for n in self.scenario.targets]
        # Genetic Evolutive Plan Design
        cpd = GeneticCPD(self._contact_list, task_nodes, relay_nodes, target_nodes, 25, 0.6, 100, False)
        solution, fitness = cpd.run()
        # Save results
        contact_fname = "logs/" + time.strftime("%Y%m%d%H%M%S") + "_contact_plan.csv" if contact_fname is None else contact_fname
        self._contact_plan = self._contact_list.iloc[solution]
        self._contact_plan.to_csv(contact_fname, index=False)
        cpd.plot_results()
        return self._contact_plan

    def check_contact_plan(self):
        """
        Check contact plan validity against rules R1-R5
        :return: Bool
        """
        try:
            assert self._contact_plan.iloc[0][COL_FROM] == self.scenario.node(self.task.start).node
            assert self._contact_plan.iloc[-1][COL_TO] == self.scenario.node(self.task.end).node
            for tgt in self.task.targets:
                assert self.scenario.node(tgt.id).node in self._contact_plan.iloc[1:-1][COL_TO].to_list()
        except AssertionError:
            print("Invalid sequence")
            return False
        print("Valid sequence")
        return True

    def flight_plan(self, plan_fname=None):
        """
        Generate a Flight Plan table from the contact plan table,
        task and scenario definitions.
        :param contact_plan: DataFrame. Contact plan table
        :param task: Task. Task definition
        :param scenario: Scenario. Scenario definition
        :return: DataFrame. Flight plan table
        """
        if self.task is None or self._contact_plan is None:
            raise AttributeError("Task or contact plan not initialized!")

        sat_sta_nodes = [sat.node for sat in self.scenario.satellites+self.scenario.stations]
        target_nodes = {self.scenario.node(tgt.id).node: tgt for tgt in self.task.targets}
        data = None
        flight_plan = []

        for i, row in self._contact_plan.iterrows():
            time = row['start']
            fp_entry = {"time": time, "node": row["from"], "command": None}

            # Case: X->SAT|GND use 'fp_send NODE'
            if row['to'] in sat_sta_nodes:
                fp_entry["command"] = "fp_send {}".format(row['to'])
                flight_plan.append(fp_entry)
                if data:  # Transfer data if required
                    fp_entry_data = {"time": time+1, "node": row["from"],
                                     "command": "send_data {} {}".format(row["to"], data)}
                    flight_plan.append(fp_entry_data)

            # Case: target SAT->TGT use 'task target command'
            elif row['to'] in target_nodes.keys():
                fp_entry["command"] = target_nodes[row['to']].command
                flight_plan.append(fp_entry)
                # DATA <- data
                _data = target_nodes[row['to']].result
                data = _data if _data is not None else data

        self._flight_plan = pd.DataFrame(flight_plan)
        print(self._flight_plan)
        # Save results
        plan_fname = "logs/" + time.strftime("%Y%m%d%H%M%S") + "_flight_plan.csv" if plan_fname is None else plan_fname
        self._flight_plan.to_csv(plan_fname, index=False)
        self.task.solution = plan_fname
        return self._flight_plan


def main(scenario_path, task_path):
    """
    Constellation control framework entry point
    :param scenario_path: Str. Path to scenario definition json
    :param task_path: Str. Path to task definition json
    :return: None
    """
    # Load scenario and task definition
    with open(scenario_path) as scenario_file:
        scenario_json = json.load(scenario_file)
    with open(task_path) as task_file:
        task_json = json.load(task_file)
    scenario = Scenario(scenario_json)
    task = Task(task_json)
    controller = ConstellationController(scenario, task)

    # Generate or load tracks, contact list
    if controller.scenario.tracks is None or controller.scenario.contacts is None:
        track_filename = "logs/track_{}_{}.csv".format(scenario.id, scenario.start)
        contacts_filename = "logs/contacts_{}_{}.csv".format(scenario.id, scenario.start)
        controller.contact_list(track_filename, contacts_filename)
    else:
        tracks, contacts = pd.read_csv(scenario.tracks), pd.read_csv(scenario.contacts)
        controller._contact_list = contacts

    # Create or load contact_plan and contact_list
    if task.solution is None:
        contact_plan_fname = "logs/contact_plan_{}_{}.csv".format(task.id, scenario.start)
        flight_plan_fname = "logs/flight_plan_{}_{}.csv".format(task.id, scenario.start)
        ok = False
        while not ok:
            controller.contact_plan(contact_plan_fname)
            ok = controller.check_contact_plan()
        controller.flight_plan(flight_plan_fname)
    else:
        solution = pd.read_csv(task.solution)
        controller._flight_plan = solution

    # Run simulation
    # run_simulation(task, scenario, tty=8)


def get_parameters():
    """
    Parse command line parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", metavar='SCENARIO', help="File with access list")
    parser.add_argument("task", metavar='TASK', help="Task file")
    parser.add_argument("-s", "--size", default=50, type=int, help="Population size")
    parser.add_argument("-m", "--mut", default=0.3, type=float, help="Mutation rate")
    parser.add_argument("-i", "--iter", default=100, type=int, help="Max. iterations")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_parameters()
    main(args.scenario, args.task)
