from enum import Enum

class OpenflowProtocolsDescription(Enum): 
    OF10=0
    OF12=2
    OF13=3 
    OF14=4
    OF15=5

class SwitchPortStatisticsDescription():
    def __init__(self):
        self.RXPkts=0
        self.TXPkts=0
        self.RXBytes=0
        self.TXBytes=0

class SwitchDescription:
    def __init__(self):
        self.portIDs=[]                                     #list of port IDs (strings)
        self.portMACs=[]                                    #list of port MAC addresses (strings)
        self.portStats=[]                                   #list of port status (OFPPort state value)
        self.portStatistics=[]                              #list of statistics per port 
        self.portSpeeds=[]                                  #list of port speeds

        self.protocol=None                                  #switch's openflow protocol 
        self.datapathID=None                                #switch's datapath ID (string)
        self.switchCapabilities=None                        #switch's capabilities class (OFPSwitchFeatures)

class HostDescription:
   def __init__(self,hostMAC,hostIPv4,hostIPv6=None):
        self.MAC=hostMAC        #MAC address of the host (string)
        self.IPv4=hostIPv4      #IPv4 address of the host (string)
        self.IPv6=hostIPv6      #IPv6 address of the host (string)

class LinkDescription:
    DOWN=0
    UP=1
    ORPHANED=-1

class SSLinkDescription(LinkDescription):
    def __init__(self,switch1,switch2,switchMAC1,switchMAC2,linkStatus):
        self.switch1=switch1            #SwitchDescription 1 instance
        self.switch2=switch2            #switchDescription 2 instance
        self.switchMAC1=switchMAC1      #switchDescription 1 used port MAC address
        self.switchMAC2=switchMAC2      #switchDescription 2 used port MAC address
        self.linkStatus=linkStatus

class SHLinkDescription(LinkDescription):
    def __init__(self,switch,host,switchMACPort,linkStatus):
        self.switch=switch                  #SwitchDescription instance
        self.host=host                      #HostDescription instance
        self.switchMACPort=switchMACPort    #Switch's used port MAC address 
        self.linkStatus=linkStatus

class NetworkLayoutDescription:
    def __init__(self):     
        self.switches=[]                    #list of SwitchDescription instances
        self.hosts=[]                       #list of HostDescription instances
        self.links=[]                       #list of LinkDescription instances