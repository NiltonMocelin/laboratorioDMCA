sudo ovs-vsctl add-br switch
sudo ovs-vsctl set bridge switch protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13
sudo ovs-vsctl add-port switch eth0

IPETH=$(ip a | grep 'dynamic eth0' | awk '{print $2}')
DEFAULTG=$(ip route | grep 'via' | awk '{print $3}')

sudo ifconfig eth0 0.0.0.0
sudo ifconfig switch $IPETH
sudo ip route add default via $DEFAULTG dev switch
