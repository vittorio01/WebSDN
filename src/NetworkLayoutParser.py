from ryu.ofproto import ofproto_v1_0,ofproto_v1_2,ofproto_v1_3,ofproto_v1_4
from NetworkLayout import * 

from enum import Enum
import json 

class OpenflowProtocolsDescription(Enum): 
    OF10="OpenFlow 1.0"
    OF12="OpenFlow 1.2"
    OF13="OpenFlow 1.3"
    OF14="OpenFlow 1.4"
    OF15="OpenFlow 1.5"

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
    DOWN="Down"
    UP="Up"
    ORPHANED="Orphaned"

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

class NetworkLayoutParser():
    @staticmethod
    def parseSwitchDescription(NLSwitch):
        switchDescription=SwitchDescription()
        switchDescription.datapathID=NLSwitch.datapathID
        switchDescription.switchCapabilities=NLSwitch.switchCapabilities
        if (NLSwitch.protocol.OFP_VERSION==ofproto_v1_0.OFP_VERSION):
            switchDescription.protocol=OpenflowProtocolsDescription.OF10 
        elif (NLSwitch.protocol.OFP_VERSION==ofproto_v1_2.OFP_VERSION):
            switchDescription.protocol=OpenflowProtocolsDescription.OF12
        elif (NLSwitch.protocol.OFP_VERSION==ofproto_v1_3.OFP_VERSION):
            switchDescription.protocol=OpenflowProtocolsDescription.OF13
        elif (NLSwitch.protocol.OFP_VERSION==ofproto_v1_4.OFP_VERSION):
            switchDescription.protocol=OpenflowProtocolsDescription.OF14
        else:
            switchDescription.protocol=OpenflowProtocolsDescription.OF15 

        for index in range(len(NLSwitch.portIDs)):
            switchDescription.portIDs.append(NLSwitch.portIDs[index])
            switchDescription.portMACs.append(NLSwitch.portMACs[index])
            switchDescription.portStats.append(NLSwitch.portStats[index])
            switchDescription.portSpeeds.append(NLSwitch.portSpeeds[index])
            switchDescriptionPortStatistics=SwitchPortStatisticsDescription()
            switchDescriptionPortStatistics.RXPkts=NLSwitch.PortStatistics.RXPkts
            switchDescriptionPortStatistics.TXPkts=NLSwitch.PortStatistics.TXPkts
            switchDescriptionPortStatistics.RXBytes=NLSwitch.PortStatistics.RXBytes
            switchDescriptionPortStatistics.TXBytes=NLSwitch.PortStatistics.TXBytes
            switchDescription.portStatistics.append(switchDescriptionPortStatistics)
        return switchDescription
    
    @staticmethod
    def parseHostDescription(NLHost):
        hostDescription=HostDescription()
        hostDescription.MAC=NLHost.MAC 
        hostDescription.IPv4=NLHost.IPv4 
        hostDescription.IPv6=NLHost.IPv6 
        return hostDescription
    
    @staticmethod 
    def compareHostWithDescription(hostDescription,NLHost):
        if hostDescription.MAC==NLHost.MAC and hostDescription.IPv4==NLHost.IPv4 and hostDescription.IPv6==NLHost.IPv6: return True 
        return False  

    @staticmethod 
    def compareSwitchWithDescription(switchDescription,NLSwitch):
        if switchDescription.datapathID==NLSwitch.datapathID: return True 
        return False 
    
    @staticmethod
    def to_dict(NLClass):
        networkLayoutDescription=NetworkLayoutDescription()
        for switch in NLClass.hosts:
            networkLayoutDescription.switches.append(NetworkLayoutParser.parseSwitchDescription(switch))
        for host in NLClass.hosts:
            networkLayoutDescription.switches.append(NetworkLayoutParser.parseHostDescription(host))
        for link in NLClass.links:
            if isinstance(SHLink,link):
                shlink=SHLinkDescription()
                for host in networkLayoutDescription.hosts:
                    if NetworkLayoutParser.compareHostWithDescription(host,link.host):
                        shlink.host=host
                for switch in networkLayoutDescription.switches:
                    if NetworkLayoutParser.compareHostWithDescription(switch,link.switch):
                        shlink.host=host
                shlink.switchMACPort=link.switchMACPort
                if (link.linkStatus==Link.DOWN):
                    shlink.linkStatus=LinkDescription.DOWN 
                elif (link.linkStatus==Link.UP):
                    shlink.linkStatus=LinkDescription.UP 
                else:
                    shlink.linkStatus=LinkDescription.ORPHANED  
            elif (isinstance(SSLink,link)):
                shlink=SHLinkDescription()
                for switch in networkLayoutDescription.switches:
                    if NetworkLayoutParser.compareHostWithDescription(switch,link.switch1):
                        shlink.switch1=switch 
                        shlink.switchMAC1=link.switchMAC1
                    elif NetworkLayoutParser.compareHostWithDescription(switch,link.switch2):
                        shlink.switch2=switch
                        shlink.switchMAC2=link.switchMAC2
                
                if (link.linkStatus==Link.DOWN):
                    shlink.linkStatus=LinkDescription.DOWN 
                elif (link.linkStatus==Link.UP):
                    shlink.linkStatus=LinkDescription.UP 
                else:
                    shlink.linkStatus=LinkDescription.ORPHANED  
        return {
            "switches": [
                {
                    "datapathID": sw.datapathID,
                    "protocol": sw.protocol,
                    "portIDs": sw.portIDs,
                    "portMACs": sw.portMACs,
                    "portStats": sw.portStats,
                    "portSpeeds": sw.portSpeeds,
                }
                for sw in networkLayoutDescription.switches
            ],
            "hosts": [
                {
                    "MAC": host.MAC,
                    "IPv4": host.IPv4,
                    "IPv6": host.IPv6 if host.IPv6 else "N/A",
                }
                for host in networkLayoutDescription.hosts
            ],
            "links": [
                {
                    "switch1": link.switch1.datapathID,
                    "switch2": link.switch2.datapathID,
                    "switchMAC1": link.switchMAC1,
                    "switchMAC2": link.switchMAC2,
                    "linkStatus": link.linkStatus,
                }
                if isinstance(link, SSLinkDescription)
                else {
                    "switch": link.switch.datapathID,
                    "host": link.host.MAC,
                    "switchMACPort": link.switchMACPort,
                    "linkStatus": link.linkStatus,
                }
                for link in networkLayoutDescription.links
            ],
        }