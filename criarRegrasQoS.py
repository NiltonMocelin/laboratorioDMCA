from ryu.lib.packet import ethernet, ipv4, udp, tcp, in_proto, ether_types

#criando regra meter
def addRegraM(datapath, meter_id, banda):
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    
	#criando meter bands
    bands = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, len_=0, rate=banda, burst_size=10)]#e esse burst_size ajustar?
    req = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=ofproto.OFPMF_KBPS, meter_id=meter_id, bands=bands)
    datapath.send_msg(req)
    return

	#add regra tabela FORWARD
def addRegraF(datapath, ip_src, ip_dst, out_port, proto, meter_id):
    """ Parametros:
    ip_ver:str
    ip_src: str
    ip_dst: str
    ip_dscp: int
    out_port: int
    src_port: int
    dst_port: int 
    proto: str
    meter_id: int 
    """
        
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    
    match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ipv4_src=ip_src, ipv4_dst=ip_dst, ip_proto = proto)
         
    actions = [parser.OFPActionOutput(out_port)]
    
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    
    if meter_id != None:
        inst.append( parser.OFPInstructionMeter(meter_id=meter_id) )

    mod = parser.OFPFlowMod(datapath=datapath,match=match, priority=100, instructions=inst)
    datapath.send_msg(mod)

def injetar_pacote(porta_saida, porta_origem, datapath, msg, dados):
    print('porta saida:', porta_saida)
    actions = [datapath.ofproto_parser.OFPActionOutput(porta_saida)]
	
    out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                              in_port=porta_origem, actions=actions, data=dados)
    datapath.send_msg(out)