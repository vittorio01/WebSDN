
class Link:
    port1=""
    port2=""
    def __init__(self,port1,port2):
        self.port1=port1 
        self.port2=port2 

class Switch:
    switchID=0
    switchCapabilities=0

    portIDs=[]
    portMACs=[]
    portStats=[]
    portConfigs=[]

    def __init__(self, switchMessage):
        self.switchID=switchMessage.datapath_id
        self.switchCapabilities=switchMessage.capabilities
        for port in switchMessage.ports:
            self.portIDs.append(switchMessage.ports[port].port_no)
            self.portMACs.append(switchMessage.ports[port].hw_addr)
            self.portStats.append(switchMessage.ports[port].state)
            self.portConfigs.append(switchMessage.ports[port].config)
    
    def printInformation(self):
        print("     Switch ",self.switchID)
        print("--------------------")
        print("Capabilities: ",self.switchCapabilities)
        print("Ports: ",self.portIDs)
        print("MAC addresses: ",self.portMACs)
        print("--------------------")


class Host:
    hostID=""
    hostMAC=""
    def __init__(self,hostID,hostMAC):
        self.hostID=hostID 
        self.hostMAC=hostMAC 
    
    def printInformation(self):
        print("Host ",self.hostID,", ",self.hostMAC)


class NetworkLayout:
    switches=[]
    hosts=[]
    links=[]
    def addSwitch(self,switch):
        self.switches.append(switch)
    def addHost(self,host):
        self.hosts.append()
    def addMACLink(self,macAddress1,macAddress2):
        link=Link(macAddress1,macAddress2)
        self.links.append(link)

    def getSwitchLinks(self,switchID):
        selectedSwitch=None
        deviceList=[]
        for switch in self.switches:
            if switch.switchID==switchID:
                selectedSwitch=switch
                break 
        if (selectedSwitch==None):
            return None 
        for switchPort in selectedSwitch.portMacs:
            for link in self.links:
                if (switchPort == link.port1) or (switchPort == link.port2):
                    match=False 
                    for switch2 in self.switches:
                        if (link.port1 in switch2) or (link.port2 in switch2):
                            deviceList.append(switch2)
                            match=True
                            break 
                    if match==False:
                        for host in self.hosts:
                            if (link.port1 == host.hostMAC) or (link2.port2 == host.hostMAC):
                                deviceList.append(host)
                                break
        return deviceList

    


