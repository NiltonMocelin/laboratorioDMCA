# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.



#ofproto.OFPP_CONTROLLER - para gerar packet_in, ou ofproto.OFPP_LOCAL(switch),  OFPP_Normal-> para sair do pipeline do ovs, 1 = eth0

#pipeline
#VM -> pacote -> eth0(in_port=1) -> switch(in_port=LOCAL ou 4294967294) -> NORMAL -> fora da VM
#Fora VM -> pacote -> switch(in_port=LOCAL) -> eth0(in_port=1) -> VM

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, udp, tcp, in_proto
from ryu.lib.packet import ether_types


from criarRegrasQoS import addRegraM, addRegraF, injetar_pacote

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        print('in_port', in_port)

        #se inport == eth0 (1), mandar para local
        #se inport == local(4294967294), mandar para eth0
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src


        #se o fluxo for udp, limitar 1mb
        #se o fluxo for tcp, limitar 5mb ou nao limitar
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        ip_src = None
        ip_dst = None
        
        if pkt_ipv4:
            ip_src = pkt_ipv4.src
            ip_dst = pkt_ipv4.dst
            print('proto', pkt_ipv4.proto)

        pkt_tcp = pkt.get_protocol(tcp.tcp)

        pkt_udp = pkt.get_protocol(udp.udp)


        #pipeline
        #VM -> pacote -> eth0(in_port=1) -> switch(in_port=LOCAL ou 4294967294) -> NORMAL -> fora da VM
        #Fora VM -> pacote -> switch(in_port=LOCAL) -> eth0(in_port=1) -> VM

        #VM -> pacote -> eth0(in_port=1) -> switch(in_port=LOCAL ou 4294967294) -> NORMAL -> fora da VM
        if in_port == 1:
            out_port = ofproto.OFPP_NORMAL

            #addRegraF(datapath, ip_src, ip_dst, out_port, proto, meter_id)
            addRegraF(datapath, ip_src, ip_dst, out_port, pkt_ipv4.proto, 1, None)

            #limitar trafego udp
            addRegraM(datapath= datapath, meter_id = 20, banda = 2048) # 2Mbps
            #criar flow rule datapath, ip_src, ip_dst, out_port, src_port, dst_port, proto, meter_id
            addRegraF(datapath, ip_src, ip_dst, out_port, 17, 100, 20)

        if in_port == ofproto.OFPP_LOCAL:
            out_port = 1

            #addRegraF(datapath, ip_src, ip_dst, out_port, proto, meter_id) #tcp =6
            addRegraF(datapath, ip_src, ip_dst, out_port, pkt_ipv4.proto, 1, None)
            
            #limitar trafego udp
            addRegraM(datapath= datapath, meter_id = 10, banda = 2048) # 2Mbps
            #criar flow rule ip_src, ip_dst, out_port, proto, priority, meter_id
            addRegraF(datapath, ip_src, ip_dst, out_port, 17, 100, 10)        


        injetar_pacote(out_port, in_port, datapath, msg, msg.data)
    
        