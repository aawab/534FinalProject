#!/bin/bash
# INTRA PROTOCOL RTT FAIRNESS TESTING

# Var for cc algo
ALGORITHM=$1

# Define sender IPs
sender1IP="192.168.139.128"
sender2IP="192.168.139.129"
sender3IP="192.168.139.130"

senderArr=($sender1IP $sender2IP $sender3IP)

receiver1IP="192.168.192.128"
receiver2IP="192.168.192.129"
receiver3IP="192.168.192.130"

receiverArr=($receiver1IP $receiver2IP $receiver3IP)

# Clear existing tc rules
sudo tc qdisc del dev ens33 root 2>/dev/null

# Create root qdisc
sudo tc qdisc add dev ens33 root handle 1: prio bands 4

# Add delay qdiscs for each band
sudo tc qdisc add dev ens33 parent 1:1 handle 10: netem delay 10ms
sudo tc qdisc add dev ens33 parent 1:2 handle 20: netem delay 20ms 
sudo tc qdisc add dev ens33 parent 1:3 handle 30: netem delay 40ms
sudo tc qdisc add dev ens33 parent 1:4 handle 40: netem delay 0ms 

# Add filters for directing traffic from each sender to band
sudo tc filter add dev ens33 protocol ip parent 1: prio 1 u32 match ip src $sender1IP/32 flowid 1:1
sudo tc filter add dev ens33 protocol ip parent 1: prio 1 u32 match ip src $sender2IP/32 flowid 1:2
sudo tc filter add dev ens33 protocol ip parent 1: prio 1 u32 match ip src $sender3IP/32 flowid 1:3

echo "ubuntu" | ssh ${senderArr[0]} "sudo -S sysctl -w net.ipv4.tcp_congestion_control=$ALGORITHM" 
echo "ubuntu" | ssh ${senderArr[1]} "sudo -S sysctl -w net.ipv4.tcp_congestion_control=$ALGORITHM" 
echo "ubuntu" | ssh ${senderArr[2]} "sudo -S sysctl -w net.ipv4.tcp_congestion_control=$ALGORITHM" 

ssh ${senderArr[0]} "iperf3 -c ${receiverArr[0]} -t 300 -i 1 -J > ${senderArr[0]}_${ALGORITHM}_results.json" & 
ssh ${senderArr[1]} "iperf3 -c ${receiverArr[1]} -t 300 -i 1 -J > ${senderArr[1]}_${ALGORITHM}_results.json" & 
ssh ${senderArr[2]} "iperf3 -c ${receiverArr[2]} -t 300 -i 1 -J > ${senderArr[2]}_${ALGORITHM}_results.json" & 

wait
echo "Intra-protocol RTT fairness test complete"