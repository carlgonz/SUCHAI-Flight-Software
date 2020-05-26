#!/usr/bin/env python3

import sys
import time
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from skyfield.api import EarthSatellite, Topos, load, utc

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


def map_plot(df, lat='lat', lon='lon', sats=None):
    plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.stock_img()
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5)
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    plt.title("Satellite tracks and accesses")

    for i, (name, sat) in enumerate(df.groupby('name')):
        ax.scatter(sat[lon], sat[lat], c=sat[[n for n in sats if n != name]].sum(axis=1)>0)

    plt.show()


def access_plot(access=pd.DataFrame(), _from='from', _to='to', _start='start', end='end', _width='duration', sats=None):
    if sats is None:
        codes = {k: i for i, k in enumerate(sorted(set(access[_to].values.tolist() + access[_from].values.tolist())))}
    else:
        codes = {k: i for i, k in enumerate(sats)}

    access[_to+'i'] = [codes[k] for k in access[_to]]
    access[_from+'i'] = [codes[k] for k in access[_from]]
    access_x = access.loc[:, [_start, _start]].values
    access_y = access.loc[:, [_from+'i', _to+'i']].values
    width = access[_width].values
    height = abs(np.diff(access_y).flatten())

    rectangles = [Rectangle((access_x[i, 0], min(access_y[i, :])), width[i], height[i], alpha=0.5) for i in range(len(access_x))]

    fig, ax = plt.subplots(1, 1)
    for rect in rectangles:
        ax.add_artist(rect)

    # plt.figure()
    for i in range(len(access_x)):
        ax.plot(access_x[i], access_y[i], 'o-', color='gray', alpha=0.7)

    plt.grid()
    plt.yticks(list(codes.values()), list(codes.keys()))
    plt.title("Contact plan")
    plt.xlabel("Date and time")
    plt.ylabel("Nodes and targets")
    plt.show()
    print(rectangles)


def generate_contact_plan(satellites, targets, start, sim_time, dt, track_fname=None, plan_fname=None):
    times = list(range(start, start + sim_time, dt))
    ts = load.timescale()

    stations = {tgt["id"]: Topos(latitude_degrees=tgt["lat"], longitude_degrees=tgt["lon"], elevation_m=tgt["alt"]) for tgt in targets}
    # stations = {"stgo": Topos(latitude_degrees=-33.3833, longitude_degrees=-70.7833, elevation_m=476),
    #             "tokyo": Topos(latitude_degrees=35.6830, longitude_degrees=139.7670, elevation_m=5)}

    nodes = len(satellites)
    sats = {sat["id"]: EarthSatellite(sat["tle1"], sat["tle2"], sat["id"], ts) for sat in satellites}
    # sats = {tle['name']: EarthSatellite(tle['tle1'], tle['tle2'], tle['name'], ts) for index, tle in tles.iterrows()}

    dt = {t: ts.utc(datetime.fromtimestamp(t, utc)) for t in times}
    mi2 = pd.MultiIndex.from_product([sats.keys(), dt.keys()], names=['name', 'time'])

    # Satellite positions
    latlot = lambda topos: {"lat": topos.latitude.degrees, "lon": topos.longitude.degrees, "alt": topos.elevation.m}
    pos = [latlot(sats[s].at(dt[t]).subpoint()) for s, t in mi2]
    pos = pd.DataFrame(pos, index=mi2)

    # Satellite to targets contacts
    visible = lambda sat, t: {name: (sat - station).at(t).altaz()[0].degrees > 5 for name, station in stations.items()}
    elev = [visible(sats[s], dt[t]) for s, t in mi2]
    elev = pd.DataFrame(elev, index=mi2)

    # Satellite to satellite contacts
    interlink = lambda sat, t: {name: 0 < (sat - sat2).at(t).distance().km < 3000 for name, sat2 in sats.items()}
    dist = [interlink(sats[s], dt[t]) for s, t in mi2]
    dist = pd.DataFrame(dist, index=mi2)

    # Build tracks datafile
    tracks = pos.join(elev).join(dist)
    print(tracks)
    track_fname = time.strftime("%Y%m%d%H%M%S") + "_tracks.csv" if track_fname is None else track_fname
    tracks.to_csv(track_fname, index=False)

    # TODO: Optimize this code
    # Build contacts datafile
    names = list(stations.keys()) + list(sats.keys())
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
    plan_fname = track_fname.replace("_tracks", "_contacts") if plan_fname is None else plan_fname
    contacts.to_csv(plan_fname, index=False)

    return tracks, contacts


def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nodes", default=1, type=int, help="Nodes number")
    parser.add_argument("-s", "--start", default=int(time.time()), type=int, help="Starting time")
    parser.add_argument("--time", default=60, type=int, help="Simulation time")
    parser.add_argument("--dt", default=1, type=int, help="Simulation time step")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_parameters()
    tracks, contacts = generate_contact_plan(args.nodes, args.start, args.time, args.dt)
    map_plot(tracks)
    access_plot(contacts)
