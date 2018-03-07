from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()
class Test (object):
	def __init__ (self, connection):
		self.connection = connection
		connection.addListeners(self)
		msg = of.ofp_flow_mod()
		msg.priority = 10
		msg.idle_timeout = 100
		msg.match.dl_type = 0x800
		msg.match.in_port=1
		msg.match.nw_proto = 6
		msg.match.tp_dst = 80
		msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
		self.connection.send(msg)

	def _handle_PacketIn (self, event):
		ports = {"10.0.0.1":1,"10.0.0.2":2,"10.0.0.3":3,"10.0.0.4":4,"10.0.0.5":5,"10.0.0.6":6,"10.0.0.7":7}
		print ' Welcome Packet In :) ' 
		packet = event.parsed 
		if not packet.parsed:
			log.warning("Ignoring incomplete packet")
			return


		ip = packet.find('ipv4')
		src_ip = ip.srcip
		dst_ip = ip.dstip
		print 'The src IP is ', src_ip , 'The dst IP is ', dst_ip

		tcp= packet.find('tcp')
		if tcp != None : 
			src_port = tcp.srcport
			dst_port = tcp.dstport

			print 'The src Port is ', src_port , 'The dst Port is ', dst_port

			found = 0 
			f = open('pox/misc/undesirable.txt','r')
			lst = list(f)
			for line in lst :
				if line == dst_ip:
					print 'The IP ', dst_ip , 'is in undesirable file, the packect will be droped' 
					found = 1
					msg = of.ofp_packet_out()
					msg.data = event.ofp
					#msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))
					self.connection.send(msg) # no action -> drop 
		
			if found == 0 :
				print 'The IP ', dst_ip , 'is NOT in undesirable file, the packect will forworded'
				msg = of.ofp_flow_mod()
				msg.priority = 100
				msg.idle_timeout = 100
				msg.match.dl_type = 0x800
				msg.match.in_port= 1
				msg.match.nw_proto = 6
				msg.match.nw_dst = dst_ip
				msg.match.tp_dst = 80
				msg.actions.append(of.ofp_action_output(port = ports[str(dst_ip)]))
				self.connection.send(msg)

				msg = of.ofp_flow_mod()
				msg.priority = 100
				msg.idle_timeout = 100
				msg.match.dl_type = 0x800
				msg.match.in_port= ports[str(dst_ip)]
				msg.match.nw_proto = 6
				msg.match.ip_dst = src_ip 
				msg.actions.append(of.ofp_action_output(port = 1))
				self.connection.send(msg)


def launch ():
	def start_switch (event):
		log.debug("Controlling %s" % (event.connection,))
		Test(event.connection)
        
	core.openflow.addListenerByName("ConnectionUp", start_switch)
