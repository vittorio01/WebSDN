#Custom configuration with three hosts h1,h2,h3 and three switches s1,s2,s3:
#                           h1 
#                           |
#                           s1
#                         /    \
#                 h2 ―― s2 ――― s3 ―― h3

from mininet.topo import Topo

class Topology_Linear( Topo ):
    def build( self ):
        host1 = self.addHost('h1')
        host2 = self.addHost('h2')

        switch1 = self.addSwitch('s1',protocols='OpenFlow13')
        switch2 = self.addSwitch('s2',protocols='OpenFlow13')

        self.addLink(host1,switch1)
        self.addLink(host2,switch2)
        self.addLink(switch1,switch2)

topos = { 'topology_linear': ( lambda: Topology_Linear() ) }
