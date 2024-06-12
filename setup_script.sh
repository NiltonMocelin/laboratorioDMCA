#configurando a conexao entre eth0 e switch
sudo dhclient
sudo ovs-vsctl add-br switch
sudo ovs-vsctl set bridge switch protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13
sudo ovs-vsctl add-port switch eth0

IPETH=$(ip a | grep 'dynamic eth0' | awk '{print $2}')
DEFAULTG=$(ip route | grep 'via' | awk '{print $3}')

sudo ifconfig eth0 0.0.0.0
sudo ifconfig switch $IPETH
sudo ip route add default via $DEFAULTG dev switch

#limitando largura de banda

sudo ovs-vsctl set interface switch ingress_policing_rate=100000
sudo tc qdisc del dev eth0 root
sudo tc qdisc add dev eth0 root tbf rate 100000kbit latency 10ms burst 100000

