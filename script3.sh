echo ' so deve rodar este script depois de ter realizado a configuracao de rede VM parte 3'

sudo tc qdisc add dev switch root tbf rate 20240kbit latency 10ms burst 15400

sudo vs-vsctl set interface switch ingress policing rate=20000