# simple_tree_topo.py
from mininet.topo import Topo

class SimpleTreeTopo(Topo):
    def build(self):
        # Root switch
        s1 = self.addSwitch('s1')
        
        # Child switches
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        
        # Connect switches
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        
        # Add hosts
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')
        
        # Connect hosts to switches
        self.addLink(h1, s2)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
        self.addLink(h4, s3)

topos = {'simpletree': SimpleTreeTopo}
