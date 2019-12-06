import zmq
import struct
import random
import argparse
import numpy as np
from csp_zmq.zmqnode import CspZmqNode
from csp_zmq.zmqnode import threaded


class ZmqPayload(CspZmqNode):

    def __init__(self, node=3, hub_ip='localhost', in_port="8001", out_port="8002"):
        CspZmqNode.__init__(self, node, hub_ip, in_port, out_port, monitor=True, console=True)

    def read_message(self, message, header=None):
        print("PAYLOAD:", message, header.dst_port if header else None)
        if header:
            if header.dst_port == 1:  # PING
                # Simple resend the same message, the default behaviour
                pass
            elif header.dst_port == 10:  # TAKE PICTURE
                message = bytes([random.randint(0, 254) for i in range(100)])
                print("IMG:", np.array(message).reshape(10, 10))

            header.resend()
            self.send_message(message.decode('ascii', 'replace'), header)



def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--node", default=2, help="Node address")
    parser.add_argument("-d", "--ip", default="localhost", help="Hub IP address")
    parser.add_argument("-i", "--in_port", default="8001", help="Input port")
    parser.add_argument("-o", "--out_port", default="8002", help="Output port")

    return parser.parse_args()


if __name__ == "__main__":
    # Get arguments
    args = get_parameters()
    print(args)

    node = ZmqNanopower(int(args.node), args.ip, args.in_port, args.out_port)

    try:
        node.start()
        node.join()
    except KeyboardInterrupt:
        node.stop()
