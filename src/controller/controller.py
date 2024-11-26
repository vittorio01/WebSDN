import connection.py

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.packet import packet


class Controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    switchesIDs=[]
    switchesCapabilities=[]
    
    switchesPortsIDs=[]
    switchesPortsHwaddrs=[]
    
    connections=[]

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_configuration_handler(self, ev):
        msg=ev.msg
        if msg.datapath_id not in self.switchesIDs:

            self.switchesIDs.append(msg.datapath_id)
            self.switchesCapabilities.append(msg.capabilities)

            port_addresses=[]
            port_names=[]
            for port in msg.ports:
                port_names.append(msg.ports[port].port_no)
                port_addresses.append(msg.ports[port].hw_addr)
            self.switchesPortsIDs.append(port_names)
            self.switchesPortsHwaddrs.append(port_addresses)

            print("Switch ",msg.datapath_id," configuration received: ")
            print("ID: ", msg.datapath_id)
            print("Capabilities: ",msg.capabilities)
            print("Ports: ",len(port_names),", ",port_addresses)
            print("----------------------------------------------------------")

    #@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    #def packet_in_handler(self, ev):
    #    msg = ev.msg
    #    dp = msg.datapath
    #    ofp = dp.ofproto
    #    ofp_parser = dp.ofproto_parser
    #    print(dp)

    #    actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]

    #    data = None
    #    if msg.buffer_id == ofp.OFP_NO_BUFFER:
    #         data = msg.data

    #    out = ofp_parser.OFPPacketOut(
    #        datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port,
    #        actions=actions, data = data)
    #    dp.send_msg(out)
        