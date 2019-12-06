import zmq
import struct
import argparse
from csp_zmq.zmqnode import CspZmqNode
from csp_zmq.zmqnode import threaded


class ZmqNanocom(CspZmqNode):
    def __init__(self, node_int=5, hub_ip_int='localhost', in_port_int="8001", out_port_int="8002",
                 node_ext=5, hub_ip_ext='localhost', in_port_ext="10001", out_port_ext="10002"):
        self._intern_node = CspZmqNode(node_int, hub_ip_int, in_port_int, out_port_int, True, True)
        self._extern_node = CspZmqNode(node_ext, hub_ip_ext, in_port_ext, out_port, ext, True, True)
        
    def start():
        CspZmqNode.start(self)
        self._extern_node.start()

    def read_message(self, message, header=None):
        print("NANOCOM", message, header.dst_port if header else None)
        if header:
            print("NANOCOM:", self.node, header.dst_node, header.dst_port)
            if header.dst_node == self.node:
                if header.dst_port == 1:    # PING
                    header.resend()
                    self.send_message(message.decode('ascii', 'replace'), header)
                elif header.dst_port == 7:  # GET/SET_CONFIG:
                    rparam_query = '<2B4HBI'
                    # print(struct.unpack(rparam_query, message))
                    print("CONFIG:", message, "F:", int(message[-4:].hex(), 16))
                    header.resend()
                    self.send_message('\0', header)
            else:
                print("NANOCOM-TX:", message)
                self._extern_node.send_message(message.decode('ascii', 'replace'), header)


def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--node", default=5, help="Node address")
    parser.add_argument("-d", "--ip", default="localhost", help="Hub IP address")
    parser.add_argument("-i", "--in_port", default="8001", help="Input port")
    parser.add_argument("-o", "--out_port", default="8002", help="Output port")

    return parser.parse_args()


if __name__ == "__main__":
    # Get arguments
    args = get_parameters()
    print(args)

    node = ZmqNanocom(int(args.node), args.ip, args.in_port, args.out_port)
    try:
        node.start()
        node.join()
    except KeyboardInterrupt:
        node.stop()
