import struct
import numpy as np
import pandas as pd
from datetime import datetime
from pyorbital import astronomy
from pyorbital.orbital import Orbital

COM_FRAME_MAX_LEN = 200  # Packet size (bytes)

XKMPER = 6378.135
F = 1 / 298.257223563  # Earth flattening WGS-84
A = 6378.137  # WGS84 Equatorial radius


def get_lonlatalt(row):
    """Calculate sublon, sublat and altitude of satellite.
    http://celestrak.com/columns/v02n03/
    https://github.com/pytroll/pyorbital/blob/master/pyorbital/orbital.py
    """
    pos_x, pos_y, pos_z, utc_time = row[["dat_ads_pos_x", "dat_ads_pos_y", "dat_ads_pos_z", "dat_ads_tle_last"]]
    pos_x /= XKMPER; pos_y /= XKMPER; pos_z /= XKMPER
    utc_time = datetime.utcfromtimestamp(utc_time)
    lon = ((np.arctan2(pos_y * XKMPER, pos_x * XKMPER) - astronomy.gmst(utc_time))
           % (2 * np.pi))

    lon = np.where(lon > np.pi, lon - np.pi * 2, lon)
    lon = np.where(lon <= -np.pi, lon + np.pi * 2, lon)

    r = np.sqrt(pos_x ** 2 + pos_y ** 2)
    lat = np.arctan2(pos_z, r)
    e2 = F * (2 - F)
    while True:
        lat2 = lat
        c = 1 / (np.sqrt(1 - e2 * (np.sin(lat2) ** 2)))
        lat = np.arctan2(pos_z + c * e2 * np.sin(lat2), r)
        if np.all(abs(lat - lat2) < 1e-10):
            break
    alt = r / np.cos(lat) - c
    alt *= A

    # return np.rad2deg(lon), np.rad2deg(lat), alt

    row["dat_ads_lon"] = np.rad2deg(lon)
    row["dat_ads_lat"] = np.rad2deg(lat)
    row["dat_ads_alt"] = alt
    return row


def tle_prop(row, tles=None):
    node = int(row["node"])
    tle = tles.iloc[node-1]
    dt = datetime.utcfromtimestamp(row["dat_ads_tle_last"])
    sat = Orbital(tle["name"], line1=tle["tle1"], line2=tle["tle2"])
    try:
        lon, lat, alt = sat.get_lonlatalt(dt)
        pos, vel = sat.get_position(dt, normalize=False)
    except Exception:
        lon, lat, alt = [0, 0, 0]
        pos = [0, 0, 0]

    row["ref_lon"] = lon
    row["ref_lat"] = lat
    row["ref_alt"] = alt
    row["ref_pos_x"] = pos[0]
    row["ref_pos_y"] = pos[1]
    row["ref_pos_z"] = pos[2]
    return row


def add_lonlatalt(tm, tles):
    tm = tm.apply(get_lonlatalt, axis=1)
    # tm = tm.apply(tle_prop, axis=1, tles=tles)
    return tm


class Telemetry(object):
    def __init__(self):
        self.hdr = '2H1I'
        self.frame_len = COM_FRAME_MAX_LEN
        self.fmt = ""
        self.names = tuple()
        self.values = tuple()
        self.node = -1

    def __len__(self):
        return len(self.names)

    def parse(self, buffer, node=None):
        padding = self.frame_len - struct.calcsize(self.hdr+self.fmt)
        header = struct.calcsize(self.hdr)
        self.node = node if node is not None else -1
        self.values = struct.unpack(self.fmt, buffer[header:-padding])

    def list(self):
        return [self.node] + list(self.values)

    def dataframe(self):
        return pd.DataFrame(self.list(), self.names)


class StatusTelemetry(Telemetry):
    def __init__(self):
        Telemetry.__init__(self)
        self.fmt = '7i3f14i3f20i'
        self.names = (
            "node",
            "dat_obc_opmode",           # General operation mode
            "dat_obc_last_reset",           # Last reset source
            "dat_obc_hrs_alive",            # Hours since first boot
            "dat_obc_hrs_wo_reset",         # Hours since last reset
            "dat_obc_reset_counter",        # Number of reset since first boot
            "dat_obc_sw_wdt",               # Software watchdog timer counter
            "dat_obc_cmd_queue",            # Command queue size
            "dat_obc_temp_1",               # Temperature value of the first sensor
            "dat_obc_temp_2",               # Temperature value of the second sensor
            "dat_obc_temp_3",               # Temperature value of the gyroscope
    
            # DEP: Deployment related variables.
            "dat_dep_deployed",             # Was the satellite deployed?
            "dat_dep_ant_deployed",         # Was the antenna deployed?
            "dat_dep_date_time",            # Antenna deployment unix time
    
            # RTC: Rtc related variables
            "dat_rtc_date_time",            # RTC current unix time
    
            # COM: Communications system variables.
            "dat_com_count_tm",             # Number of Telemetries sent
            "dat_com_count_tc",             # Number of received Telecommands
            "dat_com_last_tc",              # Unix time of the last received Telecommand
            "dat_com_freq",                 # Communications frequency [Hz]
            "dat_com_tx_pwr",               # TX power (0: 25dBm, 1: 27dBm, 2: 28dBm 3: 30dBm)
            "dat_com_baud",                 # Baudrate [bps]
            "dat_com_mode",                 # Framing mode (1: RAW, 2: ASM, 3: HDLC, 4: Viterbi, 5: GOLAY 6: AX25)
            "dat_com_bcn_period",           # Number of seconds between beacon packets
    
            # FPL: Flight plan related variables
            "dat_fpl_last",                 # Last executed flight plan (unix time)
            "dat_fpl_queue",                # Flight plan queue length
    
            # ADS: Altitude determination system
            #    "dat_ads_acc_x",                # Gyroscope acceleration value along the x axis
            #    "dat_ads_acc_y",                # Gyroscope acceleration value along the y axis
            #    "dat_ads_acc_z",                # Gyroscope acceleration value along the z axis
            #    "dat_tgt_acc_x",                # Target acceleration value along the x axis
            #    "dat_tgt_acc_y",                # Target acceleration value along the y axis
            #    "dat_tgt_acc_z",                # Target acceleration value along the z axis
            #    "dat_ads_mag_x",                # Magnetometer value along the x axis
            #    "dat_ads_mag_y",                # Magnetometer value along the y axis
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    #    "dat_ads_mag_z",                # Magnetometer value along the z axis
            "dat_ads_pos_x",                # Satellite orbit position x (ECI)
            "dat_ads_pos_y",                # Satellite orbit position y (ECI)
            "dat_ads_pos_z",                # Satellite orbit position z (ECI)
            "dat_ads_tle_epoch",            # Current TLE epoch 0 if TLE is invalid
            "dat_ads_tle_last",             # Las time position was propagated
            #    "dat_ads_q0",                  # Attitude quaternion (Inertial to body)
            #    "dat_ads_q1",                  # Attitude quaternion (Inertial to body)
            #    "dat_ads_q2",                  # Attitude quaternion (Inertial to body)
            #    "dat_ads_q3",                  # Attitude quaternion (Inertial to body)
            #    "dat_tgt_q0",                  # Target quaternion (Inertial to body)
            #    "dat_tgt_q1",                  # Target quaternion (Inertial to body)
            #    "dat_tgt_q2",                  # Target quaternion (Inertial to body)
            #    "dat_tgt_q3",                  # Target quaternion (Inertial to body)
    
            # EPS: Energy power system
            "dat_eps_vbatt",                # Voltage of the battery [mV]
            "dat_eps_cur_sun",              # Current from boost converters [mA]
            "dat_eps_cur_sys",              # Current from the battery [mA]
            "dat_eps_temp_bat0",            # Battery temperature sensor
    
            # Memory: Current payload memory addresses
            "dat_drp_temp",                 # Temperature data index
            "dat_drp_ads",                  # ADS data index
            "dat_drp_eps",                  # EPS data index
            "dat_drp_lang",                 # Langmuir data index
    
            # Memory: Current send acknowledge data
            "dat_drp_ack_temp",                 # Temperature data acknowledge
            "dat_drp_ack_ads",                  # ADS data index acknowledge
            "dat_drp_ack_eps",                  # EPS data index acknowledge
            "dat_drp_ack_lang",                 # Langmuir data index acknowledge
    
            # Sample Machine: Current state of sample machine
            "dat_drp_mach_action",
            "dat_drp_mach_state",
            "dat_drp_mach_step",
            "dat_drp_mach_payloads",
            "dat_drp_mach_left",
    
            # Add custom status variables here
            # "dat_custom",                 # Variable description
    
            # LAST ELEMENT: DO NOT EDIT
            "dat_system_last_var",           # Dummy element the amount of status variables
        )
