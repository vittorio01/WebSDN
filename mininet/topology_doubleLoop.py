
from mininet.topo import Topo

class Topology_Loop( Topo ):
    def build( self ):
        host1 = self.addHost('h1')
        host2 = self.addHost('h2')
        host3 = self.addHost('h3') 
        host4 = self.addHost('h4') 

        switch1 = self.addSwitch('s1',protocols='OpenFlow13')
        switch2 = self.addSwitch('s2',protocols='OpenFlow13')
        switch3 = self.addSwitch('s3',protocols='OpenFlow13')
        switch4 = self.addSwitch('s4',protocols='OpenFlow13')
        switch5 = self.addSwitch('s5',protocols='OpenFlow13')
        switch6 = self.addSwitch('s6',protocols='OpenFlow13')

        self.addLink(host1,switch1)
        self.addLink(host2,switch2)
        self.addLink(host3,switch3)
        self.addLink(host4,switch6)
        self.addLink(switch1,switch2)
        self.addLink(switch2,switch3)
        self.addLink(switch1,switch3)
        self.addLink(switch3,switch4)
        self.addLink(switch4,switch5)
        self.addLink(switch3,switch5)
        self.addLink(switch2,switch5)
        self.addLink(switch5,switch6)

topos = { 'topology_doubleLoop': ( lambda: Topology_Loop() ) }
