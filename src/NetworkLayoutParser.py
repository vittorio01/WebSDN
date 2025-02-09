from ryu.ofproto import ofproto_v1_0,ofproto_v1_2,ofproto_v1_3,ofproto_v1_4,ofproto_v1_5
from NetworkLayout import * 

from enum import Enum

class NetworkLayoutParser():
    @staticmethod
    def parseOFVersion(protocol):
        if (protocol==ofproto_v1_0):
            return "Openflow 1.0"
        elif (protocol==ofproto_v1_2):
            return "Openflow 1.2"
        elif (protocol==ofproto_v1_3):
            return "Openflow 1.3"
        elif (protocol==ofproto_v1_4):
            return "Openflow 1.4"
        elif (protocol==ofproto_v1_5):
            return "Openflow 1.5"
        else:
            "N/A"
    
    @staticmethod
    def parseSwitchPortStatus(switch):
        parsedStats=[]
        for port in switch.portStats:
            if port==switch.protocol.OFPPS_LINK_DOWN:
                parsedStats.append("Port down")
            else:
                parsedStats.append("Port active")
        return parsedStats
    @staticmethod
    def to_dict(NLClass):
        return {
            "switches": [
                {
                    "datapathID": sw.datapathID,
                    "protocol": NetworkLayoutParser.parseOFVersion(sw.protocol),
                    "portIDs": sw.portIDs,
                    "portMACs": sw.portMACs,
                    "portStats": NetworkLayoutParser.parseSwitchPortStatus(sw),
                    "portStatistics": [
                        {
                            "RXPkts": statistics.RXPkts,
                            "TXPkts": statistics.TXPkts,
                            "RXBytes": statistics.RXBytes,
                            "TXBytes": statistics.TXBytes,
                        } 
                        for statistics in sw.portStatistics
                    ],
                    "portSpeeds": sw.portSpeeds,
                }
                for sw in NLClass.switches
            ],
            "hosts": [
                {
                    "MAC": host.MAC,
                    "IPv4": host.IPv4,
                    "IPv6": host.IPv6 if host.IPv6 else "N/A",
                }
                for host in NLClass.hosts
            ],
            "links": [
                {
                    "type":"SS",
                    "switch1": link.switch1.datapathID,
                    "switch2": link.switch2.datapathID,
                    "switchMAC1": link.switchMAC1,
                    "switchMAC2": link.switchMAC2,
                    "linkStatus": link.linkStatus,
                }
                if isinstance(link, SSLink)
                else {
                    "type":"SH",
                    "switch": link.switch.datapathID,
                    "host": link.host.MAC,
                    "switchMACPort": link.switchMACPort,
                    "linkStatus": link.linkStatus,
                }
                for link in NLClass.links
            ],
        }