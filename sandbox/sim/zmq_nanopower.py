import zmq
import struct
import argparse
from csp_zmq.zmqnode import CspZmqNode
from csp_zmq.zmqnode import threaded

"""
typedef struct __attribute__((packed)) {
    uint16_t vboost[3];3h                                //! Voltage of boost converters [mV] [PV1, PV2, PV3]
    uint16_t vbatt;h                                    //! Voltage of battery [mV]
    uint16_t curin[3];hhh                                //! Current in [mA]
    uint16_t cursun;h                                //! Current from boost converters [mA]
    uint16_t cursys;h                                //! Current out of battery [mA]
    uint16_t reserved;h
    uint16_t curout[6];hhhhhh                                //! Current out [mA]
    uint8_t output[8];BBBBBBBB                                //! Status of outputs [0 or 1]
    uint16_t output_on_delta[8];hhhhhhhh                    //! Time till power on [s]
    uint16_t output_off_delta[8];hhhhhhhh                    //! Time till power off [s]
    uint16_t latchup[6];hhhhhh                            //! Number of latch-ups []
    uint32_t wdt_i2c_time_left;I                        //! Time left on I2C wdt [s]
    uint32_t wdt_gnd_time_left;I                        //! Time left on I2C wdt [s]
    uint8_t  wdt_csp_pings_left[2];BB                    //! Pings left on CSP wdt []
    uint32_t counter_wdt_i2c;I                        //! Number of WDT I2C reboots []
    uint32_t counter_wdt_gnd;I                        //! Number of WDT GND reboots []
    uint32_t counter_wdt_csp[2];II                    //! Number of WDT CSP reboots []
    uint32_t counter_boot;I                             //! Number of EPS reboots []
    int16_t temp[6];hhhhhh                                //! Temperature sensors [0 = TEMP1, TEMP2, TEMP3, TEMP4, BATT0, BATT1]
    uint8_t    bootcause;B                                //! Cause of last EPS reset
    uint8_t battmode;B                                //! Mode for battery [0 = normal, 1 = undervoltage, 2 = overvoltage]
    uint8_t pptmode;B                                //! Mode of PPT tracker [1 = MPPT, 2 = fixed]
    uint16_t reserved2;h
} eps_hk_t;
"""


class ZmqNanopower(CspZmqNode):

    def __init__(self, node=2, hub_ip='localhost', in_port="8001", out_port="8002"):
        CspZmqNode.__init__(self, node, hub_ip, in_port, out_port, monitor=True, console=True)
        self.eps_hk_t = '3H1H3H1H1H1H6H8B8H8H6H1I1I2B1I1I2I1I6h1B1B1B' #1H'
        self.eps_config_t = '1B1B1b1b8B8B8H8H3h'

    def read_message(self, message, header=None):
        print("NANOPOWER:", message, header.dst_port if header else None)
        if header:
            if header.dst_port == 1:  # PING
                pass
            elif header.dst_port == 8:  # GET_HK
                message = struct.pack(self.eps_hk_t, *[0]*64)
                print("EPS_HK:", message, len(message))
            elif header.dst_port == 13:  # SET_HEATER
                message = message[-2:]
                print("EPS_HEAT:", message, len(message))
            elif header.dst_port == 18:  # GET_CONFIG
                message = struct.pack(self.eps_config_t, *[0]*39)
                print("EPS_CON:", message, len(message))
            elif header.dst_port == 20:  # HARD_RESET
                print("HARD RESET")

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
