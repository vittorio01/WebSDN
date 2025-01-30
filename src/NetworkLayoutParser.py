from ryu.ofproto import ofproto_v1_0,ofproto_v1_2,ofproto_v1_3,ofproto_v1_4
from NetworkLayout import * 
from NetworkDescription import *

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
    def parseNetworkLayout(NLClass):
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
                    
        return networkLayoutDescription