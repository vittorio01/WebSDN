from NetworkLayout import Switch,Host,Link,SSLink,SHLink,NetworkLayout 
from NetworkLayoutParser import *

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ether
from ryu.lib.packet import packet,ipv4,ipv6,tcp,udp,icmpv6, arp, ethernet, ether_types
from ryu.lib import hub

from flask import Flask
import json
from threading import Thread

app = Flask(__name__)

network=NetworkLayout() 

class Controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    IPv6_ICMPv6 = 58
    IPv4_ICMP = 1
    IPv6_TCP=6
    IPv6_UDP=17
    verbosity=1
    #verbosity level. Console info messages are filtered using a verbosity level that can be setted as an argument when launching the SDN controller. Higher values means more info messages.


    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        #initializes the network layout instance               
        self.switchMonitorThread = hub.spawn(self.switchStatisticsMonitor)
        self.server_thread = hub.spawn(self.run_flask)

    def run_flask(self):
        app.run(host="localhost", port=5000, debug=False, use_reloader=False)

    @app.route("/network_status", methods=["GET"])
    def get_network_status():
        return json.dumps(NetworkLayoutParser.to_dict(network),indent=4)
    
    def info(self, *args,type=0,verbosityLevel=0):
        if (verbosityLevel>self.verbosity): return
        if type==0:
            #message type for controller messages
            prefix="(C) "
        elif type==1:
            #message type for incoming packets
            prefix="(P)   "
        elif type==2:
            #message type for link level messages
            prefix="(L) "
        elif type==3:
            #message type for routing messages
            prefix="(R)      "
        elif type==4:
            #message type for packet forwarding messages
            prefix="(R)       --"
        else:
            prefix=""

        sep=""
        output = sep.join(map(str, args)) + "\n"
        output=prefix+output.strip()
        self.logger.info(output)


    #function to send a request of information to a switch 
    # switch -> Switch instance
    def sendSwitchUpdatePortRequest(self,switch):
        #updates port informations for a specific switch
        switch.datapath.send_msg(switch.parser.OFPPortDescStatsRequest(switch.datapath))

    def sendSwitchPortStatusRequest(self,switch):
        switch.datapath.send_msg(switch.parser.OFPPortStatsRequest(switch.datapath, 0, switch.protocol.OFPP_ANY))

    def switchStatisticsMonitor(self):
        hub.sleep(10)
        while True:
            for switch in network.switches:
                self.sendSwitchUpdatePortRequest(switch)
            hub.sleep(1)
            for switch in network.switches:
                self.sendSwitchPortStatusRequest(switch)
            hub.sleep(9)  # Intervallo tra le richieste (10 secondi)

    #handler for switch error messages
    @set_ev_cls(ofp_event.EventOFPErrorMsg,[HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        self.logger.debug('OFPErrorMsg received: type=0x%02x code=0x%02x message=%s',msg.type, msg.code, msg.data)

    #switch features handler
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_configuration_handler(self, ev):
        switch=Switch(ev.msg)
        if network.addSwitch(switch)==True:
            self.info("Added Switch ",switch.datapathID," to network layout",type=0,verbosityLevel=0)
            self.sendSwitchUpdatePortRequest(switch)
            switch.datapath.send_msg(switch.parser.OFPSetConfig(switch.datapath, switch.protocol.OFPC_FRAG_NORMAL, switch.protocol.OFPCML_NO_BUFFER))

            packet_in_mask = 1 << switch.protocol.OFPR_NO_MATCH
            port_status_mask = (1 << switch.protocol.OFPPR_ADD | 1 << switch.protocol.OFPPR_DELETE | 1 << switch.protocol.OFPPR_MODIFY)
            flow_removed_mask = (1 << switch.protocol.OFPRR_IDLE_TIMEOUT | 1 << switch.protocol.OFPRR_HARD_TIMEOUT | 1 << switch.protocol.OFPRR_DELETE)
            switch.datapath.send_msg(switch.parser.OFPSetAsync(switch.datapath,[packet_in_mask, 0],[port_status_mask, 0],[flow_removed_mask, 0]))

            switch.addFlowDirective(actions=[switch.parser.OFPActionOutput(switch.protocol.OFPP_CONTROLLER,switch.protocol.OFPCML_NO_BUFFER)])
    
    #handler for port descriptions
    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        network.updateSwitchDescriptions(ev.msg.datapath.id,ev.msg)
        self.info("Received port description for switch ",ev.msg.datapath.id,type=0,verbosityLevel=0)
        switch=network.getSwitch(ev.msg.datapath.id)
        for port in ev.msg.body:
            if (port.state==switch.protocol.OFPPS_LINK_DOWN):
                self.info("port:",port.port_no,", ",port.hw_addr, ", LINK DOWN, ",port.config,type=0,verbosityLevel=1)
            else:
                self.info("port:",port.port_no,", ",port.hw_addr, ", LINK UP, ",port.config,type=0,verbosityLevel=1)

    '''
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        self.info("Received switch status message",type=0,verbosityLevel=0)
        network.updateSwitchPort(ev.msg.datapath.id,ev.msg)
        port=ev.msg.desc
        
        if ev.msg.reason==ev.msg.datapath.ofproto.OFPPR_ADD:
            self.info("Added port to switch ",ev.msg.datapath.id,type=0,verbosityLevel=0)
            self.info("Port:",port.port_no,", ",port.hw_addr, ", ",port.state,", ",port.config,type=0,verbosityLevel=1)
        elif ev.msg.reason==ev.msg.datapath.ofproto.OFPPR_DELETE:
            self.info("Removed port in switch ",ev.msg.datapath.id,type=0,verbosityLevel=0)
        elif ev.msg.reason==ev.msg.datapath.ofproto.OFPPR_ADD:
            self.info("Modified port in switch ",ev.msg.datapath.id,type=0,verbosityLevel=0)
            self.info("Port:",port.port_no,", ",port.hw_addr, ", ",port.state,", ",port.config,type=0,verbosityLevel=1)
    '''

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        network.updateSwitchStatistics(ev.msg.datapath.id,ev.msg)
        self.info("Received port status for switch ",ev.msg.datapath.id,type=0,verbosityLevel=2)
        for port in ev.msg.body:
            self.info("port:",port.port_no,", RX pkts: ",port.rx_packets, ", TX pkts: ",port.tx_packets,", RX bytes: ",port.rx_bytes,", TX bytes: ",port.tx_bytes,type=0,verbosityLevel=3)

    #handler for packet in  
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg=ev.msg 

        #gets all switch information 
        switch=network.getSwitch(msg.datapath.id)
        switchPortInID=msg.match['in_port']
        switchPortInMAC=switch.getPortMAC(switchPortInID)
       
        packetIn=packet.Packet(msg.data)
        ethHeader=packetIn.get_protocol(ethernet.ethernet)
        sourceMAC=ethHeader.src
        destinationMAC=ethHeader.dst

        #try to find the source device from the registered network layout
        sourceDevice=network.getDeviceByAddress(sourceMAC) 
        if isinstance(sourceDevice,Switch):
            #if the source device is a controller, then adds a new switch to switch link in the network layout
            ssLink=SSLink(switch,sourceDevice,switchPortInMAC,sourceMAC)
            if network.addMACLink(ssLink)==True:
                self.info("Added link from switch ",sourceDevice.datapathID," port ",ssLink.getSwitchUsedPortID(sourceDevice)," to switch ",switch.datapathID," port ",ssLink.getSwitchUsedPortID(switch),type=2,verbosityLevel=0)


        if ethHeader.ethertype == ether_types.ETH_TYPE_IPV6:
            ipv6Header=packetIn.get_protocol(ipv6.ipv6)
            sourceIP=ipv6Header.src 
            destinationIP=ipv6Header.dst
            if (ipv6Header.nxt==self.IPv6_ICMPv6): 
                self.info("Received IPv6 (ICMPv6) packet in switch ",switch.datapathID," from ",sourceIP, " (",sourceMAC,") to ",destinationIP," (",destinationMAC,")",type=1,verbosityLevel=3)
                return
            self.info("Received IPv6 packet in switch ",switch.datapathID," from ",sourceIP, " (",sourceMAC,") to ",destinationIP," (",destinationMAC,")",type=1,verbosityLevel=0)
            sourceHost=network.getDeviceByAddress(sourceMAC)
            if sourceHost == None: 
                #if the host is not registered in the networ layout, then a new host is added to the network layout
                sourceHost=Host(sourceMAC,sourceIP)               
                network.addHost(sourceHost)
                network.addMACLink(SHLink(switch,sourceHost,switchPortInMAC))
                self.info("Added device ",sourceIP," to host list (linked to switch ",switch.datapathID,": ",sourceMAC," -> port ",switchPortInID," (",switchPortInMAC,")",type=2,verbosityLevel=0)
            destinationHost=network.getHost(destinationIP)
            if (destinationHost==None):
                #if the destination host is not in the network layout, the packet will be flooded
                maskSwitch=False
                self.info("Destination host not in network layout, flooding...",type=3,verbosityLevel=2)
                if isinstance(sourceDevice,Switch): maskSwitch=True
                for port in switch.portIDs:
                    if maskSwitch==True:
                        #if the source device is a registered switch, flow rules to mask all same ARP requests are added to all ports to avoid loops in the network
                        switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IPV6)
                    else:
                        #if the source device is a host, flow rules to mask all ports but the source port are added to all ports to avoid loops
                        if not (port==switchPortInID):
                            switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IPV6)
                for port in switch.portIDs:
                    if not (port==switchPortInID):
                        network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=port,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                        self.info("Forwaring packet to port ",port,type=4,verbosityLevel=0)
            else: 
                #if the destination host is already present in the network layout, a new path will be searched.
                self.info("Destination found in network layout: starting shortest path algorthm...",type=3,verbosityLevel=3)
                pathList=network.getPath(switch,destinationHost)
                if pathList==None:
                    #If the path cannot be enstablished, the packet will be flooded
                    self.info("Path not found: Flooding...",type=3,verbosityLevel=3)
                    maskSwitch=False
                    if isinstance(sourceDevice,Switch): maskSwitch=True
                    for port in switch.portIDs:
                        if maskSwitch==True:
                            #if the source device is a registered switch, flow rules to mask all same ARP requests are added to all ports to avoid loops in the network
                            switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IPV6)
                        else:
                            #if the source device is a host, flow rules to mask all ports but the source port are added to all ports to avoid loops
                            if not (port==switchPortInID):
                                switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IPV6)
                    for port in switch.portIDs:
                        if not (port==switchPortInID):
                            network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=port,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                            self.info("Forwaring packet to port ",port,type=4,verbosityLevel=0)               
                else:
                    self.info("Path found: ",str(pathList),type=3,verbosityLevel=3)
                    deviceOut=network.getDeviceByID(pathList[1])
                    linkOut=network.getLinkFromDevices(switch,deviceOut)
                    switchOutPortID=linkOut.getSwitchUsedPortID(switch)
                    switchOutPortMAC=linkOut.getSwitchUsedPortMAC(switch)
                    self.info("Adding flow rule for device ",switch.datapathID,": IPv6 from port ",switchPortInID," forward to port ",switchOutPortID," (",switchOutPortMAC,")",type=3,verbosityLevel=0)
                    
                    #registering a flow rule for the current switch to avoid to launch again the algoithm
                    switch.addFlowDirective(priority=100,actions=[switch.parser.OFPActionSetField(eth_src=switchOutPortMAC),switch.parser.OFPActionOutput(switchOutPortID)],hardTimeout=100,flowPortIn=switchPortInID,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IPV6)

                    #the packet is then forwarded to the output port
                    network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=switchOutPortID,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                    self.info("Forwaring packet to port ",switchOutPortID,type=4,verbosityLevel=0)

        if ethHeader.ethertype == ether_types.ETH_TYPE_IP:
            ipv4Header=packetIn.get_protocol(ipv4.ipv4)
            sourceIP=ipv4Header.src 
            destinationIP=ipv4Header.dst

            self.info("Received IPv4 packet in switch ",switch.datapathID," from ",sourceIP, " (",sourceMAC,") to ",destinationIP," (",destinationMAC,")",type=1,verbosityLevel=0)
            sourceHost=network.getDeviceByAddress(sourceIP)
            if sourceHost == None: 
                #if the host is not registered in the network layout, then a new host is added to the network layout
                sourceHost=Host(sourceMAC,sourceIP)               
                network.addHost(sourceHost)
                network.addMACLink(SHLink(switch,sourceHost,switchPortInMAC))
                self.info("Added device ",sourceIP," to host list (linked to switch ",switch.datapathID,": ",sourceMAC," -> port ",switchPortInID," (",switchPortInMAC,")",type=2,verbosityLevel=0)
            
            destinationHost=network.getHost(destinationIP)
            if destinationHost==None:
                #if the destination host is not registered in the network layout, the packet will be flooded
                self.info("Destination host not in network layout, flooding...",type=3,verbosityLevel=3)
                maskSwitch=False
                if isinstance(sourceDevice,Switch): maskSwitch=True
                for port in switch.portIDs:
                    if maskSwitch==True:
                        #if the source device is a registered switch, flow rules to mask all same ARP requests are added to all ports to avoid loops in the network
                        switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IP)
                    else:
                        #if the source device is a host, flow rules to mask all ports but the source port are added to all ports to avoid loops
                        if not (port==switchPortInID):
                            switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IP)
                for port in switch.portIDs:
                    if not (port==switchPortInID):
                        network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=port,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                        self.info("Forwaring packet to port ",port,type=4,verbosityLevel=0)
            else: 
                #if the destination host is already present in the network layout, a new path will be searched.
                self.info("Destination found in network layout: starting shortest path algorthm...",type=3,verbosityLevel=3)
                pathList=network.getPath(switch,destinationHost)
                if pathList==None:
                    #If the path cannot be enstablished, the packet will be flooded
                    self.info("Path not found: Flooding...",type=3,verbosityLevel=3)
                    maskSwitch=False
                    if isinstance(sourceDevice,Switch): maskSwitch=True
                    for port in switch.portIDs:
                        if maskSwitch==True:
                            #if the source device is a registered switch, flow rules to mask all same ARP requests are added to all ports to avoid loops in the network
                            switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IP)
                        else:
                            #if the source device is a host, flow rules to mask all ports but the source port are added to all ports to avoid loops
                            if not (port==switchPortInID):
                                switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IP)
                        for port in switch.portIDs:
                            if not (port==switchPortInID):
                                network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=port,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                                self.info("Forwaring packet to port ",port,type=4,verbosityLevel=0)
                else:
                    self.info("Path found: ",str(pathList),type=3,verbosityLevel=3)
                    deviceOut=network.getDeviceByID(pathList[1])
                    linkOut=network.getLinkFromDevices(switch,deviceOut)
                    switchOutPortID=linkOut.getSwitchUsedPortID(switch)
                    switchOutPortMAC=linkOut.getSwitchUsedPortMAC(switch)
                    self.info("Adding flow rule for device ",switch.datapathID,": IPv4 from port ",switchPortInID," forward to port ",switchOutPortID," (",switchOutPortMAC,")",type=3,verbosityLevel=0)
                    
                    #registering a flow rule for the current switch to avoid to launch again the algoithm
                    switch.addFlowDirective(priority=100,actions=[switch.parser.OFPActionSetField(eth_src=switchOutPortMAC),switch.parser.OFPActionOutput(switchOutPortID)],hardTimeout=100,flowPortIn=switchPortInID,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_IP)

                    #the packet is then forwarded to the output port
                    network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=switchOutPortID,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                    self.info("Forwaring packet to port ",switchOutPortID,type=4,verbosityLevel=0)




        elif ethHeader.ethertype == ether_types.ETH_TYPE_ARP:
            #Specifications for ARP protocol: all network switches work like ARP proxies

            arpHeader=packetIn.get_protocol(arp.arp)
            sourceIP=arpHeader.src_ip 
            destinationIP=arpHeader.dst_ip
            arpOPCode=arpHeader.opcode

            sourceHost=network.getDeviceByAddress(sourceMAC)
            if sourceHost == None:
                #if the source host is not registered in the network layout, then a new host and a link from switch to host is added to the network layout
                sourceHost=Host(sourceMAC,sourceIP)               
                network.addHost(sourceHost)
                network.addMACLink(SHLink(switch,sourceHost,switchPortInMAC))
                self.info("Added device ",sourceIP," to host list (linked to switch ",switch.datapathID,": ",sourceMAC," -> port ",switchPortInID," (",switchPortInMAC,")",type=2,verbosityLevel=0)


            if (arpOPCode==1):
                #ARP request 

                self.info("Received ARP request packet in switch ",switch.datapathID," from ",sourceIP, " (",sourceMAC,") to ",destinationIP," (",destinationMAC,")",type=1,verbosityLevel=0)
                maskSwitch=False
                if isinstance(sourceDevice,Switch): maskSwitch=True
                for port in switch.portIDs:
                    if maskSwitch==True:
                        #if the source device is a registered switch, flow rules to mask all same ARP requests are added to all ports to avoid loops in the network
                        switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_ARP,flowArpOp=1)
                    else:
                        #if the source device is a host, flow rules to mask all ports but the source port are added to all ports to avoid loops
                        if not (port==switchPortInID):
                            switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_ARP,flowArpOp=1)
                        
                #The packet then is flooded 
                for port in switch.portIDs:
                    if not (port==switchPortInID):
                        network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=port,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                        self.info("Forwaring packet to port ",port,type=4,verbosityLevel=0)

                
            else:
                #ARP response 

                self.info("Received ARP reply packet in switch ",switch.datapathID," from ",sourceIP, " (",sourceMAC,") to ",destinationIP," (",destinationMAC,")",type=1,verbosityLevel=0)
                destinationHost=network.getHost(destinationIP)

                self.info("Destination found in network layout: starting shortest path algorthm...",type=3,verbosityLevel=3)
                pathList=network.getPath(switch,destinationHost)
                if pathList==None:
                    self.info("Path not found: Flooding...",type=3,verbosityLevel=3)
                    maskSwitch=False
                    if isinstance(sourceDevice,Switch): maskSwitch=True
                    for port in switch.portIDs:
                        if maskSwitch==True:
                            #if the source device is a registered switch, flow rules to mask all same ARP requests are added to all ports to avoid loops in the network
                            switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_ARP,flowArpOp=2)
                        else:
                            #if the source device is a host, flow rules to mask all ports but the source port are added to all ports to avoid loops
                            if not (port==switchPortInID):
                                switch.addFlowDirective(priority=100,actions=None,hardTimeout=1,flowPortIn=port,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_ARP,flowArpOp=2)
                            
                    #The packet then is flooded 
                    for port in switch.portIDs:
                        if not (port==switchPortInID):
                            network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=port,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                            self.info("Forwaring packet to port ",port,type=4,verbosityLevel=0)

                else:

                    self.info("Path found: ",str(pathList),type=3,verbosityLevel=3)
                    deviceOut=network.getDeviceByID(pathList[1])
                    linkOut=network.getLinkFromDevices(switch,deviceOut)
                    switchOutPortID=linkOut.getSwitchUsedPortID(switch)
                    switchOutPortMAC=linkOut.getSwitchUsedPortMAC(switch)
                    self.info("Adding flow rule for device ",switch.datapathID,": ARP reply from port ",switchPortInID," forward to port ",switchOutPortID," (",switchOutPortMAC,")",type=3,verbosityLevel=0)
                    
                    #registering a flow rule for the current switch to avoid to launch again the algoithm
                    switch.addFlowDirective(priority=100,actions=[switch.parser.OFPActionSetField(eth_src=switchOutPortMAC),switch.parser.OFPActionOutput(switchOutPortID)],hardTimeout=100,flowPortIn=switchPortInID,flowSourceMAC=None,flowSourceIP=sourceIP,flowDestinationMAC=None,flowDestinationIP=destinationIP,flowEthType=ether_types.ETH_TYPE_ARP,flowArpOp=2)

                    #the packet is then forwarded to the output port
                    network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=switchOutPortID,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                    self.info("Forwaring packet to port ",switchOutPortID,type=4,verbosityLevel=0)
        else:

            #not managed packets
            self.info("Received not managed packet in switch ",switch.datapathID," from ",sourceIP, " (",sourceMAC,") to ",destinationIP," (",destinationMAC,"): ethertype=",ethHeader.ethertype,type=1,verbosityLevel=0)

                