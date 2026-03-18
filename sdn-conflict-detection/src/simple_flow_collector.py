"""
Simple Flow Collector with Conflict Generation
No REST API - uses command line arguments instead
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types
import csv
import random
import os
from datetime import datetime
import threading
import time

class SimpleFlowCollector(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(SimpleFlowCollector, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.flow_records = []
        self.flow_id = 0
        self.normal_count = 0
        self.conflict_count = 0
        
        self.logger.info("=" * 60)
        self.logger.info("Simple Flow Collector Initialized")
        self.logger.info("Commands will be available after switches connect")
        self.logger.info("=" * 60)
        
        # Start command interface in separate thread
        self.cmd_thread = threading.Thread(target=self.command_interface, daemon=True)
        self.cmd_thread.start()
    
    def command_interface(self):
        """Simple command line interface"""
        time.sleep(3)  # Wait for switches to connect
        
        print("\n" + "=" * 60)
        print("FLOW COLLECTOR COMMAND INTERFACE")
        print("=" * 60)
        print("Commands:")
        print("  stats              - Show current statistics")
        print("  normal <N>         - Generate N normal flows")
        print("  conflict <N>       - Generate N conflict flows")
        print("  generate <N>       - Generate N total flows (70% normal, 30% conflict)")
        print("  export             - Export flows to CSV")
        print("  reset              - Reset all records")
        print("  help               - Show this help")
        print("  quit               - Exit (Ctrl+C also works)")
        print("=" * 60 + "\n")
        
        while True:
            try:
                cmd = input("flow_collector> ").strip().lower()
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0]
                
                if command == 'stats':
                    self.show_stats()
                
                elif command == 'normal' and len(parts) > 1:
                    count = int(parts[1])
                    self.generate_normal_flows(count)
                
                elif command == 'conflict' and len(parts) > 1:
                    count = int(parts[1])
                    self.generate_conflict_flows(count)
                
                elif command == 'generate' and len(parts) > 1:
                    count = int(parts[1])
                    normal = int(count * 0.7)
                    conflicts = count - normal
                    print(f"Generating {normal} normal + {conflicts} conflict flows...")
                    self.generate_normal_flows(normal)
                    self.generate_conflict_flows(conflicts)
                    self.show_stats()
                
                elif command == 'export':
                    self.export_to_csv()
                
                elif command == 'reset':
                    self.reset_records()
                
                elif command == 'help':
                    print("Commands: stats, normal <N>, conflict <N>, generate <N>, export, reset, quit")
                
                elif command == 'quit':
                    print("Exiting...")
                    break
                
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' for available commands")
            
            except ValueError as e:
                print(f"Invalid number: {e}")
            except Exception as e:
                print(f"Error: {e}")
    
    def show_stats(self):
        """Display current statistics"""
        conflict_breakdown = {}
        for record in self.flow_records:
            ct = record['conflict_type']
            conflict_breakdown[ct] = conflict_breakdown.get(ct, 0) + 1
        
        print("\n--- FLOW STATISTICS ---")
        print(f"Total Flows: {len(self.flow_records)}")
        print(f"Normal Flows: {self.normal_count}")
        print(f"Conflict Flows: {self.conflict_count}")
        print(f"Switches Connected: {len(self.datapaths)}")
        print("\nConflict Breakdown:")
        for ctype, count in sorted(conflict_breakdown.items()):
            print(f"  {ctype}: {count}")
        print("-" * 25 + "\n")
    
    def reset_records(self):
        """Reset all flow records"""
        self.flow_records = []
        self.flow_id = 0
        self.normal_count = 0
        self.conflict_count = 0
        print("All records reset!")
    
    def add_flow(self, datapath, priority, match, actions, flow_type='normal', conflict_type=None):
        """Add flow to switch and record it"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        flow_mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                      match=match, instructions=inst)
        datapath.send_msg(flow_mod)
        
        # Record the flow
        self.record_flow(datapath.id, priority, match, actions, flow_type, conflict_type)
    
    def record_flow(self, dpid, priority, match, actions, flow_type, conflict_type):
        """Record flow for ML dataset"""
        self.flow_id += 1
        
        match_dict = dict(match._fields2) if hasattr(match, '_fields2') else {}
        
        record = {
            'flow_id': self.flow_id,
            'dpid': dpid,
            'priority': priority,
            'in_port': match_dict.get('in_port', 0),
            'eth_src': str(match_dict.get('eth_src', 'any')),
            'eth_dst': str(match_dict.get('eth_dst', 'any')),
            'eth_type': match_dict.get('eth_type', 0),
            'ipv4_src': str(match_dict.get('ipv4_src', 'any')),
            'ipv4_dst': str(match_dict.get('ipv4_dst', 'any')),
            'tcp_src': match_dict.get('tcp_src', 0),
            'tcp_dst': match_dict.get('tcp_dst', 0),
            'action': self._actions_to_str(actions),
            'flow_type': flow_type,
            'conflict_type': conflict_type if conflict_type else 'none'
        }
        
        self.flow_records.append(record)
        
        if flow_type == 'normal':
            self.normal_count += 1
        else:
            self.conflict_count += 1
    
    def _actions_to_str(self, actions):
        """Convert actions to string"""
        parts = []
        for a in actions:
            if hasattr(a, 'port'):
                parts.append(f"OUTPUT:{a.port}")
        return ','.join(parts) if parts else 'DROP'
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        dpid = dp.id
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        
        self.logger.info(f"Switch {dpid} connected")
        self.datapaths[dpid] = dp
        self.mac_to_port.setdefault(dpid, {})
        
        # Table-miss flow
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions, 'normal', None)
        
        # Install base connectivity rules
        self._install_base_rules(dp, dpid, parser)
    
    def _install_base_rules(self, dp, dpid, parser):
        """Install basic L2 forwarding rules"""
        if dpid == 1:  # Core switch
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:01"),
                         [parser.OFPActionOutput(1)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:02"),
                         [parser.OFPActionOutput(1)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:03"),
                         [parser.OFPActionOutput(2)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:04"),
                         [parser.OFPActionOutput(2)], 'normal')
            self.add_flow(dp, 50, parser.OFPMatch(eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(2)], 'normal')
        
        elif dpid == 2:  # Edge switch 1
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:01"),
                         [parser.OFPActionOutput(2)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:02"),
                         [parser.OFPActionOutput(3)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:03"),
                         [parser.OFPActionOutput(1)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:04"),
                         [parser.OFPActionOutput(1)], 'normal')
            self.add_flow(dp, 50, parser.OFPMatch(in_port=1, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(2), parser.OFPActionOutput(3)], 'normal')
            self.add_flow(dp, 50, parser.OFPMatch(in_port=2, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(3)], 'normal')
            self.add_flow(dp, 50, parser.OFPMatch(in_port=3, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(2)], 'normal')
        
        elif dpid == 3:  # Edge switch 2
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:03"),
                         [parser.OFPActionOutput(2)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:04"),
                         [parser.OFPActionOutput(3)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:01"),
                         [parser.OFPActionOutput(1)], 'normal')
            self.add_flow(dp, 100, parser.OFPMatch(eth_dst="00:00:00:00:00:02"),
                         [parser.OFPActionOutput(1)], 'normal')
            self.add_flow(dp, 50, parser.OFPMatch(in_port=1, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(2), parser.OFPActionOutput(3)], 'normal')
            self.add_flow(dp, 50, parser.OFPMatch(in_port=2, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(3)], 'normal')
            self.add_flow(dp, 50, parser.OFPMatch(in_port=3, eth_dst="ff:ff:ff:ff:ff:ff"),
                         [parser.OFPActionOutput(1), parser.OFPActionOutput(2)], 'normal')
    
    def generate_normal_flows(self, count):
        """Generate additional normal flows"""
        if not self.datapaths:
            print("ERROR: No switches connected!")
            return
        
        print(f"Generating {count} normal flows...")
        for i in range(count):
            dpid = random.choice(list(self.datapaths.keys()))
            dp = self.datapaths[dpid]
            parser = dp.ofproto_parser
            
            src_ip = f"10.0.{random.randint(0,255)}.{random.randint(1,254)}"
            dst_ip = f"10.0.{random.randint(0,255)}.{random.randint(1,254)}"
            priority = random.randint(100, 300)
            port = random.randint(1, 3)
            
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
            actions = [parser.OFPActionOutput(port)]
            self.add_flow(dp, priority, match, actions, 'normal', None)
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{count} normal flows")
        
        print(f"Done! Generated {count} normal flows")
    
    def generate_conflict_flows(self, count):
        """Generate conflict flows of various types"""
        if not self.datapaths:
            print("ERROR: No switches connected!")
            return
        
        conflict_types = ['redundancy', 'shadowing', 'overlapping', 
                         'correlation_a', 'correlation_b', 'generalization', 'imbrication']
        
        print(f"Generating {count} conflict flows...")
        for i in range(count):
            ctype = random.choice(conflict_types)
            dpid = random.choice(list(self.datapaths.keys()))
            dp = self.datapaths[dpid]
            parser = dp.ofproto_parser
            
            self._create_conflict(dp, parser, ctype)
            
            if (i + 1) % 50 == 0:
                print(f"  Generated {i + 1}/{count} conflict flows")
        
        print(f"Done! Generated {count} conflict flows")
    
    def _create_conflict(self, dp, parser, ctype):
        """Create specific conflict type"""
        src = f"10.0.{random.randint(0,255)}.{random.randint(1,254)}"
        dst = f"10.0.{random.randint(0,255)}.{random.randint(1,254)}"
        
        if ctype == 'redundancy':
            m = parser.OFPMatch(eth_type=0x0800, ipv4_src=src, ipv4_dst=dst)
            a = [parser.OFPActionOutput(1)]
            self.add_flow(dp, 200, m, a, 'conflict', 'redundancy')
            self.add_flow(dp, 200, m, a, 'conflict', 'redundancy')
        
        elif ctype == 'shadowing':
            m1 = parser.OFPMatch(eth_type=0x0800, ipv4_dst=dst)
            m2 = parser.OFPMatch(eth_type=0x0800, ipv4_src=src, ipv4_dst=dst)
            self.add_flow(dp, 300, m1, [parser.OFPActionOutput(1)], 'conflict', 'shadowing')
            self.add_flow(dp, 200, m2, [parser.OFPActionOutput(2)], 'conflict', 'shadowing')
        
        elif ctype == 'overlapping':
            m1 = parser.OFPMatch(eth_type=0x0800, ipv4_src=src)
            m2 = parser.OFPMatch(eth_type=0x0800, ipv4_dst=dst)
            self.add_flow(dp, 200, m1, [parser.OFPActionOutput(1)], 'conflict', 'overlapping')
            self.add_flow(dp, 200, m2, [parser.OFPActionOutput(2)], 'conflict', 'overlapping')
        
        elif ctype == 'correlation_a':
            m1 = parser.OFPMatch(eth_type=0x0800, ipv4_src=src, ipv4_dst=dst)
            m2 = parser.OFPMatch(eth_type=0x0800, ipv4_src=src)
            self.add_flow(dp, 200, m1, [parser.OFPActionOutput(1)], 'conflict', 'correlation_a')
            self.add_flow(dp, 200, m2, [parser.OFPActionOutput(1)], 'conflict', 'correlation_a')
        
        elif ctype == 'correlation_b':
            m1 = parser.OFPMatch(eth_type=0x0800, ipv4_dst=dst)
            m2 = parser.OFPMatch(eth_type=0x0800, ipv4_src=src, ipv4_dst=dst)
            self.add_flow(dp, 200, m1, [parser.OFPActionOutput(2)], 'conflict', 'correlation_b')
            self.add_flow(dp, 200, m2, [parser.OFPActionOutput(1)], 'conflict', 'correlation_b')
        
        elif ctype == 'generalization':
            m1 = parser.OFPMatch(eth_type=0x0800)
            m2 = parser.OFPMatch(eth_type=0x0800, ipv4_dst=dst)
            self.add_flow(dp, 150, m1, [parser.OFPActionOutput(1)], 'conflict', 'generalization')
            self.add_flow(dp, 250, m2, [parser.OFPActionOutput(2)], 'conflict', 'generalization')
        
        elif ctype == 'imbrication':
            m1 = parser.OFPMatch(eth_type=0x0800, ipv4_src=src)
            m2 = parser.OFPMatch(eth_type=0x0800, ipv4_dst=dst)
            m3 = parser.OFPMatch(eth_type=0x0800, ipv4_src=src, ipv4_dst=dst)
            self.add_flow(dp, 200, m1, [parser.OFPActionOutput(1)], 'conflict', 'imbrication')
            self.add_flow(dp, 200, m2, [parser.OFPActionOutput(2)], 'conflict', 'imbrication')
            self.add_flow(dp, 250, m3, [parser.OFPActionOutput(3)], 'conflict', 'imbrication')
    
    def export_to_csv(self):
        """Export all flow records to CSV"""
        if not self.flow_records:
            print("No flows to export!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flows_{len(self.flow_records)}_{timestamp}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.flow_records[0].keys())
            writer.writeheader()
            writer.writerows(self.flow_records)
        
        print(f"\nExported {len(self.flow_records)} flows to: {filepath}")
        print(f"  Normal: {self.normal_count}")
        print(f"  Conflict: {self.conflict_count}")
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser  # Fixed: define parser
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        
        out = parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        dp.send_msg(out)
