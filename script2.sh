sudo ovs-vsctl add-br switch
sudo ovs-vsctl set bridge switch protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13
sudo ovs-vsctl add-port eth0