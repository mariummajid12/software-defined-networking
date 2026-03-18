from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, ether_types

class FlowGenerator(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(FlowGenerator, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.logger.info("FlowGenerator v3 initialized")
    
    def add_flow(self, datapath, priority, match, actions, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        flow_mod = parser.OFPFlowMod(
            datapath=datapath, 
            priority=priority,
            match=match, 
            instructions=inst,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout
        )
        datapath.send_msg(flow_mod)
        self.logger.info(f"Flow added to switch {datapath.id}: priority={priority}")
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        dpid = dp.id
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        
        self.logger.info(f"Switch {dpid} connected")
        self.mac_to_port.setdefault(dpid, {})
        
        # Table-miss flow entry: send to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions)
        
        """
        Topology:
        h1 (10.0.0.1) -- s2:port2
        h2 (10.0.0.2) -- s2:port3
        s2:port1 -- s1:port1
        s1:port2 -- s3:port1
        h3 (10.0.0.3) -- s3:port2
        h4 (10.0.0.4) -- s3:port3
        
        With --mac flag:
        h1 MAC: 00:00:00:00:00:01
        h2 MAC: 00:00:00:00:00:02
        h3 MAC: 00:00:00:00:00:03
        h4 MAC: 00:00:00:00:00:04
        """
        
        if dpid == 1:  # s1 - Core switch
            # Forward to s2 (port 1) based on destination MAC
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:01"),
                         [parser.OFPActionOutput(1)])
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:02"),
                         [parser.OFPActionOutput(1)])
            
            # Forward to s3 (port 2) based on destination MAC
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:03"),
                         [parser.OFPActionOutput(2)])
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:04"),
                         [parser.OFPActionOutput(2)])
            
            # Broadcast/Unknown: flood to both ports
            self.add_flow(dp, 50,
                         parser.OFPMatch(eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(2)])
        
        elif dpid == 2:  # s2 - Edge switch (h1, h2)
            # Forward to h1 (port 2)
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:01"),
                         [parser.OFPActionOutput(2)])
            
            # Forward to h2 (port 3)
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:02"),
                         [parser.OFPActionOutput(3)])
            
            # Forward to h3 or h4 (via s1, port 1)
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:03"),
                         [parser.OFPActionOutput(1)])
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:04"),
                         [parser.OFPActionOutput(1)])
            
            # Broadcast: flood to all ports except incoming
            self.add_flow(dp, 50,
                         parser.OFPMatch(in_port=1, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(2), parser.OFPActionOutput(3)])
            self.add_flow(dp, 50,
                         parser.OFPMatch(in_port=2, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(3)])
            self.add_flow(dp, 50,
                         parser.OFPMatch(in_port=3, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(2)])
        
        elif dpid == 3:  # s3 - Edge switch (h3, h4)
            # Forward to h3 (port 2)
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:03"),
                         [parser.OFPActionOutput(2)])
            
            # Forward to h4 (port 3)
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:04"),
                         [parser.OFPActionOutput(3)])
            
            # Forward to h1 or h2 (via s1, port 1)
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:01"),
                         [parser.OFPActionOutput(1)])
            self.add_flow(dp, 100,
                         parser.OFPMatch(eth_dst="00:00:00:00:00:02"),
                         [parser.OFPActionOutput(1)])
            
            # Broadcast: flood to all ports except incoming
            self.add_flow(dp, 50,
                         parser.OFPMatch(in_port=1, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(2), parser.OFPActionOutput(3)])
            self.add_flow(dp, 50,
                         parser.OFPMatch(in_port=2, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(3)])
            self.add_flow(dp, 50,
                         parser.OFPMatch(in_port=3, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(2)])
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        dpid = dp.id
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        dst = eth.dst
        src = eth.src
        
        self.logger.info(f"Packet-In: switch={dpid}, in_port={in_port}, src={src}, dst={dst}")
        
        # Default action: flood
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        
        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        out = parser.OFPPacketOut(
            datapath=dp,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )
        dp.send_msg(out)
