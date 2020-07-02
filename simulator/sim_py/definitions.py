"""
Constellation Control Framework
--------------------------------
Task and Scenario objects definition

:Date: 2002-06
:Version: 1
:Author: Carlos Gonzalez C. carlgonz@uchile.cl
"""

COL_START = "start"
COL_END = "end"
COL_FROM = "from"
COL_TO = "to"
COL_DT = "duration"


class Definition(object):
    def __init__(self, json_dict=None):
        if json_dict:
            self.from_json(json_dict)

    def from_vars(self, *args, **kwargs):
        pass

    def from_json(self, json_dict):
        self.__dict__.update(json_dict)

    def to_json(self):
        return self.__dict__


class Satellite(Definition):
    def __init__(self, json_dict=None):
        self.id = None
        self.node = None
        self.tle1 = None
        self.tle2 = None
        Definition.__init__(self, json_dict)

    def from_vars(self, _id, node, tle1, tle2):
        self.id = _id
        self.node = node
        self.tle1 = tle1
        self.tle2 = tle2


class Target(Definition):
    def __init__(self, json_dict=None):
        self.id = None
        self.node = None
        self.lat = None
        self.lon = None
        self.alt = None
        Definition.__init__(self, json_dict)

    def from_vars(self, _id, node, lat, lon, alt):
        self.id = _id
        self.node = node
        self.lat = lat
        self.lon = lon
        self.alt = alt


class GroundStation(Target):
    pass


class Scenario(Definition):
    def __init__(self, json_dict=None):
        self.id = None
        self.start = None
        self.duration = None
        self.step = None
        self.satellites = None
        self.stations = None
        self.targets = None
        self.tracks = None
        self.contacts = None
        Definition.__init__(self, json_dict)
        self.satellites = [Satellite(_json) for _json in json_dict["satellites"]]
        self.stations = [GroundStation(_json) for _json in json_dict["stations"]]
        self.targets = [Target(_json) for _json in json_dict["targets"]]
        self._ids = {d.id: d for d in self.satellites+self.stations+self.targets}

    def from_vars(self, _id, start, duration, step, satellites=(), stations=(), targets=(), tracks=None, contacts=None):
        self.id = _id
        self.start = start
        self.duration = duration
        self.step = step
        self.satellites = satellites
        self.stations = stations
        self.targets = targets
        self.tracks = tracks
        self.contacts = contacts

    def get(self, id):
        return self._ids.get(id, None)


class TaskTarget(Definition):
    def __init__(self, json_dict):
        self.id = None
        self.command = None
        self.result = None
        Definition.__init__(self, json_dict)

    def from_vars(self, target, command, result=None):
        self.id = target.id
        self.target = target
        self.command = command
        self.result = result


class Task(Definition):
    def __init__(self, json_dict):
        self.id = None
        self.start = None
        self.end = None
        self.targets = None
        self.solution = None
        Definition.__init__(self, json_dict)
        self.targets = [TaskTarget(_json) for _json in json_dict["targets"]]
        self._ids = {}

    def from_vars(self, _id, start_node, end_node, targets=(), solution=None):
        self.id = _id
        self.start = start_node
        self.end_node = end_node
        self.targets = targets
        self.solution = solution

    def ids(self):
        tgt_ids = [self.start]+[t.id for t in self.targets]+[self.end]
        return tgt_ids
