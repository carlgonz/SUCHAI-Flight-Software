import zmq
import struct
import argparse
from csp_zmq.zmqnode import CspZmqNode
from csp_zmq.zmqnode import threaded


class ZmqNanocom(object):
    def __init__(self, node_int=5, hub_ip_int='localhost', in_port_int="8001", out_port_int="8002",
                 node_ext=5, hub_ip_ext='localhost', in_port_ext="10001", out_port_ext="10002",
                 internal_nodes=range(100)):
        
        self._intern_node = CspZmqNode(node_int, hub_ip_int, in_port_int, out_port_int, True, True)
        self._extern_node = CspZmqNode(node_ext, hub_ip_ext, in_port_ext, out_port_ext, True, True)
        
        self._intern_node.read_message = self._int_read_message
        self._extern_node.read_message = self._ext_read_message

        self._internal_nodes = internal_nodes
        
        
    def start(self):
        self._intern_node.start()
        self._extern_node.start()
        
    def join(self):
        self._intern_node.join()
        self._extern_node.join()
    
    def stop(self):
        self._intern_node.stop()
        self._extern_node.stop()

    def route_msg(self, header, msg, this_node):
        # SERVE
        print("ARRIVED TO {} | FROM {}:{} -> TO {}:{}".format(this_node, header.src_node, header.src_port, header.dst_node, header.dst_port))
        if header.dst_node == this_node:
            header, msg = self.serve(header, msg)

        # ROUTE
        if header and msg:
            if header.dst_node not in self._internal_nodes:
                print("ROUTING FROM {}:{} -> TO {}:{} | VIA EXT ({})".format(header.src_node, header.src_port, header.dst_node, header.dst_port, self._extern_node.node))
                self._extern_node.send_message(msg.decode('ascii', 'replace'), header)
            else:
                print("ROUTING FROM {}:{} -> TO {}:{} | VIA INT ({})".format(header.src_node, header.src_port, header.dst_node, header.dst_port, self._intern_node.node))
                self._intern_node.send_message(msg.decode('ascii', 'replace'), header)

    def _int_read_message(self, message, header=None):
        self.route_msg(header, message, self._intern_node.node)

    def _ext_read_message(self, message, header=None):
        self.route_msg(header, message, self._extern_node.node)
        return

        #print("NANOCOM-EXT", message, header.dst_port if header else None)
        # if header:
        #     print("NANOCOM {}. FROM {}:{} -> TO {}:{}".format(self._intern_node.node, header.src_node, header.src_port, header.dst_node, header.dst_port))
        #     if header.dst_node == self._extern_node.node:
        #         if header.dst_port == 1:    # PING
        #             header.resend()
        #             self._extern_node.send_message(message.decode('ascii', 'replace'), header)
        #         elif header.dst_port == 7:  # GET/SET_CONFIG
        #             rparam_query = '<2B4HBI'
        #             # print(struct.unpack(rparam_query, message))
        #             print("CONFIG:", message, "F:", int(message[-4:].hex(), 16))
        #             header.resend()
        #             self._extern_node.send_message('\0', header)
        #     else:
        #         print("NANOCOM-TX-EXT:", message)
        #         self._intern_node.send_message(message.decode('ascii', 'replace'), header)
                
    def serve(self, header, msg):
        # PING
        if header.dst_port == 1:
            print("PING RECEIVED!")
            header.resend()
        # GET/SET_CONFIG
        elif header.dst_port == 7:
            rparam_query = '<2B4HBI'
            # print(struct.unpack(rparam_query, message))
            print("CONFIG:", msg, "F:", int(msg[-4:].hex(), 16))
            header.resend()
            msg = '\0'
        # NOT SUPPORTED
        else:
            header = None
            msg = None

        return header, msg
            

def get_parameters():
    """ Parse command line parameters """
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--i_node", default=5, help="Int. Node address")
    parser.add_argument("-d", "--i_ip", default="localhost", help="Int. Hub IP address")
    parser.add_argument("-i", "--i_in_port", default="8001", help="Int. Input port")
    parser.add_argument("-o", "--i_out_port", default="8002", help="Int. Output port")
    
    parser.add_argument("-m", "--e_node", default=5, help="Ext. Node address")
    parser.add_argument("-e", "--e_ip", default="localhost", help="Ext. Hub IP address")
    parser.add_argument("-j", "--e_in_port", default="9001", help="Ext. Input port")
    parser.add_argument("-p", "--e_out_port", default="9002", help="Ext. Output port")

    return parser.parse_args()


if __name__ == "__main__":
    # Get arguments
    args = get_parameters()
    print(args)

    node = ZmqNanocom(int(args.i_node), args.i_ip, args.i_in_port, args.i_out_port, 
                      int(args.e_node), args.e_ip, args.e_in_port, args.e_out_port)
    try:
        node.start()
        node.join()
    except KeyboardInterrupt:
        node.stop()
