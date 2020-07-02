#!/usr/bin/env python3
"""
Constellation Control Framework
--------------------------------
Plots

:Date: 2002-06
:Version: 1
:Author: Carlos Gonzalez C. carlgonz@uchile.cl
"""

import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from matplotlib.patches import Rectangle


from definitions import *

LAT_COL = "lat"
LON_COL = "lon"
NODE_COL = "node"


def plot_tracks(tracks: pd.DataFrame, scenario: Scenario, figname: str = None):
    """
    Plot constellation tracks
    :param tracks: DataFrame. Tracks table.
    :param scenario: Scenario. Scenario definition.
    :param figname: Str. Filename to save figure
    :return: None
    """
    plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())
    #ax.stock_img()
    # ax.add_feature(cfeature.OCEAN, zorder=0, facecolor='lightblue')
    ax.add_feature(cfeature.LAND, zorder=0, edgecolor='lightgray', facecolor='lightgray')

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    plt.title("Satellite tracks and contacts")

    t = ax.scatter(tracks[LON_COL], tracks[LAT_COL], c=tracks[NODE_COL], vmin=-3, vmax=3, s=10, cmap='BuGn')
    # produce a legend with the unique colors from the scatter
    legend1 = ax.legend(*t.legend_elements(), title="Node",  loc="upper left")
    ax.add_artist(legend1)
    contact = tracks[[str(n) for n in [1, 2, 3, 4, 5, 6]]].sum(axis=1) > 0
    t = ax.scatter(tracks[LON_COL], tracks[LAT_COL], s=contact*10, c=contact)

    for s in scenario.stations+scenario.targets:
        ax.scatter(s.lon, s.lat, s=[50], c='r')
        ax.scatter(s.lon, s.lat, s=[1000], facecolors='none', edgecolor='r', alpha=0.5)
        ax.text(s.lon+1, s.lat+1, s.id)

    if figname:
        plt.savefig(figname)
    else:
        plt.show()


def plot_contact_list(contacts: pd.DataFrame, scenario: Scenario = None, contact_plan: pd.DataFrame = None,
                      plot_duration=False, figname: str = None):

    contacts = contacts.copy()
    start = contacts[COL_START].min()
    contacts.loc[:, [COL_START]] -= start
    access_x = contacts.loc[:, [COL_START, COL_START]].values
    access_y = contacts.loc[:, [COL_FROM, COL_TO]].values

    fig, ax = plt.subplots(1, 1)

    # Plot contact list duration
    if plot_duration:
        width = contacts[COL_DT].values
        height = abs(np.diff(access_y).flatten())
        rectangles = [Rectangle((access_x[i, 0], min(access_y[i, :])), width[i], height[i], alpha=0.5) for i in range(len(access_x))]
        for rect in rectangles:
            ax.add_artist(rect)

    # Plot contact list
    alpha = 0.7 if contact_plan is None else 0.3
    for i in range(len(access_x)):
        ax.plot(access_x[i], access_y[i], 'o-', color='gray', alpha=alpha)

    # Plot Contact Plan
    if contact_plan is not None:
        contact_plan = contact_plan.copy()
        contact_plan.loc[:, [COL_START]] -= start
        results_x = contact_plan.loc[:, [COL_START, COL_START]].values
        results_y = contact_plan.loc[:, [COL_FROM, COL_TO]].values
        for i in range(len(results_x)):
            res_plt, = plt.plot(results_x[i], results_y[i], 'ro-')

    if scenario is not None:
        labels = {d.node: "{}: {}".format(d.node, d.id) for d in scenario.satellites + scenario.stations + scenario.targets}
        plt.yticks(list(labels.keys()), list(labels.values()))

    plt.title("Contact list" if contact_plan is None else "Contact list and contact plan")
    plt.grid()
    plt.xlabel("Timestamp since {} (s) ".format(start))
    # plt.ylabel("Nodes")

    if figname:
        plt.savefig(figname)
    else:
        plt.show()


def get_parameters():
    """
    Parse command line parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", metavar='SCENARIO', help="File with access list")
    parser.add_argument("task", metavar='TASK', help="Task file")
    parser.add_argument("-t", "--tracks", action="store_true", help="Plot tracks")
    parser.add_argument("-c", "--contacts", action="store_true", help="Plot contact list")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_parameters()

    # Load scenario and task definition
    with open(args.scenario) as scenario_file:
        scenario_json = json.load(scenario_file)
    with open(args.task) as task_file:
        task_json = json.load(task_file)

    # Load scenario, task and contact list
    scenario = Scenario(scenario_json)
    task = Task(task_json)

    if args.tracks:
        assert (scenario.tracks is not None)
        tracks = pd.read_csv(scenario.tracks)
        plot_tracks(tracks, scenario)

    if args.contacts:
        assert (scenario.contacts is not None)
        contacts = pd.read_csv(scenario.contacts)
        contact_plan = task.solution
        if contact_plan is not None:
            contact_plan = pd.read_csv(task.solution)
        plot_contact_list(contacts, scenario, contact_plan)
