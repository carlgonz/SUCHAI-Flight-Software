#!/usr/bin/env python3
import sys
import time
import signal
import argparse
import pandas as pd
from subprocess import Popen, PIPE, DEVNULL

sys.path.append("../../sandbox")
from csp_zmq.zmqnode import CspZmqNode, CspHeader, threaded
from telemetry import StatusTelemetry, add_lonlatalt

SCH_TRX_PORT_TM = 9   # Telemetry port
SCH_TRX_PORT_TC = 10  # Telecommands port
SCH_TRX_PORT_RPT = 11  # Digirepeater port (resend packets)
SCH_TRX_PORT_CMD = 12  # Commands port (execute console commands)
SCH_TRX_PORT_DBG = 13  # Debug port, logs output
COM_FRAME_MAX_LEN = 200  # Packet size (bytes)


class Simulator(CspZmqNode):
    def __init__(self):
        self.nodes = []
        self.obcs = []
        self.ttys = []
        self.hub = None
        self.tm_status = []

        CspZmqNode.__init__(self, "0", writer=True)

    def join(self):
        self.hub.wait()
        CspZmqNode.join(self)

    def stop(self):
        for obc in self.obcs:
            obc.wait()
        for tty in self.ttys:
            tty.close()
        self.hub.kill()

        CspZmqNode.stop(self)

    def start(self, nodes, ttys):
        self.ttys = ttys
        self.nodes = nodes

        self.hub = Popen(["python", "../../sandbox/csp_zmq/zmqhub.py"], stdin=DEVNULL, stdout=DEVNULL)
        for node, tty in zip(self.nodes, self.ttys):
            pass
            obc = Popen(["./SUCHAI_Flight_Software", str(node)], stdin=DEVNULL, stdout=tty,
                        preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))
            self.obcs.append(obc)

        CspZmqNode.start(self)

    def send_command(self, command, nodes=None):
        if nodes is None:
            nodes = self.nodes

        for dnode in nodes:
            hdr = CspHeader(src_node=self.node, dst_node=dnode, dst_port=10)
            self.send_message(command, hdr)

    def read_message(self, message, header=None):
        if header.dst_port is SCH_TRX_PORT_TM:
            self.parse_tm_status(header.src_node, message)
        else:
            print(header.src_node, header.dst_port, message)

    def parse_tm_status(self, node, message):
        tm = StatusTelemetry()
        tm.parse(message, node)
        self.tm_status.append(tm.list())


def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--ip", default="localhost", help="Hub IP address")
    parser.add_argument("-i", "--inport", default="8001", help="Input port")
    parser.add_argument("-o", "--outport", default="8002", help="Output port")
    parser.add_argument("-n", "--nodes", default=1, type=int, help="Node number")
    parser.add_argument("-t", "--tty", default=0, type=int, help="First tty to connect")
    parser.add_argument("--time", default=60, type=int, help="Simulation time")

    return parser.parse_args()


if __name__ == "__main__":
    # Get arguments
    args = get_parameters()
    print(args)

    in_port = args.inport
    out_port = args.outport
    # mon_port = str(8003)  # + args.node)
    nodes = list(range(1, args.nodes+1))
    ttys = [open("/dev/pts/{}".format(i), "wb+", buffering=0) for i in range(args.tty, args.tty+args.nodes)]

    simulator = Simulator()
    simulator.start(nodes, ttys)
    time.sleep(1)

    # Reset Repo data
    simulator.send_command("drp_ebf 1010")

    # Set up TLE
    tles = pd.read_csv("starlink.csv")
    tles = tles.sample(n=args.nodes, random_state=5)
    print(tles)
    for n in nodes:
        tle = tles.iloc[n-1]
        tle1, tle2 = tle[["tle1", "tle2"]]
        # simulator.send_command("obc_set_tle "+tle1 +";"+"obc_set_tle "+tle2+";"+"obc_update_tle", [n])
        simulator.send_command("obc_set_tle "+tle1, [n])
        simulator.send_command("obc_set_tle "+tle2, [n])
        simulator.send_command("obc_update_tle", [n])

    # Set up date
    # now = int(time.time())
    now = 1587160800
    simulator.send_command("obc_set_time "+str(now))

    # Start simulation
    simulator.send_command("sim_start {}".format(int(time.time())+3))
    # simulator.send_command("sim_start")
    try:
        time.sleep(args.time)
    except KeyboardInterrupt:
        pass
    finally:
        simulator.send_command("sim_stop")
        simulator.stop()
        tm = pd.DataFrame(simulator.tm_status, columns=StatusTelemetry().names)
        tm = add_lonlatalt(tm, tles)
        tm_file = "tm_status_{}.csv".format(time.strftime("%Y%m%d-%H%M%S", time.localtime()))
        tm.to_csv(tm_file, index=False)
        print("Saved to", tm_file)
