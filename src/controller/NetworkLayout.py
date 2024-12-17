from enum import Enum 
from ryu.lib.packet import packet,ipv4,ipv6, arp, ethernet, ether_types

import networkx as nx

#Link represent a general link between two devices in the network
class Link:
    pass

#SSLink represents a link between two switches
class SSLink(Link):
    def __init__(self,switch1,switch2,switchMAC1,switchMAC2):
        self.switch1=switch1            #Switch 1 instance
        self.switch2=switch2            #switch 2 instance
        self.switchMAC1=switchMAC1      #switch 1 used port MAC address
        self.switchMAC2=switchMAC2      #switch 2 used port MAC address

    #getLinkedMACAddress return the MAC address of the device linked with the specified MAC address. 
    #In this case, given the MAC address of the switch port, the function return the mac address of the other connected switch port.
    #macAddress     ->      MAC address of one of the two switches
    #returns        ->      MAC address of the other switch, None if the MAC address is not specified in the link
    def getLinkedMACAddress(self,macAddress):
        if macAddress==self.switchMAC1:
            return self.switchMAC2
        elif macAddress==self.switchMAC2:
            return self.switchMAC1 
        else:
            return None 
    
    #getSwitchUsedPortID(self,switch) returns the port ID used by the switch instance in the link.
    #switch     ->      one of the two switch instance specified in the link 
    #returns    ->      ID of the used switch's port, None if the switch instance is not specified in the link 
    def getSwitchUsedPortID(self,switch):
        if switch==self.switch1:
            return self.switch1.getPortID(self.switchMAC1)
        elif switch==self.switch2:
            return self.switch2.getPortID(self.switchMAC2)
        else:
            return None
    
    #getSwitchUsedPortID(self,switch) returns the port MAC address used by the switch instance in the link.
    #switch     ->      one of the two switch instance specified in the link 
    #returns    ->      MAC address of the used switch's port, None if the switch instance is not specified in the link 
    def getSwitchUsedPortMAC(self,switch):
        if switch==self.switch1:
            return self.switchMAC1
        elif switch==self.switch2:
            return self.switchMAC2
        else:
            return None

    #isLinked(self,macAddress) verifies if thegiven MAC address is used in the link's instance
    #macAddress ->      MAC address to verify
    #returns    ->     True if the address is contained in the link, False otherwise
    def isLinked(self,macAddress):
        if macAddress==self.switchMAC1 or  macAddress==self.switchMAC2:
            return True
        else:
            return False
    
    #getWeight(self) generates a numer that specifies the weight to be used in the shortest path algorithm (now setted in a fixed value)
    # return    ->  weight of the link  
    def getWeight(self):
        return 1

    #isLink(self,switch1,switch2) verify if this istance connects two switches together
    # switch1, switch2      ->  instances of the two switches
    #returns -> True or False
    def isLink(self,switch1,switch2):
        if (self.switch1==switch1 and self.switch2==switch2) or (self.switch2==switch1 and self.switch1==switch2):
            return True 
        return False

    def __eq__(self,link):
        if isinstance(link,SSLink):
            if (self.switch1==link.switch1 and self.switch2==link.switch2 and self.switchMAC1==link.switchMAC1 and self.switchMAC2==link.switchMAC2) or (self.switch2==link.switch1 and self.switch1==link.switch2 and self.switchMAC2==link.switchMAC1 and self.switchMAC1==link.switchMAC2):
                return True
        return False

#SHLink represents a link between a Host and a Switch
class SHLink(Link):
    def __init__(self,switch,host,switchMACPort):
        self.switch=switch                  #Switch instance
        self.host=host                      #Host instance
        self.switchMACPort=switchMACPort    #Switch's used port MAC address 

    #getLinkedMACAddress return the MAC address of the device linked with the specified MAC address. 
    #In this case, given the MAC address of the switch's used port or the MAC address of the Host, the function return the mac address of the other connected device.
    #macAddress     ->      MAC address of one of the two switches
    #returns        ->      MAC address of the other device (switch or host), None if the MAC address is not specified in the link
    def getLinkedMACAddress(self,macAddress):
        if macAddress==self.switchMACPort:
            return self.host.MAC
        elif macAddress==self.host.MAC:
            return self.switchMACPort
        else:
            return None 

    #getSwitchUsedPortID(self,switch) returns the port ID used by the switch instance in the link.
    #switch     ->      one of the two switch instance specified in the link 
    #returns    ->      ID of the used switch's port, None if the switch instance is not specified in the link 
    def getSwitchUsedPortID(self,switch):
        if switch==self.switch:
            return self.switch.getPortID(self.switchMACPort)
        else:
            return None
    
    #getSwitchUsedPortID(self,switch) returns the port MAC address used by the switch instance in the link.
    #switch     ->      one of the two switch instance specified in the link 
    #returns    ->      MAC address of the used switch's port, None if the switch instance is not specified in the link 
    def getSwitchUsedPortMAC(self,switch):
        if switch==self.switch:
            return self.switchMACPort
        else:
            return None

    #isLinked(self,macAddress) verifies if thegiven MAC address is used in the link's instance
    #macAddress ->      MAC address to verify
    #returns    ->     True if the address is contained in the link, False otherwise
    def isLinked(self,macAddress):
        if macAddress==self.switchMACPort or macAddress==self.host.MAC:
            return True
        else:
            return False
        
    #isLink(self,switch1,switch2) verify if this istance connects two switches together
    # device1, device2      ->  instances of Host and Switch (in any order)
    #returns -> True or False
    def isLink(self,device1,device2):
        if isinstance(device1,Host):
            if (self.host==device1 and self.switch==device2):
                return True 
            else:
                return False
        else:
            if (self.host==device2 and self.switch==device1):
                return True 
            else:
                return False

    #getWeight(self) generates a numer that specifies the weight to be used in the shortest path algorithm (now setted in a fixed value)
    # return    ->  weight of the link  
    def getWeight(self):
        return 1

    def __eq__(self,link):
        if isinstance(link,SHLink):
            if self.switch==link.switch and self.host==link.host and self.switchMACPort==link.switchMACPort:
                return True
        return False

#Switch represents a switch in the network
class Switch():
    openflow_port=4294967294        #default port used by openflow 
    def __init__(self, switchMessage):

        self.portIDs=[]                                     #list of port IDs (strings)
        self.portMACs=[]                                    #list of port MAC addresses (strings)
        self.portStats=[]                                   #list of port status (OFPPort state value)
        self.portConfigs=[]                                 #list of port configurations (OFPPort config value)

        self.datapath=switchMessage.datapath                #switch's datapath instance 
        self.protocol=self.datapath.ofproto                 #switch's openflow protocol 
        self.parser=self.datapath.ofproto_parser            #switch's parser class 
        self.datapathID=switchMessage.datapath_id           #switch's datapath ID (string)
        self.switchCapabilities=switchMessage.capabilities  #switch's capabilities class (OFPSwitchFeatures)

    #updatePorts(self,portDescriptions) update port information and status
    #portDescription -> istance of the message's body from the ofp_event.EventOFPPortDescStatsReply handler (msg.body)
    def updatePorts(self,portDescriptions):
        self.portMACs.clear()
        self.portMACs.clear()
        self.portStats.clear()
        self.portConfigs.clear()
        for port in portDescriptions:
            if not (port.port_no==self.openflow_port):
                self.portIDs.append(port.port_no)
                self.portMACs.append(port.hw_addr)
                self.portStats.append(port.state)
                self.portConfigs.append(port.config) 

    #addFlowDirective(self,actions=None,match=None,priority=0,buffer_id=None,idleTimeout=0,hardTimeout=0) adds a directive to the flow table of the switch
    #actions -> list of openflow actions 
    #match -> istance of OFPMatch 
    #buffer_id -> buffer position (if specified)
    #idleTimeout, hardTimeout -> integer values if specified
    def addFlowDirective(self,actions=None,match=None,priority=0,buffer_id=None,idleTimeout=0,hardTimeout=0):
        if match==None:
            msgMatch=self.parser.OFPMatch()
        else:
            msgMatch=match
        if actions==None:
             instructions = []
        else:
            instructions = [self.parser.OFPInstructionActions(self.protocol.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id==None:
            switchMessage=self.parser.OFPFlowMod(datapath=self.datapath,priority=priority,match=msgMatch,instructions=instructions,idle_timeout=idleTimeout,hard_timeout=hardTimeout)
        else:
            switchMessage=self.parser.OFPFLowMod(datapath=self.datapath,buffer_id=buffer_id,priority=priority,match=match,instructions=instructions,idle_timeout=idleTimeout,hard_timeout=hardTimeout)
        self.datapath.send_msg(switchMessage)
    
    #sendPacket(self,data,inputPort,buffer_id=None,outputPort=None) sends a packet to the corresponding switch that tells to forward a packet to a specific port 
    #data -> packet data 
    #inputPort -> datapathID of the port that have received the packet
    #buffer_id - buffer id of the input packet 
    #output_port -> port to send the packet, if None the packet will be forwarded to all ports
    def sendPacket(self,data,inputPort,buffer_id=None,outputPort=None):
        packetData=None 
        if outputPort==None:
            actions = [self.parser.OFPActionOutput(self.protocol.OFPP_FLOOD)]
        else:
            actions = [self.parser.OFPActionOutput(outputPort)]

        if buffer_id==self.protocol.OFP_NO_BUFFER or buffer_id==None:
            packetData=data
            packetDirective = self.parser.OFPPacketOut(datapath=self.datapath, buffer_id=self.protocol.OFP_NO_BUFFER,in_port=inputPort, actions=actions, data=packetData)
        else:
            packetDirective = self.parser.OFPPacketOut(datapath=self.datapath, buffer_id=buffer_id, in_port=inputPort, actions=actions,data=None)
        self.datapath.send_msg(packetDirective)

    #def getPortMAC(self,portID) return the port MAC address from its ID
    #portID -> port identifier
    #returns -> MAC address of the port, None if the ID is incorrect
    
    def getPortMAC(self,portID):
        for indexNumber in range(len(self.portIDs)):
            if self.portIDs[indexNumber] == portID:
                return self.portMACs[indexNumber]
        return None
    
    #def getPortMAC(self,portID) return the port ID from its MAC address
    #portMAC -> port MAC address
    #returns -> ID of the port, None if the ID is incorrect
    def getPortID(self,portMAC):
        for indexNumber in range(len(self.portMACs)):
            if self.portMACs[indexNumber] == portMAC:
                return self.portIDs[indexNumber]
        return None

    #isSwitchPort(self,macAddress) verifies if the specified MAC address is the same as on of the switch ports
    #macAddress -> MAC address of the port
    #returns -> False or True
    def isSwitchPort(self,macAddress):
        if macAddress in self.portMACs:
            return True 
        return False
    

    def __eq__(self,switch):
        if isinstance(switch,Switch):
            if switch.datapathID==self.datapathID:
                return True
        return False


#Host class represent an Host in thenetwork configuration
class Host():
    def __init__(self,hostMAC,hostIP):
        self.MAC=hostMAC    #MAC address of the host (string)
        self.IP=hostIP      #IPv4 address of the host (string)

    def __eq__(self,host):
        if isinstance(host,Host):
            if (host.IP==self.IP) and (host.MAC == self.MAC):
                return True 
        return False

class NetworkLayout:
    MACdiscoveryAddress="ff:ff:ff:ff:ff:ff"     #discovery address in link protocol
    def __init__(self):     
        self.switches=[]                        #list of Switch instances
        self.hosts=[]                           #list of Host instances
        self.links=[]                           #list of Link instances

    #addSwitch(self,switch) adds a switch to the list
    #switch -> switch instance to add
    #returns -> True if the switch instance was not added before, False otherwise
    def addSwitch(self,switch):
        if switch not in self.switches:
            self.switches.append(switch)
            return True 
        return False
    
    #addHost(self,switch) adds a switch to the list
    #host-> host instance to add
    #returns -> True if the host instance was not added before, False otherwise
    def addHost(self,host):
        if host not in self.hosts:
            self.hosts.append(host)
            return True 
        return False 
    
    #addMACLink(self,link) adds a Link instance to the link list
    #link -> Link instance (SHLink or SSLink)
    #returns -> True if the link instance was not added before, False otherwise
    def addMACLink(self,link):
        if isinstance(link,SSLink) or isinstance(link,SHLink):
            if link not in self.links:
                self.links.append(link)
                return True 
        return False

    #def getSwitch(self,switchID) returns a switch from his datapathID 
    #switchID -> datapathID of the switch
    #returns -> switch instance, None for a non correspondence
    def getSwitch(self,switchID):
        for switch in self.switches:
            if switch.datapathID == switchID:
                return switch 
        return None
    
    #def getSwitch(self,switchID) returns a switch from his MAC address or IPv4 address
    #address -> datapathID of the switch
    #returns -> host instance, None for a non correspondence
    def getHost(self,address):
        for host in self.hosts:
            if host.IP==address or host.MAC==address:
                return host 
        return None
    
    #getDeviceByAddress(self,address) returns the corresponding network device from its MAC address (also IPv address for Hosts)
    #addess -> MAC address or IPv4 address of the device
    #returns -> Host instance (matching MAC or IP) or Switch (matching MAC address with one port) instance, None for a non correspondence 
    def getDeviceByAddress(self,address):
        for host in self.hosts:
            if host.MAC==address or host.IP==address:
                return host
        for switch in self.switches:
            if address in switch.portMACs:
                return switch 
        return None
    
    #getDeviceByID(self,address) returns the corresponding network device from its datapath ID (for Hosts the MAC address is considered as an ID)
    #addess -> Id of the device
    #returns -> Host instance (matching MAC with ID) or Switch instance, None for a non correspondence 
    def getDeviceByID(self,deviceID):
        for switch in self.switches:
            if switch.datapathID==deviceID:
                return switch 
        for host in self.hosts:
            if host.MAC==deviceID:
                return host 
        return None
            
    #getLinkFromMACAddress(self,macAddress) returns a Link instance from the MAC address of one of the two devices
    #macAddress -> MAC address of one device
    #returns -> Link instance (SSLink or SHLink), None for a non correspondence
    def getLinkFromMACAddress(self,macAddress):
        for link in self.links:
            if link.isLinked(macAddress):
                return link
        return None 
    
    #getLinkFromDevices(self,device1,device2) returns a link from two network devices IDs (MAc address for Hosts)
    #device1, device2 -> Host or switch Instances 
    #returns -> Link instance (SSLink or SHLink), None for a non correspondence
    def getLinkFromDevices(self,device1,device2):
        for link in self.links:
            if link.isLink(device1,device2):
                return link

    #forwardPacket(self,packetIn,switch,inputPort,outputPort=None,buffer_id=None) change the source MAC address with a specified port of the switch and forwards it
    #switch -> switch instance for forwarding
    #packetIn -> packet to forward
    #inputPort -> packet switch input port ID
    #buffer_id -> buffer_id of the packet to forward 
    #outputPort -> output switch port ID (None to forward the packet to all ports)

    def forwardPacket(self,packetIn,switch,inputPort,outputPort=None,buffer_id=None):
        ethHeader=packetIn.get_protocol(ethernet.ethernet)
        if outputPort==None:
            for port in switch.portIds:
                sourceMAC=switch.getPortMAC(port)
                link=self.getLinkFromMACAddress(sourceMAC)
                if link==None or (ethHeader.ethertype == ether_types.ETH_TYPE_ARP and packetIn.get_protocol(arp.arp).opcode==1):
                    destinationMAC=self.MACdiscoveryAddress
                else: 
                    destinationMAC=link.getLinkedMACAddress(sourceMAC)
                ethHeader.src=sourceMAC 
                ethHeader.dst=destinationMAC 
                packetIn.serialize()
                switch.sendPacket(data=packetIn.data,inputPort=inputPort,buffer_id=buffer_id,outputPort=port)
        else:
            sourceMAC=switch.getPortMAC(outputPort)
            link=self.getLinkFromMACAddress(sourceMAC)
            if link==None or (ethHeader.ethertype == ether_types.ETH_TYPE_ARP and packetIn.get_protocol(arp.arp).opcode==1):
                destinationMAC=self.MACdiscoveryAddress
            else: 
                destinationMAC=link.getLinkedMACAddress(sourceMAC)
            ethHeader.src=sourceMAC 
            ethHeader.dst=destinationMAC 
            packetIn.serialize()
            switch.sendPacket(data=packetIn.data,inputPort=inputPort,buffer_id=buffer_id,outputPort=outputPort)

    #getPath(self,switch,host) create a path using the dijkstra algorithm based on all network links from the switch to the host
    #switch -> istance of the source switch
    #host -> instance of the destination Host
    #returns -> list of switch datapathIDs terminated with the host MAC address, None of the path does not exists 
    def getPath(self,switch,host):
        graph=nx.Graph()
        destinationLink=self.getLinkFromMACAddress(host.MAC)
        graph.add_edge(host.MAC,destinationLink.switch.datapathID,weight=destinationLink.getWeight())       
        for link in self.links:
            if isinstance(link,SSLink):
                graph.add_edge(link.switch1.datapathID,link.switch2.datapathID,weight=link.getWeight())
        try:
            devicePath = nx.dijkstra_path(graph, source=switch.datapathID, target=host.MAC, weight='weight')
            return devicePath
        except nx.NetworkXNoPath:
            return None


