#!/usr/bin/env python
import argparse
from subprocess import Popen

from csp_zmq.zmqhub import CspZmqHub
from zmq_nanocom import ZmqNanocom
from zmq_nanopower import ZmqNanopower

def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--ip", default="localhost", help="Hub IP address")
    parser.add_argument("-i", "--e_in_port", default="6001", help="Input port")
    parser.add_argument("-o", "--e_out_port", default="6002", help="Output port")
    parser.add_argument("-n", "--node", default=1, type=int, help="Node address")

    return parser.parse_args()


if __name__ == "__main__":
    # Get arguments
    args = get_parameters()
    print(args)
    
    in_port = str(8001)  # + args.node)
    out_port = str(8002)  # + args.node)
    mon_port = str(8003)  # + args.node)
    nobc, neps, ntrx, ntnc = [str(i+args.node) for i in range(4)]

    # hub = CspZmqHub(in_port=out_port, out_port=in_port, mon_port=mon_port, reader=False, writer=False)
    trx = ZmqNanocom(ntrx, args.ip, in_port, out_port,
                     ntnc, args.ip, args.e_in_port, args.e_out_port)
    eps = ZmqNanopower(neps, in_port=in_port, out_port=out_port)
    obc = Popen(["./SUCHAI_Flight_Software", "tcp://{}:{}".format(args.ip, in_port), "tcp://{}:{}".format(args.ip, out_port), nobc, neps, ntrx, ntnc])

    nodes = [trx, eps] #, hub]
    for n in nodes:
        print(n)
        n.start()
    try:
        for n in nodes:
            n.join()
    except KeyboardInterrupt:
        for n in nodes:
            n.stop()

