from NetworkLayout import Switch,Host,Link,SSLink,SHLink,NetworkLayout 

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ether
from ryu.lib.packet import packet,ipv4,ipv6,icmp, arp, ethernet, ether_types


class Controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

        #initializes the network layout instance
        self.network=NetworkLayout()                

    #function to send a request of information to a switch 
    # switch -> Switch instance
    def sendSwitchUpdatePortRequest(self,switch):

        #updates port informations for a specific switch
        switch.datapath.send_msg(switch.parser.OFPPortDescStatsRequest(switch.datapath))

    #handler for switch error messages
    @set_ev_cls(ofp_event.EventOFPErrorMsg,[HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        self.logger.debug('OFPErrorMsg received: type=0x%02x code=0x%02x message=%s',msg.type, msg.code, msg.data)

    #switch features handler
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_configuration_handler(self, ev):
        switch=Switch(ev.msg)
        if self.network.addSwitch(switch)==True:
            self.logger.info("Added Switch %s to network layout",switch.datapathID)
            self.sendSwitchUpdatePortRequest(switch)
            switch.addFlowDirective(actions=[switch.parser.OFPActionOutput(switch.protocol.OFPP_CONTROLLER,switch.protocol.OFPCML_NO_BUFFER)])
    
    #handler for port descriptions
    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        switch=self.network.getSwitch(ev.msg.datapath.id)
        switch.updatePorts(ev.msg.body)
        self.logger.info("received port status for switch %s ",switch.datapathID)

    #handler for packet in  
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg=ev.msg 

        #gets all switch information 
        switch=self.network.getSwitch(msg.datapath.id)
        switchPortInID=msg.match['in_port']
        switchPortInMAC=switch.getPortMAC(switchPortInID)
       
        packetIn=packet.Packet(msg.data)
        ethHeader=packetIn.get_protocol(ethernet.ethernet)
        sourceMAC=ethHeader.src
        destinationMAC=ethHeader.dst

        #try to find the source device from the registered network layout
        sourceDevice=self.network.getDeviceByAddress(sourceMAC) 
        if isinstance(sourceDevice,Switch):
            #if the source device is a controller, then adds a new switch to switch controller list
            ssLink=SSLink(switch,sourceDevice,switchPortInMAC,sourceMAC)
            if self.network.addMACLink(ssLink)==True:
                self.logger.info("-L> Added link from switch %s port %s to switch %s port %s",sourceDevice.datapathID,ssLink.getSwitchUsedPortID(sourceDevice),switch.datapathID,ssLink.getSwitchUsedPortID(switch))


        if ethHeader.ethertype == ether_types.ETH_TYPE_IPV6:
            ipv6Header=packetIn.get_protocol(ipv6.ipv6)
            sourceIP=ipv6Header.src 
            destinationIP=ipv6Header.dst

            #self.logger.info("received IPv6 packet in switch %s from %s (%s) to %s (%s)",switch.datapathID,sourceIP,sourceMAC, destinationIP,destinationMAC)
            icmpheader=packetIn.get_protocol(icmp.icmp)
            if icmpheader:
                self.logger.info("ICMP packet!")
            

        elif ethHeader.ethertype == ether_types.ETH_TYPE_ARP:
            #Specifications for ARP protocol: all network switches work like ARP proxies

            arpHeader=packetIn.get_protocol(arp.arp)
            sourceIP=arpHeader.src_ip 
            destinationIP=arpHeader.dst_ip
            arpOPCode=arpHeader.opcode

            sourceHost=self.network.getHost(sourceIP)
            if sourceHost == None:
                #if the source host is not registered in the network layout, then a new host and a link from switch to host is added to the network layout
                sourceHost=Host(sourceMAC,sourceIP)               
                self.network.addHost(sourceHost)
                self.network.addMACLink(SHLink(switch,sourceHost,switchPortInMAC))
                self.logger.info("-L> Added device %s to host list (linked to switch %s: %s -> port %s (%s) )",sourceIP,switch.datapathID,sourceMAC,switchPortInID,switchPortInMAC)

            if (arpOPCode==1):
                #ARP request 

                self.logger.info("-!> received ARP request packet in switch %s port %s from %s (%s) to %s",switch.datapathID,switchPortInID,sourceIP,sourceMAC, destinationIP)
                maskSwitch=False
                if isinstance(sourceDevice,Switch): maskSwitch=True

                
               
                for port in switch.portIDs:
                    if maskSwitch==True:
                        #if the source device is a registered switch, flow rules to mask all same ARP requests are added to all ports to avoid loops in the network
                        switch.addFlowDirective(priority=100,actions=None,match=switch.parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP,arp_op=1,in_port=port,arp_spa=sourceIP,arp_tpa=destinationIP),hardTimeout=1)
                    else:
                        #if the source device is a host, flow rules to mask all ports but the source port are added to all ports to avoid loops
                        if not (port==switchPortInID):
                            switch.addFlowDirective(priority=100,actions=None,match=switch.parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP,arp_op=1,in_port=port,arp_spa=sourceIP,arp_tpa=destinationIP),hardTimeout=1)
                        
                #The packet then is flooded 
                for port in switch.portIDs:
                    if not (port==switchPortInID):
                        self.network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=port,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                        self.logger.info("   -- Forward to port %s",port)

                
            else:
                #ARP response 

                self.logger.info("-!> received ARP reply packet in switch %s port %s from %s (%s) to %s (%s)",switch.datapathID,switchPortInID,sourceIP,sourceMAC, destinationIP,destinationMAC)
                destinationHost=self.network.getHost(destinationIP)

                #The source device is always already registered at least a path should exists because the host has received the ARP request
                self.logger.info("   -- Starting shortest path algorithm...")
                pathList=self.network.getPath(switch,destinationHost)
                if pathList==None:
                    self.logger.info("   -- No path found, flooding")
                else:

                    self.logger.info("   -- PathFound: %s",str(pathList))
                    deviceOut=self.network.getDeviceByID(pathList[1])
                    linkOut=self.network.getLinkFromDevices(switch,deviceOut)
                    switchOutPortID=linkOut.getSwitchUsedPortID(switch)
                    switchOutPortMAC=linkOut.getSwitchUsedPortMAC(switch)
                    self.logger.info("   -- Adding flow rule for device %s: ARP response packets from port %s forward to port %s (%s)",switch.datapathID,switchPortInID,switchOutPortID,switchOutPortMAC)
                    
                    #registering a flow rule for the current switch to avoid to launch again the algoithm
                    switch.addFlowDirective(priority=100,actions=[switch.parser.OFPActionSetField(eth_src=switchOutPortMAC),switch.parser.OFPActionOutput(switchOutPortID)],match=switch.parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP,arp_op=2,in_port=switchPortInID, arp_spa=sourceIP,arp_tpa=destinationIP),hardTimeout=100)

                    #the packet is then forwarded to the output port
                    self.network.forwardPacket(packetIn=packetIn,switch=switch,outputPort=switchOutPortID,inputPort=switchPortInID,buffer_id=msg.buffer_id)
                    self.logger.info("   -- Forward to port %s",switchOutPortID)
        else:

            #not recognized packets
            self.logger.info("-!> received not recognized packet (%s) in switch %s from %s to %s",ethHeader.ethertype,switch.datapathID,sourceMAC, destinationMAC)

                